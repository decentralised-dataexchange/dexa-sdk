"""DEXA config."""
from aries_cloudagent.config.base import InjectorError
from aries_cloudagent.config.injection_context import InjectionContext
from dexa_sdk.ledgers.ethereum.core import EthereumClient
from loguru import logger


async def smartcontract_config(context: InjectionContext):
    """Add agent controller organisation to dexa smartcontract whitelist.

    Args:
        context (InjectionContext): Injection context to be used.
    """
    try:
        logger.info("Audit mode is enabled.")
        eth_client: EthereumClient = await context.inject(EthereumClient)

        # Add organisation to whitelist
        await eth_client.add_organisation()
    except InjectorError:
        logger.info("Audit mode is not enabled.")
