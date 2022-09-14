import requests
from aries_cloudagent.config.argparse import (
    CAT_START,
    ArgumentGroup,
    ArgumentParser,
    Namespace,
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

        default_contract_abi_url = (
            "https://raw.githubusercontent.com"
            "/decentralised-dataexchange/dexa-smartcontracts"
            "/main/abi/abi.json"
        )

        settings["dexa.eth_node_rpc"] = args.eth_node_rpc
        settings["dexa.org_eth_private_key"] = args.org_eth_private_key
        settings[
            "dexa.intermediary_eth_private_key"
        ] = args.intermediary_eth_private_key
        settings["dexa.contract_address"] = args.contract_address
        settings["dexa.contract_abi_url"] = (
            args.contract_abi_url if args.contract_abi_url else default_contract_abi_url
        )

        # Fetch ABI from URL and store it in settings
        req = requests.get(settings["dexa.contract_abi_url"])
        abi = req.json()
        settings["dexa.contract_abi"] = abi

        return settings


@group(CAT_START)
class IntemediaryGroup(ArgumentGroup):
    """Intermediary settings."""

    GROUP_NAME = "Intermediary"

    def add_arguments(self, parser: ArgumentParser):
        """Add intermediary-specific command line arguments to the parser."""

        parser.add_argument(
            "--firebase-web-api-key",
            type=str,
            metavar="<firebase-web-api-key>",
            env_var="FIREBASE_WEB_API_KEY",
            help="Firebase web API key",
        )

        parser.add_argument(
            "--firebase-domain-uri-prefix",
            type=str,
            metavar="<firebase-domain-uri-prefix>",
            env_var="FIREBASE_DOMAIN_URI_PREFIX",
            help="Firebase domain URI prefix",
        )

        parser.add_argument(
            "--firebase-android-package-name",
            type=str,
            metavar="<firebase-android-package-name>",
            env_var="FIREBASE_ANDROID_PACKAGE_NAME",
            help="Firebase android package name",
        )

        parser.add_argument(
            "--firebase-ios-bundle-id",
            type=str,
            metavar="<firebase-ios-bundle-id>",
            env_var="FIREBASE_IOS_BUNDLE_ID",
            help="Firebase iOS bundle ID",
        )

        parser.add_argument(
            "--firebase-ios-appstore-id",
            type=str,
            metavar="<firebase-ios-appstore-id>",
            env_var="FIREBASE_IOS_APPSTORE_ID",
            help="Firebase iOS appstore ID",
        )

        parser.add_argument(
            "--igrantio-org-id",
            type=str,
            metavar="<igrantio-org-id>",
            env_var="IGRANTIO_ORG_ID",
            help="iGrant.io org ID",
        )

        parser.add_argument(
            "--igrantio-org-api-key",
            type=str,
            metavar="<igrantio-org-api-key>",
            env_var="IGRANTIO_ORG_API_KEY",
            help="iGrant.io org API key",
        )

        parser.add_argument(
            "--igrantio-org-api-key-secret",
            type=str,
            metavar="<igrantio-org-api-key-secret>",
            env_var="IGRANTIO_ORG_API_KEY_SECRET",
            help="iGrant.io org API key secret",
        )

        parser.add_argument(
            "--igrantio-endpoint-url",
            type=str,
            metavar="<igrantio-endpoint-url>",
            env_var="IGRANTIO_ENDPOINT_URL",
            help="iGrant.io org endpoint URL",
        )

        parser.add_argument(
            "--igrantio-authentication",
            action="store_true",
            env_var="IGRANTIO_AUTHENTICATION",
            help="iGrant.io authentication",
        )

    def get_settings(self, args: Namespace):
        """Extract dexa settings."""
        settings = {}

        settings["intermediary.firebase_web_api_key"] = args.firebase_web_api_key
        settings[
            "intermediary.firebase_domain_uri_prefix"
        ] = args.firebase_domain_uri_prefix
        settings[
            "intermediary.firebase_android_package_name"
        ] = args.firebase_android_package_name
        settings["intermediary.firebase_ios_bundle_id"] = args.firebase_ios_bundle_id
        settings[
            "intermediary.firebase_ios_appstore_id"
        ] = args.firebase_ios_appstore_id
        settings["intermediary.igrantio_org_id"] = args.igrantio_org_id
        settings["intermediary.igrantio_org_api_key"] = args.igrantio_org_api_key
        settings[
            "intermediary.igrantio_org_api_key_secret"
        ] = args.igrantio_org_api_key_secret
        settings["intermediary.igrantio_endpoint_url"] = args.igrantio_endpoint_url

        if args.igrantio_authentication:
            settings["intermediary.igrantio_authentication"] = True
        else:
            settings["intermediary.igrantio_authentication"] = False

        return settings
