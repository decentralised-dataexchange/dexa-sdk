"""DEXA config."""
import logging

from aries_cloudagent.config.injection_context import InjectionContext
from dexa_sdk.ledgers.ethereum.core import EthereumClient

LOGGER = logging.getLogger(__name__)


async def smartcontract_config(context: InjectionContext):
    """Add agent controller organisation to dexa smartcontract whitelist.

    Args:
        context (InjectionContext): Injection context to be used.
    """
    eth_client: EthereumClient = await context.inject(EthereumClient)

    # Add organisation to whitelist
    await eth_client.add_organisation()
