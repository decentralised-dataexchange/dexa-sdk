import ast
import json
import math
import typing
from collections import namedtuple
from urllib.parse import parse_qs, urlparse

import aiohttp
import jcs
import semver
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.jsonld.credential import (
    b64_to_bytes,
    b64encode,
    bytes_to_b64,
)
from aries_cloudagent.messaging.models.base_record import BaseRecord


def jcs_rfc8785(data: typing.Union[list, dict]) -> bytes:
    """JSON canonicalisation schema as per IETF RFC 8785"""
    return jcs.canonicalize(data)


def jcs_bytes_to_pyobject(data: bytes) -> typing.Any:
    """Convert JCS bytes to <dict, list e.t.c>"""
    return ast.literal_eval(data.decode())


def replace_jws(doc: dict) -> dict:
    """Replace 'jws' field with 'proofValue' field

    Args:
        doc (dict): input document with proof

    Returns:
        dict: replaced document
    """
    # Add 'proofValue' field
    doc["proofValue"] = doc["jws"]
    # Delete 'jws' field
    del doc["jws"]

    return doc


def replace_proof_value(doc: dict) -> dict:
    """Replace 'proofValue' field with 'jws' field

    Args:
        doc (dict): input document with proof

    Returns:
        dict: replaced document
    """
    # Add 'proofValue' field
    doc["jws"] = doc["proofValue"]
    # Delete 'jws' field
    del doc["proofValue"]

    return doc


def replace_proof_chain(doc: dict) -> dict:
    """Replace 'proofChain' field with 'proof' field

    Args:
        doc (dict): input document with proof

    Returns:
        dict: replaced document
    """
    # Add 'proof' field with first proof in the chain
    doc["proof"] = doc["proofChain"][0]
    # Delete 'proofChain' field
    del doc["proofChain"]

    return doc


def sort_exchange_record_dicts_by_created_at(
    records: typing.List[dict], sort_order: str = "desc"
) -> typing.List[dict]:
    """Sort exchange record dicts based on 'created at' field

    Args:
        records (typing.List[dict]): Exchange record dicts
        sort_order (str, optional): Sort order ('desc' or 'asc'). Defaults to "desc".

    Returns:
        typing.List[dict]: Sorted record dicts
    """
    assert sort_order in ("desc", "asc")

    return sorted(
        records,
        key=lambda k: k["updated_at"],
        reverse=True if sort_order == "desc" else False,
    )


def bump_major_for_semver_string(version: str) -> str:
    """Bump major part of the semver string.

    Args:
        version (str): semver compatible version string

    Returns:
        str: Bumped version
    """
    v = semver.parse_version_info(version)
    return str(v.bump_major())


# Pagination config
PaginationConfig = namedtuple(
    "PaginationConfig", ["total_count", "page", "page_size", "total_pages"]
)

# Pagination result
PaginationResult = namedtuple("PaginationResult", ["results", "pagination"])


def get_slices(page, page_size=10):
    """
    Get the start and end indices for the given page and page size.

    Args:
        page: page number
        page_size: page size

    Returns: start and end indices

    """
    start = (page - 1) * page_size

    end = start + page_size

    return start, end


def paginate(
    items_list: typing.List, page: int = 1, page_size: int = 10
) -> PaginationResult:
    """Paginate an items list

    Args:
        items_list (typing.List): items list
        page (int, optional): page number. Defaults to None.

    Returns:
        PaginationResult: Pagination result
    """

    page = page if page else 1

    # total count
    total_count = len(items_list)

    # total pages
    total_pages = math.ceil(total_count / page_size)

    # Get the items list for the current page
    # Fetch pagination indices
    lower, upper = get_slices(page, page_size)

    # Slice the items for current page
    items_list = items_list[lower:upper]

    pconfig = PaginationConfig(
        total_count=total_count, page=page, page_size=page_size, total_pages=total_pages
    )

    res = PaginationResult(results=items_list, pagination=pconfig._asdict())

    return res


def paginate_records(
    records: typing.List[BaseRecord], page: int = 1, page_size: int = 10
) -> PaginationResult:
    """Paginate records

    Args:
        records (typing.List[BaseRecord]): records
        page (int, optional): page. Defaults to 1.
        page_size (int, optional): page_size. Defaults to 10.

    Returns:
        PaginationResult: Results
    """

    presults = paginate(records, page, page_size)

    serialised_item_list = []
    for item in presults.results:
        serialised_item_list.append(item.serialize())

    # Sort the serialised records.
    serialised_item_list = sort_exchange_record_dicts_by_created_at(
        serialised_item_list
    )

    res = PaginationResult(results=serialised_item_list, pagination=presults.pagination)

    return res


