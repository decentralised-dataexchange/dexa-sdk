import uuid
import json
import aiohttp
import typing
import asyncio
from loguru import logger
from web3._utils.encoding import to_json
from aries_cloudagent.core.dispatcher import Dispatcher
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.wallet.indy import IndyWallet
from aries_cloudagent.utils.task_queue import CompletedTask, PendingTask
from aries_cloudagent.connections.models.connection_target import ConnectionTarget
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.messaging.agent_message import AgentMessage
from aries_cloudagent.messaging.decorators.transport_decorator import TransportDecorator
from aries_cloudagent.transport.pack_format import BaseWireFormat, PackWireFormat
from aries_cloudagent.protocols.connections.v1_0.manager import (
    ConnectionManager
)
from aries_cloudagent.transport.inbound.receipt import MessageReceipt
from mydata_did.v1_0.utils.util import bool_to_str
from mydata_did.v1_0.messages.data_controller_details import DataControllerDetailsMessage
from mydata_did.v1_0.messages.data_controller_details_response import (
    DataControllerDetailsResponseMessage
)
from dexa_protocol.v1_0.messages.negotiation.request_dda import RequestDDAMessage
from dexa_protocol.v1_0.messages.negotiation.offer_dda import OfferDDAMessage
from dexa_protocol.v1_0.messages.negotiation.accept_dda import AcceptDDAMessage
from dexa_protocol.v1_0.models.offer_dda_model import (
    OfferDDAMessageBodyModel,
    CustomerIdentificationModel
)
from dexa_protocol.v1_0.models.accept_dda_model import (
    AcceptDDAMessageBodyModel
)
from dexa_protocol.v1_0.models.request_dda_model import RequestDDAModel
from dexa_protocol.v1_0.messages.marketplace.publish_dda import PublishDDAMessage
from dexa_protocol.v1_0.models.publish_dda_model import PublishDDAModel
from dexa_protocol.v1_0.messages.marketplace.delete_dda import DeleteDDAMessage
from dexa_protocol.v1_0.models.delete_dda_model import DeleteDDAModel
from dexa_protocol.v1_0.messages.marketplace.list_marketplace_dda import ListMarketplaceDDAMessage
from dexa_protocol.v1_0.messages.marketplace.list_marketplace_dda_response import (
    ListMarketplaceDDAResponseMessage
)
from dexa_protocol.v1_0.models.list_marketplace_dda_response_model import (
    ListMarketplaceDDAResponseBody,
    ListMarketplaceDDAResponseModel
)
from dexa_protocol.v1_0.messages.negotiation.dda_negotiation_receipt import (
    DDANegotiationReceiptMessage
)
from dexa_protocol.v1_0.models.dda_negotiation_receipt_model import (
    DDANegotiationReceiptBodyModel
)
from .ada_manager import V2ADAManager
from ..utils import (
    PaginationResult,
    paginate_records,
    drop_none_dict
)
from ..agreements.dda.v1_0.models.dda_instance_models import (
    DataDisclosureAgreementInstanceModel
)
from ..agreements.da.v1_0.records.da_template_record import (
    DataAgreementTemplateRecord
)
from ..agreements.dda.v1_0.records.dda_template_record import (
    DataDisclosureAgreementTemplateRecord
)
from ..agreements.dda.v1_0.records.dda_instance_record import (
    DataDisclosureAgreementInstanceRecord
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
from ..agreements.da.v1_0.records.customer_identification_record import (
    CustomerIdentificationRecord
)
from ..ledgers.ethereum.core import EthereumClient
from ..did_mydata.core import DIDMyDataBuilder


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
            publish_flag: bool = True
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
        if publish_flag:
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

        # Post publish actions.
        await self.post_update_dda_template(existing_template)

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
            connection_record,
            data_controller_details_response.body
        )

    async def post_connection_delete_actions(
        self,
        connection_id: str
    ):
        """Post connection record delete actions.

        Args:
            connection_id (str): Connection identifier.
        """

        self._logger.info("Performing post delete actions for connection records...")

        # Delete marketplace connection records.
        tag_filter = {"connection_id": connection_id}
        marketplace_records = await MarketplaceConnectionRecord.query(
            self.context,
            tag_filter
        )
        if marketplace_records:
            marketplace_record = marketplace_records[0]
            await marketplace_record.delete_record(self.context)

        # Delete controller connection records.
        controller_records = await ConnectionControllerDetailsRecord.query(
            self.context,
            tag_filter
        )
        if controller_records:
            controller_record = controller_records[0]
            await controller_record.delete_record(self.context)

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
        if connection_record.state == "delete":
            # Perform cleanup.
            await self.post_connection_delete_actions(connection_record.connection_id)

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

            # Delete publish DDA records.
            await record.delete_record(self.context)

    async def list_dda_published_in_marketplace(
        self,
        page: int = 1,
        page_size: int = 10
    ) -> PaginationResult:
        """List DDAs published in a marketplace.

        Returns:
            PaginationResult: Pagination result.
        """

        # Fetch all publish dda records.
        tag_filter = {}
        records: typing.List[PublishDDARecord] = await PublishDDARecord.query(
            self.context,
            tag_filter
        )

        pagination_result = paginate_records(records, page=page, page_size=page_size)

        return pagination_result

    async def send_list_marketplace_dda_message(
        self,
        connection_id: str
    ) -> PaginationResult:
        """Send list marketplace DDA message.

        Args:
            connection_id (str): Marketplace connection identifier.
        """

        # Retrieve connection record for marketplace connection.
        connection_record = \
            await MarketplaceConnectionRecord.retrieve_connection_record(
                self.context,
                connection_id
            )

        # Construct the list dda message.
        message = ListMarketplaceDDAMessage()

        (sender_verkey, recipient_verkey, message_dict) = \
            await self.send_message_with_return_route_all(
            message,
            connection_record
        )

        # Deserialise the message dict into response message.
        response: ListMarketplaceDDAResponseMessage = \
            ListMarketplaceDDAResponseMessage.deserialize(
                message_dict
            )

        results = response.body.results

        # Pagination result.
        pagination_result = paginate_records(
            results,
            1,
            100000
        )

        return pagination_result

    async def process_list_marketplace_dda_message(
        self,
        message: ListMarketplaceDDAMessage,
        receipt: MessageReceipt
    ):
        """Process list marketplace DDA message.

        Args:
            message (ListMarketplaceDDAMessage): List marketplace DDA message.
            receipt (MessageReceipt): Message receipt.
        """

        # Query published DDAs
        tag_filter = {}
        records: typing.List[PublishedDDATemplateRecord] = \
            await PublishedDDATemplateRecord.query(
            self.context,
            tag_filter
        )

        # Iterate through the records and create DDA results.
        results = []
        for record in records:
            results.append(
                ListMarketplaceDDAResponseModel(
                    dda=record.dda,
                    template_id=record.template_id,
                    industry_sector=record.industry_sector,
                    connection_url=record.connection_url,
                    created_at=record.created_at,
                    updated_at=record.updated_at
                )
            )

        # Construct response message.
        response_message = ListMarketplaceDDAResponseMessage(
            body=ListMarketplaceDDAResponseBody(
                results=results
            )
        )

        # Initialise ADA manager
        mgr = V2ADAManager(self.context)

        # Send response message.
        await mgr.send_reply_message(
            response_message
        )

    async def get_message_class_from_dict(
            self,
            message_dict: dict
    ) -> AgentMessage:
        """Get message class from message dict.

        Args:
            message_dict (dict): Message dict.

        Returns:
            AgentMessage: Agent message.
        """

        # Initialise dispatcher
        dispatcher = Dispatcher(self.context)

        # Get message class.
        msg_class = await dispatcher.make_message(message_dict)

        return msg_class

    async def process_request_dda_message(
        self,
        message: RequestDDAMessage,
        receipt: MessageReceipt
    ):
        """Process request DDA message.

        Args:
            message (RequestDDAMessage): Request DDA message.
            receipt (MessageReceipt): Message receipt.
        """

        # Connection record.
        connection_record: ConnectionRecord = self.context.connection_record

        # Fetch the template record.
        template_id = message.body.template_id

        # Build instance record.
        (dda_instance_record, dda_instance_model) = \
            await DataDisclosureAgreementInstanceRecord.build_instance_from_template(
                self.context,
                template_id,
                connection_record)

        # Fetch customer identification data agreement if available.
        customer_identification_records = await CustomerIdentificationRecord.query(self.context, {})

        if customer_identification_records:
            customer_identification_record: CustomerIdentificationRecord = \
                customer_identification_records[0]

            # Fetch DA template.
            da_template_record: DataAgreementTemplateRecord = \
                await customer_identification_record.data_agreement_template_record(
                    self.context
                )

            # Build dda offer message
            offer_dda_message = OfferDDAMessage(
                body=OfferDDAMessageBodyModel(
                    dda=dda_instance_model,
                    customer_identification=CustomerIdentificationModel(
                        schema_id=da_template_record.schema_id,
                        cred_def_id=da_template_record.cred_def_id
                    )
                )
            )
        else:
            # Build dda offer message
            offer_dda_message = OfferDDAMessage(
                body=OfferDDAMessageBodyModel(
                    dda=dda_instance_model
                )
            )

        mgr = V2ADAManager(self.context)

        await mgr.send_reply_message(
            offer_dda_message,
            connection_record.connection_id
        )

    async def request_dda_offer_from_ds(
        self,
        connection_id: str,
        template_id: str
    ):
        """DUS requests DDA offer from DS.

        Args:
            connection_id (str): Connection ID.
            template_id (str): Template ID.
        """

        # Retreive connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context,
            connection_id
        )

        # Send DDA request message to DS.
        message = RequestDDAMessage(
            body=RequestDDAModel(
                template_id=template_id
            )
        )

        # Initialise ADA manager.
        mgr = V2ADAManager(self.context)

        await mgr.send_reply_message(
            message,
            connection_record.connection_id
        )

    async def fetch_customer_identification_data_agreement(
        self
    ) -> typing.Union[None, CustomerIdentificationRecord]:
        """Fetch customer identification data agreement.

        Returns:
            typing.Union[None, CustomerIdentificationRecord]: Customer identification record.
        """
        records = await CustomerIdentificationRecord.query(self.context, {})

        return {} if not records else records[0]

    async def configure_customer_identification_data_agreement(
        self,
        da_template_id: str
    ) -> CustomerIdentificationRecord:
        """Configure customer identification data agreement.

        Args:
            da_template_id (str): DA template ID.

        Returns:
            CustomerIdentificationRecord: _description_
        """

        return await CustomerIdentificationRecord.create_or_update_record(
            self.context,
            da_template_id
        )

    async def process_offer_dda_message(
        self,
        message: OfferDDAMessage,
        message_receipt: MessageReceipt
    ):
        """Process offer dda message.

        Args:
            message (OfferDDAMessage): Offer DDA message.
            message_receipt (MessageReceipt): Message receipt.
        """

        (record, instance_model) = \
            await DataDisclosureAgreementInstanceRecord.build_instance_from_dda_offer(
            self.context,
            message,
            self.context.connection_record
        )

        # Construct accept DDA message.
        accept_dda_message = AcceptDDAMessage(
            body=AcceptDDAMessageBodyModel(
                dda=instance_model
            )
        )

        # Initialise the ADA manager
        mgr = V2ADAManager(self.context)

        # Send the message.
        await mgr.send_reply_message(accept_dda_message)

    async def process_accept_dda_message(
        self,
        message: AcceptDDAMessage,
        message_receipt: MessageReceipt
    ):
        """Process accept dda message.

        Args:
            message (AcceptDDAMessage): Accept DDA message.
            message_receipt (MessageReceipt): Message receipt.
        """

        instance_record = \
            await DataDisclosureAgreementInstanceRecord.update_instance_from_dda_accept(
                self.context,
                message
            )

        # Anchor DDA instance to blochain.
        await self.anchor_dda_instance_to_blockchain_async_task(instance_record.instance_id)

    async def add_task(self,
                       context: InjectionContext,
                       coro: typing.Coroutine,
                       task_complete: typing.Callable = None,
                       ident: str = None) -> PendingTask:
        """
        Add a new task to the queue, delaying execution if busy.

        Args:
            context: Injection context to be used.
            coro: The coroutine to run
            task_complete: A callback to run on completion
            ident: A string identifier for the task

        Returns: a future resolving to the asyncio task instance once queued
        """
        loop = asyncio.get_event_loop()
        pack_format: PackWireFormat = await context.inject(BaseWireFormat, required=False)
        return pack_format.task_queue.put(coro, lambda x: loop.create_task(task_complete(x)), ident)

    async def anchor_dda_instance_to_blockchain_async_task(
        self,
        instance_id: str
    ):
        """Async task to anchor DDA instance to blockchain.

        Args:
            instance_id (str): Instance id
        """
        pending_task = await self.add_task(
            self.context,
            self.anchor_dda_instance_to_blockchain(instance_id),
            self.anchor_dda_instance_to_blockchain_async_task_callback
        )
        self._logger.info(pending_task)

    async def anchor_dda_instance_to_blockchain(
        self,
        instance_id: str
    ) -> None:
        """Anchor DDA instance to blockchain.

        Args:
            instance_id (str): Instance id
        """

        eth_client: EthereumClient = await self.context.inject(EthereumClient)

        tag_filter = {
            "instance_id": instance_id
        }

        # Fetch DDA instance record.
        dda_instance_records = await DataDisclosureAgreementInstanceRecord.query(
            self.context,
            tag_filter,
        )

        assert dda_instance_records, "Data agreement instance not found."

        dda_instance_record: DataDisclosureAgreementInstanceRecord = dda_instance_records[0]
        dda_model: DataDisclosureAgreementInstanceModel = \
            DataDisclosureAgreementInstanceModel.deserialize(
                dda_instance_record.data_disclosure_agreement)

        did_mydata_builder = DIDMyDataBuilder(
            artefact=dda_model
        )

        (tx_hash, tx_receipt) = await eth_client.emit_dda_did(
            did_mydata_builder.generate_did(
                "DataDisclosureAgreement"
            )
        )

        return (dda_instance_record.instance_id, did_mydata_builder.mydata_did, tx_hash, tx_receipt)

    async def anchor_dda_instance_to_blockchain_async_task_callback(
        self, *args, **kwargs
    ):
        """Anchor DDA instance to blockchain async task callback function
        """

        # Obtain the completed task.
        completed_task: CompletedTask = args[0]

        # Obtain the results from the task.
        (instance_id, mydata_did, tx_hash, tx_receipt) = completed_task.task.result()

        tag_filter = {
            "instance_id": instance_id
        }

        # Fetch data agreement instance record.
        dda_instance_records = await DataDisclosureAgreementInstanceRecord.query(
            self.context,
            tag_filter,
        )

        assert dda_instance_records, "Data agreement instance not found."

        dda_instance_record: DataDisclosureAgreementInstanceRecord = dda_instance_records[0]

        transaction_receipt = json.loads(to_json(tx_receipt))
        transaction_hash = transaction_receipt.get("transactionHash")

        # Update the data agreement with blockchain metadata.
        dda_instance_record.blink = f"blink:ethereum:rinkeby:{transaction_hash}"
        dda_instance_record.mydata_did = mydata_did
        dda_instance_record.blockchain_receipt = transaction_receipt

        await dda_instance_record.save(self.context)

        # Send negotiation receipt to DUS.
        # Construct negotiation receipt message.
        message = DDANegotiationReceiptMessage(
            body=DDANegotiationReceiptBodyModel(
                instance_id=dda_instance_record.instance_id,
                blockchain_receipt=transaction_receipt,
                blink=f"blink:ethereum:rinkeby:{transaction_hash}",
                mydata_did=mydata_did
            )
        )

        # Fetch connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context,
            dda_instance_record.connection_id
        )

        # Initialise ADA manager
        mgr = V2ADAManager(self.context)

        # Send message
        await mgr.send_reply_message(
            message,
            connection_record.connection_id
        )

    async def query_dda_instances(
        self,
        instance_id: str,
        template_id: str,
        template_version: str,
        connection_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> PaginationResult:
        """Query DDA instances

        Args:
            instance_id (str): Instance identifier
            template_id (str): Template identifier
            template_version (str): Template version
            connection_id (str): Connection id
            page (int, optional): Page. Defaults to 1.
            page_size (int, optional): Page size. Defaults to 10.

        Returns:
            PaginationResult: Pagination result
        """
        # Query by version is only possible if the template id is provided
        if template_version:
            assert template_id, "Template identifier is required to query by version"

        # Tag filter
        tag_filter = {
            "instance_id": instance_id,
            "template_id": template_id,
            "template_version": template_version,
            "connection_id": connection_id
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataDisclosureAgreementInstanceRecord.query(
            context=self.context,
            tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.created_at, reverse=True)

        paginate_result = paginate_records(records, page, page_size)

        return paginate_result

    async def process_dda_negotiation_receipt_message(
        self,
        message: DDANegotiationReceiptMessage,
        message_receipt: MessageReceipt
    ):
        """Process DDA negotiation receipt message.

        Args:
            message (DDANegotiationReceiptMessage): DDA negotiation receipt message.
            message_receipt (MessageReceipt): Message receipt.
        """

        instance_id = message.body.instance_id
        blockchain_receipt = message.body.blockchain_receipt
        blink = message.body.blink
        mydata_did = message.body.mydata_did

        # Fetch the DDA instance record.
        tag_filter = {
            "instance_id": instance_id
        }
        instance_record: DataDisclosureAgreementInstanceRecord = \
            await DataDisclosureAgreementInstanceRecord.retrieve_by_tag_filter(
                self.context,
                tag_filter
            )

        # Update instance record.
        instance_record.blockchain_receipt = blockchain_receipt
        instance_record.blink = blink
        instance_record.mydata_did = mydata_did

        await instance_record.save(self.context)
