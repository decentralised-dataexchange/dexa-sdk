"""Classes for configuring the default injection context."""

import logging
from ..core.plugin_registry import PluginRegistry as CustomPluginRegistry
from ..config.injection_context import InjectionContext

from aries_cloudagent.core.plugin_registry import PluginRegistry
from aries_cloudagent.config.base_context import ContextBuilder
from aries_cloudagent.config.provider import CachedProvider, ClassProvider, StatsProvider

from aries_cloudagent.cache.base import BaseCache
from aries_cloudagent.cache.basic import BasicCache
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.ledger.base import BaseLedger
from aries_cloudagent.ledger.provider import LedgerProvider
from aries_cloudagent.issuer.base import BaseIssuer
from aries_cloudagent.holder.base import BaseHolder
from aries_cloudagent.verifier.base import BaseVerifier
from aries_cloudagent.tails.base import BaseTailsServer

from aries_cloudagent.protocols.actionmenu.v1_0.base_service import BaseMenuService
from aries_cloudagent.protocols.actionmenu.v1_0.driver_service import DriverMenuService
from aries_cloudagent.protocols.didcomm_prefix import DIDCommPrefix
from aries_cloudagent.protocols.introduction.v0_1.base_service import BaseIntroductionService
from aries_cloudagent.protocols.introduction.v0_1.demo_service import DemoIntroductionService

from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.storage.provider import StorageProvider
from aries_cloudagent.transport.wire_format import BaseWireFormat
from aries_cloudagent.utils.stats import Collector
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.wallet.provider import WalletProvider

from ...ledgers.ethereum.core import EthereumClient


LOGGER = logging.getLogger(__name__)


class DefaultContextBuilder(ContextBuilder):
    """Default context builder."""

    async def build(self) -> InjectionContext:
        """Build the new injection context; set DIDComm prefix to emit."""

        # Disable type checking for provided instances against base class.
        # In DEXA SDK, there are multiple overriden instance that have same signature
        # as base class but doesn't inherit it.
        context = InjectionContext(
            settings=self.settings, enforce_typing=False)
        context.settings.set_default("default_label", "Aries Cloud Agent")

        if context.settings.get("timing.enabled"):
            timing_log = context.settings.get("timing.log_file")
            collector = Collector(log_path=timing_log)
            context.injector.bind_instance(Collector, collector)

        # Shared in-memory cache
        context.injector.bind_instance(BaseCache, BasicCache())

        # Global protocol registry
        context.injector.bind_instance(ProtocolRegistry, ProtocolRegistry())

        await self.bind_providers(context)
        await self.load_plugins(context)

        # Set DIDComm prefix
        DIDCommPrefix.set(context.settings)

        return context

    async def bind_providers(self, context: InjectionContext):
        """Bind various class providers."""

        context.injector.bind_provider(
            BaseStorage,
            CachedProvider(
                StatsProvider(
                    StorageProvider(), ("add_record", "get_record", "search_records")
                )
            ),
        )
        context.injector.bind_provider(
            BaseWallet,
            CachedProvider(
                StatsProvider(
                    WalletProvider(),
                    (
                        "sign_message",
                        "verify_message",
                        # "pack_message",
                        # "unpack_message",
                        "get_local_did",
                    ),
                )
            ),
        )

        context.injector.bind_provider(
            BaseLedger,
            CachedProvider(
                StatsProvider(
                    LedgerProvider(),
                    (
                        "create_and_send_credential_definition",
                        "create_and_send_schema",
                        "get_credential_definition",
                        "get_schema",
                    ),
                )
            ),
        )
        context.injector.bind_provider(
            BaseIssuer,
            StatsProvider(
                ClassProvider(
                    "aries_cloudagent.issuer.indy.IndyIssuer",
                    ClassProvider.Inject(BaseWallet),
                ),
                ("create_credential_offer", "create_credential"),
            ),
        )
        context.injector.bind_provider(
            BaseHolder,
            StatsProvider(
                ClassProvider(
                    "aries_cloudagent.holder.indy.IndyHolder",
                    ClassProvider.Inject(BaseWallet),
                ),
                ("get_credential", "store_credential", "create_credential_request"),
            ),
        )
        context.injector.bind_provider(
            BaseVerifier,
            ClassProvider(
                "aries_cloudagent.verifier.indy.IndyVerifier",
                ClassProvider.Inject(BaseLedger),
            ),
        )
        context.injector.bind_provider(
            BaseTailsServer,
            ClassProvider(
                "aries_cloudagent.tails.indy_tails_server.IndyTailsServer",
            ),
        )

        # Register default pack format
        context.injector.bind_provider(
            BaseWireFormat,
            CachedProvider(
                StatsProvider(
                    ClassProvider(
                        "aries_cloudagent.transport.pack_format.PackWireFormat"
                    ),
                    (
                        # "encode_message", "parse_message"
                    ),
                )
            ),
        )

        # Allow action menu to be provided by driver
        context.injector.bind_instance(
            BaseMenuService, DriverMenuService(context))
        context.injector.bind_instance(
            BaseIntroductionService, DemoIntroductionService(context)
        )

        # Provide ethereum client.
        context.injector.bind_instance(
            EthereumClient, EthereumClient(context)
        )

    async def load_plugins(self, context: InjectionContext):
        """Set up plugin registry and load plugins."""

        # Provide plugin
        plugin_registry = CustomPluginRegistry()
        context.injector.bind_instance(PluginRegistry,
                                       plugin_registry)

        # Register standard protocol plugins
        plugin_registry.register_package("aries_cloudagent.protocols")

        # Currently providing admin routes only
        plugin_registry.register_plugin("aries_cloudagent.holder")
        plugin_registry.register_plugin("aries_cloudagent.ledger")
        plugin_registry.register_plugin(
            "aries_cloudagent.messaging.credential_definitions"
        )
        plugin_registry.register_plugin("aries_cloudagent.messaging.schemas")
        plugin_registry.register_plugin("aries_cloudagent.revocation")
        plugin_registry.register_plugin("aries_cloudagent.wallet")

        # Register external plugins
        for plugin_path in self.settings.get("external_plugins", []):
            plugin_registry.register_plugin(plugin_path)

        # Register message protocols
        await plugin_registry.init_context(context)