def clean_and_get_field_from_dict(
    input: dict, key: str
) -> typing.Union[None, typing.Any]:
    """Return the value of the field in dict if present.

    Args:
        input (dict): dict
        key (str): dict key

    Returns:
        typing.Union[None, Any]: Value of the field
    """

    # Get field value
    field_value = input.get(key)

    # Check if field value is empty string
    if field_value and isinstance(field_value, str) and len(field_value) == 0:
        field_value = None

    return field_value


def drop_none_dict(input: dict) -> dict:
    """Return dict with None values removed

    Args:
        input (dict): input

    Returns:
        dict: output
    """

    for k, v in list(input.items()):
        if v is None:
            input.pop(k)

    return input


async def generate_firebase_dynamic_link(
    context: InjectionContext, payload: str
) -> str:
    """Generate firebase dynamic link

    Args:
        context (InjectionContext): Injection context to be used.
        payload (str): Payload.

    Returns:
        str: Firebase dynamic link
    """

    domain_uri_prefix = context.settings.get("intermediary.firebase_domain_uri_prefix")
    android_package_name = context.settings.get(
        "intermediary.firebase_android_package_name"
    )
    ios_bundle_id = context.settings.get("intermediary.firebase_ios_bundle_id")
    ios_appstore_id = context.settings.get("intermediary.firebase_ios_appstore_id")
    firebase_web_api_key = context.settings.get("intermediary.firebase_web_api_key")

    payload = {
        "dynamicLinkInfo": {
            "domainUriPrefix": domain_uri_prefix,
            "link": payload,
            "androidInfo": {
                "androidPackageName": android_package_name,
            },
            "iosInfo": {
                "iosBundleId": ios_bundle_id,
                "iosAppStoreId": ios_appstore_id,
            },
        },
        "suffix": {"option": "UNGUESSABLE"},
    }

    firebase_dynamic_link_endpoint = (
        "https://firebasedynamiclinks.googleapis.com/v1/shortLinks?key="
    )
    firebase_dynamic_link_endpoint += firebase_web_api_key

    jresp = {}
    async with aiohttp.ClientSession() as session:
        async with session.post(firebase_dynamic_link_endpoint, json=payload) as resp:
            if resp.status == 200:
                jresp = await resp.json()
            else:
                tresp = await resp.text()
                raise Exception(f"Error in Firebase dynamic link: {tresp}")

    return jresp["shortLink"]


async def fetch_org_details_from_intermediary(context: InjectionContext) -> dict:
    """Fetch org details from intermediary

    Args:
        context (InjectionContext): Injection context to be used.

    Returns:
        dict: Org details.
    """

    endpoint_url = context.settings.get("intermediary.igrantio_endpoint_url")
    org_id = context.settings.get("intermediary.igrantio_org_id")
    api_key = context.settings.get("intermediary.igrantio_org_api_key")

    # Construct iGrant.io organisation detail endpoint URL
    org_detail_url = f"{endpoint_url}/v1/organizations/{org_id}"

    # Construct request headers
    request_headers = {"Authorization": f"ApiKey {api_key}"}

    # Make request to iGrant.io organisation detail endpoint
    jresp = None
    async with aiohttp.ClientSession(headers=request_headers) as session:
        async with session.get(org_detail_url) as resp:
            if resp.status == 200:
                jresp = await resp.json()
                return jresp["Organization"]

    return jresp


async def parse_query_params(url: str, query_param: str) -> str:
    """Parse query params in a URL

    Args:
        url (str): URL
        query_param (str): Query param key.

    Returns:
        str: _description_
    """

    # Parse the URL
    parsed_url = urlparse(url)

    # Parse query string params.
    parsed_qs = parse_qs(parsed_url.query)

    return parsed_qs.get(query_param)[0]


async def create_jwt(data: dict, verkey, wallet) -> str:
    """Create and sign jwt"""

    # payload
    encoded_payload = b64encode(json.dumps(data))

    # header
    header = {"alg": "EdDSA", "type": "JWT"}
    encoded_header = b64encode(json.dumps(header))

    # to be signed payload.
    tbs = (encoded_header + ".").encode("utf-8") + encoded_payload.encode("utf-8")

    # signature.
    signature = await wallet.sign_message(tbs, verkey)

    encoded_signature = bytes_to_b64(signature, urlsafe=True, pad=False)

    return encoded_header + "." + encoded_payload + "." + encoded_signature


async def verify_jwt(token: str, public_key, wallet) -> bool:
    """Verify JWT"""

    encoded_header, encoded_payload, encoded_signature = token.split(".")

    decoded_signature = b64_to_bytes(encoded_signature, urlsafe=True)

    # to be verified
    tbv = (encoded_header + ".").encode("utf-8") + encoded_payload.encode("utf-8")

    verified = await wallet.verify_message(tbv, decoded_signature, public_key)

    return verified
