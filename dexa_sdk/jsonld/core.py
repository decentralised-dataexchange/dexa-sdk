
import hashlib
import requests
from merklelib import utils
from pyld import jsonld
from ..storage.utils.json import jcs_rfc8785

# To store jsonld context resolved documents
cache = {}


def caching_document_loader(url, options):
    """Simple in-memory cache for JSONLD context resolutions"""
    loader = jsonld.requests_document_loader()
    if url in cache:
        return cache[url]
    resp = loader(url)
    cache[url] = resp
    return resp


def configure_jsonld_simple_cache():
    """Configure cache for global jsonld instance"""
    jsonld.set_document_loader(caching_document_loader)


DEXA_JSONLD_CONTEXT_URL = ("https://raw.githubusercontent.com"
                           "/decentralised-dataexchange"
                           "/data-exchange-agreements/main/interface-specs"
                           "/jsonld/contexts/dexa-context.jsonld")


def fetch_jsonld_context_from_remote(
        context_type: str = None,
        remote_context_url: str = DEXA_JSONLD_CONTEXT_URL) -> dict:
    """
    Fetch JSONLD context from remote

    Args:
        context_type (str): Specific JSONLD context type
        remote_context_url (str): Remote JSONLD context URL

    Returns:
        jresp (dict): JSONLD context
    """
    # Perform HTTP GET against remote context URL
    req = requests.get(remote_context_url)
    assert req.status_code == 200, \
        "Failed to fetch JSONLD context from remote."
    # JSON response
    jresp = req.json()
    # Return context
    return jresp if not context_type else \
        jresp.get("@context", {}).get(context_type)


def jsonld_context_fingerprint(
        context_type: str = None,
        remote_context_url: str = DEXA_JSONLD_CONTEXT_URL) -> str:
    """Returns the fingerprint (SHA2-256) of JSON-LD context"""
    # Fetch context from remote
    jsonld_context = fetch_jsonld_context_from_remote(
        context_type,
        remote_context_url
    )
    # Canonicalise the context document
    jcs = jcs_rfc8785(jsonld_context)
    # Convert bytes to string
    value = utils.to_string(jcs)
    # Return the SHA2-256 hexdigest
    return hashlib.sha256(value).hexdigest()
