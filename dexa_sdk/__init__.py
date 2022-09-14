import pyld

from dexa_sdk.logs.core import configure_logger

# Configure loguru logger
configure_logger()

# To store jsonld context resolved documents
cache = {}


def caching_document_loader(url, options):
    """Simple in-memory cache for JSONLD context resolutions"""
    loader = pyld.jsonld.requests_document_loader()
    if url in cache:
        return cache[url]
    resp = loader(url)
    cache[url] = resp
    return resp


pyld.jsonld.set_document_loader(caching_document_loader)
