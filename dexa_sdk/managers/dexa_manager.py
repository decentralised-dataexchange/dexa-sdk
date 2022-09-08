import uuid
import json
import aiohttp
import typing
from loguru import logger
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.wallet.indy import IndyWallet
from aries_cloudagent.connections.models.connection_target import ConnectionTarget
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.messaging.agent_message import AgentMessage
from aries_cloudagent.messaging.decorators.transport_decorator import TransportDecorator
from aries_cloudagent.transport.pack_format import BaseWireFormat, PackWireFormat
from aries_cloudagent.protocols.connections.v1_0.manager import (
    ConnectionManager,
)
from aries_cloudagent.transport.inbound.receipt import MessageReceipt
from mydata_did.v1_0.utils.util import bool_to_str
from mydata_did.v1_0.messages.data_controller_details import DataControllerDetailsMessage
from mydata_did.v1_0.messages.data_controller_details_response import (
    DataControllerDetailsResponseMessage
)
from dexa_protocol.v1_0.messages.publish_dda import PublishDDAMessage
from dexa_protocol.v1_0.models.publish_dda_model import PublishDDAModel
from dexa_protocol.v1_0.messages.delete_dda import DeleteDDAMessage
from dexa_protocol.v1_0.models.delete_dda_model import DeleteDDAModel
from .ada_manager import V2ADAManager
from ..utils import (
    PaginationResult,
    paginate_records,
    drop_none_dict
)
from ..agreements.dda.v1_0.records.dda_template_record import (
    DataDisclosureAgreementTemplateRecord
)
from ..agreements.dda.v1_0.models.dda_models import (
    DDA_DEFAULT_CONTEXT,
    DDA_TYPE,
    DataDisclosureAgreementModel,
)
from ..marketplace.records.marketplace_connection_record import (
    MarketplaceConnectionRecord
)
from ..marketplace.records.publish_dda_record import (
    PublishDDARecord
)
from ..marketplace.records.published_dda_template_record import (
    PublishedDDATemplateRecord
)
from ..data_controller.records.connection_controller_details_record import (
    ConnectionControllerDetailsRecord
)


