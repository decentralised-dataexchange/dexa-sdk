from .logs.core import configure_logger
from .jsonld.core import configure_jsonld_simple_cache

# Configure loguru logger
configure_logger()

# Configure in-memory cache for jsonld instances
configure_jsonld_simple_cache()
