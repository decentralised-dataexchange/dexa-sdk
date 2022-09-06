import requests
from aries_cloudagent.config.argparse import (
    ArgumentGroup,
    CAT_START,
    ArgumentParser,
    Namespace
)


class group:
    """Decorator for registering argument groups."""

    _registered = []

    def __init__(self, *categories):
        """Initialize the decorator."""
        self.categories = tuple(categories)

    def __call__(self, group_cls: ArgumentGroup):
        """Register a class in the given categories."""
        setattr(group_cls, "CATEGORIES", self.categories)
        self._registered.append((self.categories, group_cls))
        return group_cls

    @classmethod
    def get_registered(cls, category: str = None):
        """Fetch the set of registered classes in a category."""
        return (
            grp
            for (cats, grp) in cls._registered
            if category is None or category in cats
        )


@group(CAT_START)
class DexaGroup(ArgumentGroup):
    """Dexa settings."""

    GROUP_NAME = "Dexa"

    def add_arguments(self, parser: ArgumentParser):
        """Add dexa-specific command line arguments to the parser."""

        parser.add_argument(
            "--eth-node-rpc",
            type=str,
            metavar="<eth-node-rpc>",
            env_var="ETH_NODE_RPC",
            help="Ethereum node RPC endpoint",
        )

        parser.add_argument(
            "--intermediary-eth-private-key",
            type=str,
            metavar="<intermediary-eth-private-key>",
            env_var="INTERMEDIARY_ETH_PRIVATE_KEY",
            help="Private key associated with the intermediary account address",
        )

        parser.add_argument(
            "--org-eth-private-key",
            type=str,
            metavar="<org-eth-private-key>",
            env_var="ORG_ETH_PRIVATE_KEY",
            help="Private key associated with the organisation account address",
        )

        parser.add_argument(
            "--contract-address",
            type=str,
            metavar="<contract-address>",
            env_var="CONTRACT_ADDRESS",
            help="Contract address",
        )

        parser.add_argument(
            "--contract-abi-url",
            type=str,
            metavar="<contract-abi-url>",
            env_var="CONTRACT_ABI_URL",
            help="Contract ABI URL",
        )

    def get_settings(self, args: Namespace):
        """Extract dexa settings."""
        settings = {}

        default_contract_abi_url = ("https://raw.githubusercontent.com"
                                    "/decentralised-dataexchange/dexa-smartcontracts"
                                    "/main/abi/abi.json")

        settings["dexa.eth_node_rpc"] = args.eth_node_rpc
        settings["dexa.org_eth_private_key"] = args.org_eth_private_key
        settings["dexa.intermediary_eth_private_key"] = args.intermediary_eth_private_key
        settings["dexa.contract_address"] = args.contract_address
        settings["dexa.contract_abi_url"] = \
            args.contract_abi_url if args.contract_abi_url else default_contract_abi_url

        # Fetch ABI from URL and store it in settings
        req = requests.get(settings["dexa.contract_abi_url"])
        abi = req.json()
        settings["dexa.contract_abi"] = abi

        return settings