class DexaManager:
    """Manages Dexa related functions"""

    def __init__(self, context: InjectionContext) -> None:
        """Initialise Dexa manager

        Args:
            context (InjectionContext): Injection context to be used.
        """

        # Injection context
        self._context = context

        # Logger
        self._logger = logger

    @property
    def context(self) -> InjectionContext:
        """Accessor for injection context

        Returns:
            InjectionContext: Injection context
        """
        return self._context

    @property
    def logger(self):
        """Accessor for logger."""
        return self._logger

    async def create_and_store_dda_template_in_wallet(
            self,
            dda: dict,
            *,
            publish_flag: bool = True,
    ) -> DataDisclosureAgreementTemplateRecord:
        """Create and store dda template in wallet

        Args:
            dda (dict): DDA template.
            publish_flag (bool): Publish flag
            schema_id (str): Schema identifier
        """

        # Temp hack
        template_version = "1.0.0"
        template_id = str(uuid.uuid4())
        dda.update({"@context": DDA_DEFAULT_CONTEXT})
        dda.update({"@id": template_id})
        dda.update({"@type": DDA_TYPE})
        dda.update({"version": template_version})

        # Fetch wallet from context
        wallet: IndyWallet = await self.context.inject(BaseWallet)
        controller_did = await wallet.get_public_did()

        dda["dataController"].update({"did": f"did:sov:{controller_did.did}"})

        # Validate the data agreement.
        dda: DataDisclosureAgreementModel = \
            DataDisclosureAgreementModel.deserialize(
                dda)

        # Hack: Iterate through personal data records and add a unique identifier
        # Todo: Correlating personal data across agreements needs to be done.
        pds = dda.personal_data
        for pd in pds:
            pd.attribute_id = str(uuid.uuid4())

        # Update the personal data with attribute identifiers to the agreement
        dda.personal_data = pds

        # Create template record
        record = DataDisclosureAgreementTemplateRecord(
            template_id=template_id,
            template_version=template_version,
            state=DataDisclosureAgreementTemplateRecord.STATE_DEFINITION,
            data_disclosure_agreement=dda.serialize(),
            industry_sector=dda.data_sharing_restrictions.industry_sector.lower(),
            publish_flag=bool_to_str(publish_flag),
            latest_version_flag=bool_to_str(True)
        )

        await record.save(self.context)

        return record

    async def query_dda_templates_in_wallet(
        self,
        template_id: str = None,
        template_version: str = None,
        industry_sector: str = None,
        publish_flag: str = "false",
        delete_flag: str = "false",
        latest_version_flag: str = "false",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginationResult:
        """Query DA templates in wallet.

        Args:
            template_id (str, optional): Template id. Defaults to None.
            template_version (str, optional): Template version. Defaults to None.
            industry_sector (str, optional): Industry sector. Defaults to None.
            publish_flag (str, optional): Publish flag. Defaults to "false".
            delete_flag (str, optional): Delete flag. Defaults to "false".
            latest_version_flag (str, optional): Latest version flag. Defaults to "false".
            page (int): Page number. Defaults to 1.
            page_size (int): Page size. Defaults to 10.

        Returns:
            PaginationResult: Pagination result
        """

        # Query by version is only possible if the template id is provided
        if template_version:
            assert template_id, "Template identifier is required to query by version"

        # Tag filter
        tag_filter = {
            "template_id": template_id,
            "template_version": template_version,
            "industry_sector": industry_sector.lower() if industry_sector else industry_sector,
            "publish_flag": publish_flag,
            "delete_flag": delete_flag,
            "latest_version_flag": latest_version_flag
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataDisclosureAgreementTemplateRecord.query(
            context=self.context,
            tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.created_at, reverse=True)

        paginate_result = paginate_records(records, page, page_size)

        return paginate_result

    async def update_dda_template_in_wallet(
        self,
        template_id: str,
        *,
        dda: dict,
        publish_flag: bool = True,
    ) -> DataDisclosureAgreementTemplateRecord:
        """Update DDA template in wallet.

        Args:
            template_id (str): Template identifier
            publish_flag (bool, optional): Publish flag. Defaults to True.

        Returns:
            DataDisclosureAgreementTemplateRecord: Upgraded template record.
        """

        # Fetch the latest template.
        existing_template = \
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context,
                template_id
            )

        # Upgrade the existing template to next version.
        upgraded = await existing_template.upgrade(
            self.context,
            dda,
            bool_to_str(publish_flag)
        )

        # Post update actions
        await self.post_update_dda_template(
            upgraded
        )

        return upgraded

    async def delete_dda_template_in_wallet(
        self,
        template_id: str
    ):
        """Delete DDA template in wallet.

        Args:
            template_id (str): Template identifier.
        """

        # Fetch the latest template.
        existing_template = \
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context,
                template_id
            )

        assert existing_template, "DDA template not found."

        # Delete template.
        await existing_template.delete_template(self.context)

        # Post delete actions.
        await self.post_delete_dda_template(
            template_id
        )

    async def publish_dda_template_wallet(
        self,
        template_id: str
    ):
        """Publish DDA template in wallet.

        Args:
            template_id (str): Template identifier
        """

        # Fetch the latest template.
        existing_template = \
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context,
                template_id
            )

        await existing_template.publish_template(self.context)

    async def send_message_with_return_route_all(
        self,
        message: AgentMessage,
        connection_record: ConnectionRecord
    ) -> typing.Tuple[str, str, dict]:
        """Send message with return route all in transport decorator.

        Args:
            message (AgentMessage): Agent message.
            connection_record (ConnectionRecord): Connection record.

        Returns:
            typing.Tuple[str, str, dict]: sender_verkey, recipient_verkey, message_dict
        """

        # Fetch wallet from context
        wallet: IndyWallet = await self.context.inject(BaseWallet)

        # Get pack format from context
        pack_format: PackWireFormat = await self.context.inject(BaseWireFormat)

        # Add transport decorator
        message._decorators["transport"] = TransportDecorator(
            return_route="all"
        )

        # Initialise connection manager
        connection_manager = ConnectionManager(self.context)

        # Fetch connection targets
        connection_targets = await connection_manager.fetch_connection_targets(connection_record)

        assert len(connection_targets) > 0, "Zero connection targets found."

        connection_target: ConnectionTarget = connection_targets[0]

        # Pack message
        packed_message = await pack_format.pack(
            context=self.context,
            message_json=message.serialize(as_string=True),
            recipient_keys=connection_target.recipient_keys,
            routing_keys=None,
            sender_key=connection_target.sender_key,
        )

        # Headers
        headers = {
            "Content-Type": "application/ssi-agent-wire"
        }

        # Send request and receive response.
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(connection_target.endpoint, data=packed_message) as response:
                # Assert status code is 200
                assert response.status == 200, \
                    f"HTTP request failed with status code {response.status}"

                message_body = await response.read()

                # Unpack message
                unpacked = await wallet.unpack_message(message_body)
                (message_json, sender_verkey, recipient_verkey) = unpacked

                # Convert message to dict.
                message_dict = json.loads(message_json)

                return (sender_verkey, recipient_verkey, message_dict)

    async def add_marketplace_connection(
        self,
        connection_id: str
    ) -> MarketplaceConnectionRecord:
        """Set connection as marketplace.

        Args:
            connection_id (str): Connection identifier.

        Returns:
            MarketplaceConnectionRecord: Marketplace connection record.
        """

        # Connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context,
            connection_id
        )

        record = await MarketplaceConnectionRecord.set_connection_as_marketplace(
            self.context,
            connection_record.connection_id
        )

        return record

    async def query_marketplace_connections(
        self,
        connection_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> PaginationResult:
        """Query marketplace connections

        Args:
            connection_id (str): Connection identifier
            page (int, optional): Page. Defaults to 1.
            page_size (int, optional): Page size. Defaults to 10.

        Returns:
            PaginationResult: Pagination result
        """

        tag_filter = {"connection_id": connection_id}
        tag_filter = drop_none_dict(tag_filter)

        records = await MarketplaceConnectionRecord.query(self.context, tag_filter)

        pagination_result = paginate_records(records, page, page_size)

        return pagination_result

    async def post_update_dda_template(
        self,
        template_record: DataDisclosureAgreementTemplateRecord
    ):
        """Post update DDA template actions.

        Args:
            template_record (DataDisclosureAgreementTemplateRecord): DDA template record.
        """

        # Find all the marketplace connections.
        # Query to find all marketplaces the template is published to.
        tag_filter = {
            "template_id": template_record.template_id
        }
        records: typing.List[PublishDDARecord] = await PublishDDARecord.query(
            self.context,
            tag_filter
        )

        # Notify all the marketplaces about the update.
        for record in records:
            await self.send_publish_dda_message(
                record,
                template_record
            )

    async def send_publish_dda_message(
        self,
        publish_dda_record: PublishDDARecord,
        template_record: DataDisclosureAgreementTemplateRecord
    ):
        """Send publish DDA message.

        Args:
            publish_dda_record (PublishDDARecord): Publish dda record.
            template_record (DataDisclosureAgreementTemplateRecord): DDA template record.
            connection_id (str): Connection identifier.
        """
        # Create connection invitation
        mgr = V2ADAManager(self.context)
        (connection_record_for_marketplace, connection_invitation_for_marketplace) = \
            await mgr.create_invitation(
            auto_accept=True,
            public=False,
            multi_use=True,
            alias=f"DDA_{template_record.template_id}_QR_{publish_dda_record._id}"
        )

        # Publish dda message
        publish_dda_message = PublishDDAMessage(
            body=PublishDDAModel(
                dda=template_record.dda_model,
                connection_url=connection_invitation_for_marketplace.to_url()
            )
        )

        # Send publish dda message to marketplace connection
        await mgr.send_reply_message(
            publish_dda_message,
            publish_dda_record.connection_id
        )

    async def publish_dda_template_to_marketplace(
        self,
        connection_id: str,
        template_id: str
    ) -> PublishDDARecord:
        """Publish DDA template to marketplace

        Args:
            connection_id (str): Connection ID
            template_id (str): Template ID

        Returns:
            PublishDDARecord: Publish DDA record.
        """

        # Fetch template
        template_record = await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
            self.context,
            template_id
        )

        assert template_record._publish_flag, \
            "DDA must be published locally before published to marketplace."

        # Connection record
        connection_record: ConnectionRecord = \
            await MarketplaceConnectionRecord.retrieve_connection_record(
                self.context,
                connection_id
            )

        # Create Publish DDA record.
        # Publish DDA record is mapping of which template is published in which marketplace.
        publish_dda_record = await PublishDDARecord.store_publish_dda_record(
            self.context,
            connection_record.connection_id,
            template_record.template_id,
            template_record.data_disclosure_agreement
        )

        # Send publish dda message to marketplace.
        await self.send_publish_dda_message(
            publish_dda_record,
            template_record
        )

        return publish_dda_record

    async def fetch_and_save_controller_details_for_connection(
        self,
        connection_record: ConnectionRecord
    ):
        """Fetch and save controller details for connection

        Args:
            connection_record (ConnectionRecord): Connection record
        """
        controller_details_message = DataControllerDetailsMessage()
        (sender_verkey, recipient_verkey, message_dict) = \
            await self.send_message_with_return_route_all(
            controller_details_message,
            connection_record
        )
        # Data controller detail response.
        data_controller_details_response: DataControllerDetailsResponseMessage = \
            DataControllerDetailsResponseMessage.deserialize(
                message_dict
            )

        # Save controller details for a connection.
        await ConnectionControllerDetailsRecord.set_controller_details_for_connection(
            self.context,
            connection_record.connection_id,
            data_controller_details_response.body.serialize()
        )

    async def handle_connections_webhook(
        self,
        body: dict
    ):
        """Handle connections webhook.

        Args:
            body (dict): Connection record.
        """

        # Fetch connection record.
        connection_record: ConnectionRecord = ConnectionRecord.deserialize(body)

        if connection_record.state == ConnectionRecord.STATE_ACTIVE:
            # Save controller details for connection.
            await self.fetch_and_save_controller_details_for_connection(
                connection_record
            )

    async def process_publish_dda_request_message(
        self,
        message: PublishDDAMessage,
        message_receipt: MessageReceipt
    ):
        """Process publish dda request message.

        Args:
            message (PublishDDAMessage): Publish dda request message
            message_receipt (MessageReceipt): Message receipt
        """

        # Connection record.
        connection_record: ConnectionRecord = self.context.connection_record

        # Save a publish DDA record if not existing.
        await PublishedDDATemplateRecord.store_publish_dda_record(
            self.context,
            connection_record.connection_id,
            message.body.dda,
            message.body.connection_url
        )

    async def query_publish_dda_template_records(
        self,
        page: int = 1,
        page_size: int = 10
    ) -> PaginationResult:
        """Query publish DDA template record.

        Returns:
            PaginationResult: Pagination result.
        """

        # Fetch all the published DDA records.
        records = await PublishedDDATemplateRecord.query(self.context, {})

        # Paginate the records.
        pagination_result = paginate_records(records, page=page, page_size=page_size)

        # Return the result.
        return pagination_result

    async def process_delete_dda_message(
        self,
        message: DeleteDDAMessage,
        message_receipt: MessageReceipt
    ):
        """Process delete DDA message.

        Args:
            message (DeleteDDAMessage): Delete DDA message
            message_receipt (MessageReceipt): Message receipt
        """

        # Connection record.
        connection_record: ConnectionRecord = self.context.connection_record

        # Template id.
        template_id = message.body.template_id

        # Delete published DDA template record.
        await PublishedDDATemplateRecord.delete_publish_dda_record(
            self.context,
            connection_record.connection_id,
            template_id
        )

    async def post_delete_dda_template(
        self,
        template_id: str
    ):
        """Post delete dda template record actions.

        Inform the data marketplaces the template is deleted.

        Args:
            template_id (str): Template identifier.
        """

        # Construct delete DDA message.
        message = DeleteDDAMessage(
            body=DeleteDDAModel(
                template_id=template_id
            )
        )

        # Query to find all marketplaces the template is published to.
        tag_filter = {
            "template_id": template_id
        }
        records: typing.List[PublishDDARecord] = await PublishDDARecord.query(
            self.context,
            tag_filter
        )

        mgr = V2ADAManager(self.context)

        # Notify all the marketplaces the template is deleted.
        for record in records:
            await mgr.send_reply_message(
                message,
                record.connection_id
            )
