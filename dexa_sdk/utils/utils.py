import jcs
import ast
import typing
import semver
import math
from collections import namedtuple
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


def sort_exchange_record_dicts_by_created_at(records: typing.List[dict],
                                             sort_order: str = "desc") -> typing.List[dict]:
    """Sort exchange record dicts based on 'created at' field

    Args:
        records (typing.List[dict]): Exchange record dicts
        sort_order (str, optional): Sort order ('desc' or 'asc'). Defaults to "desc".

    Returns:
        typing.List[dict]: Sorted record dicts
    """
    assert sort_order in ("desc", "asc")

    return sorted(records,
                  key=lambda k: k['created_at'],
                  reverse=True if sort_order == "desc" else False)


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
    'PaginationConfig',
    [
        "total_count",
        "page",
        "page_size",
        "total_pages"
    ]
)

# Pagination result
PaginationResult = namedtuple(
    'PaginationResult',
    [
        "results",
        "pagination"
    ]
)


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


def paginate(items_list: typing.List, page: int = 1, page_size: int = 10) -> PaginationResult:
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
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

    res = PaginationResult(results=items_list, pagination=pconfig._asdict())

    return res


def paginate_records(
    records: typing.List[BaseRecord],
    page: int = 1,
    page_size: int = 10
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

    res = PaginationResult(results=serialised_item_list, pagination=presults.pagination)

    return res


def clean_and_get_field_from_dict(
        input: dict,
        key: str
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
