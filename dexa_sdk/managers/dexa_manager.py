import asyncio
import json
import time
import typing
import uuid

import aiohttp
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.connections.models.connection_target import ConnectionTarget
from aries_cloudagent.core.dispatcher import Dispatcher
from aries_cloudagent.indy.util import generate_pr_nonce
from aries_cloudagent.messaging.agent_message import AgentMessage
from aries_cloudagent.messaging.decorators.transport_decorator import TransportDecorator
from aries_cloudagent.protocols.connections.v1_0.manager import ConnectionManager
from aries_cloudagent.transport.inbound.receipt import MessageReceipt
from aries_cloudagent.transport.pack_format import BaseWireFormat, PackWireFormat
from aries_cloudagent.utils.task_queue import CompletedTask, PendingTask
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.wallet.indy import IndyWallet
from dexa_protocol.v1_0.messages.deactivate_dda import DeactivateDDAMessage
from dexa_protocol.v1_0.messages.marketplace.delete_dda import DeleteDDAMessage
from dexa_protocol.v1_0.messages.marketplace.list_marketplace_dda import (
    ListMarketplaceDDAMessage,
)
from dexa_protocol.v1_0.messages.marketplace.list_marketplace_dda_response import (
    ListMarketplaceDDAResponseMessage,
)
from dexa_protocol.v1_0.messages.marketplace.publish_dda import PublishDDAMessage
from dexa_protocol.v1_0.messages.negotiation.accept_dda import AcceptDDAMessage
from dexa_protocol.v1_0.messages.negotiation.dda_negotiation_receipt import (
    DDANegotiationReceiptMessage,
)
from dexa_protocol.v1_0.messages.negotiation.offer_dda import OfferDDAMessage
from dexa_protocol.v1_0.messages.negotiation.request_dda import RequestDDAMessage
from dexa_protocol.v1_0.messages.pulldata_request_message import PullDataRequestMessage
from dexa_protocol.v1_0.messages.pulldata_response_message import (
    PullDataResponseMessage,
)
from dexa_protocol.v1_0.models.accept_dda_model import AcceptDDAMessageBodyModel
from dexa_protocol.v1_0.models.dda_negotiation_receipt_model import (
    DDANegotiationReceiptBodyModel,
)
from dexa_protocol.v1_0.models.deactivate_dda_model import DeactivateDDABodyModel
from dexa_protocol.v1_0.models.delete_dda_model import DeleteDDAModel
from dexa_protocol.v1_0.models.list_marketplace_dda_response_model import (
    ListMarketplaceDDAResponseBody,
    ListMarketplaceDDAResponseModel,
)
from dexa_protocol.v1_0.models.offer_dda_model import (
    CustomerIdentificationModel,
    OfferDDAMessageBodyModel,
)
from dexa_protocol.v1_0.models.publish_dda_model import PublishDDAModel
from dexa_protocol.v1_0.models.request_dda_model import RequestDDAModel
from dexa_sdk.agreements.da.v1_0.records.customer_identification_record import (
    CustomerIdentificationRecord,
)
from dexa_sdk.agreements.da.v1_0.records.da_template_record import (
    DataAgreementTemplateRecord,
)
from dexa_sdk.agreements.dda.v1_0.models.dda_instance_models import (
    DataDisclosureAgreementInstanceModel,
)
from dexa_sdk.agreements.dda.v1_0.models.dda_models import (
    DDA_DEFAULT_CONTEXT,
    DDA_TYPE,
    DataControllerModel,
    DataDisclosureAgreementModel,
    DataSharingRestrictionsModel,
    PersonalDataModel,
)
from dexa_sdk.agreements.dda.v1_0.records.dda_instance_permission_record import (
    DDAInstancePermissionRecord,
)
from dexa_sdk.agreements.dda.v1_0.records.dda_instance_record import (
    DataDisclosureAgreementInstanceRecord,
)
from dexa_sdk.agreements.dda.v1_0.records.dda_template_record import (
    DataDisclosureAgreementTemplateRecord,
)
from dexa_sdk.agreements.dda.v1_0.records.pull_data_record import PullDataRecord
from dexa_sdk.data_controller.records.connection_controller_details_record import (
    ConnectionControllerDetailsRecord,
)
from dexa_sdk.did_mydata.core import DIDMyDataBuilder
from dexa_sdk.ledgers.ethereum.core import EthereumClient
from dexa_sdk.managers.ada_manager import V2ADAManager
from dexa_sdk.marketplace.records.marketplace_connection_record import (
    MarketplaceConnectionRecord,
)
from dexa_sdk.marketplace.records.publish_dda_record import PublishDDARecord
from dexa_sdk.marketplace.records.published_dda_template_record import (
    PublishedDDATemplateRecord,
)
from dexa_sdk.utils import (
    PaginationResult,
    create_jwt,
    drop_none_dict,
    paginate_records,
)
from dexa_sdk.utils.utils import paginate
from loguru import logger
from mydata_did.v1_0.messages.data_controller_details import (
    DataControllerDetailsMessage,
)
from mydata_did.v1_0.messages.data_controller_details_response import (
    DataControllerDetailsResponseMessage,
)
from mydata_did.v1_0.utils.util import bool_to_str
from web3._utils.encoding import to_json


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
        self, da_template_id: str, *, publish_flag: bool = True
    ) -> DataDisclosureAgreementTemplateRecord:
        """Create and store dda template in wallet

        Args:
            da_template_id (str): DA template ID.
            publish_flag (bool): Publish flag
            schema_id (str): Schema identifier
        """

        # Fetch DA template record.
        da_template_record = (
            await DataAgreementTemplateRecord.latest_published_template_by_id(
                self.context, da_template_id
            )
        )

        assert da_template_record, "Data agreement template not found."

        existing_dda_template_records = (
            await DataDisclosureAgreementTemplateRecord.query(
                self.context, {"da_template_id": da_template_record.template_id}
            )
        )

        assert (
            len(existing_dda_template_records) == 0
        ), "Existing DDA template associated with the DA found."

        # DA model.
        data_agreement_model = da_template_record.data_agreement_model

        assert (
            data_agreement_model.data_policy.third_party_data_sharing
        ), "Third party data sharing not enabled."

        # Temp hack
        template_version = "1.0.0"
        template_id = str(uuid.uuid4())

        # Fetch controller details.
        mgr = V2ADAManager(self.context)
        controller_details_record = await mgr.get_controller_details_record()

        # Create DDA model.

        personal_datas = []
        for pd in data_agreement_model.personal_data:
            personal_datas.append(
                PersonalDataModel(
                    attribute_id=pd.attribute_id,
                    attribute_name=pd.attribute_name,
                    attribute_description=pd.attribute_description,
                )
            )

        dda_model = DataDisclosureAgreementModel(
            context=DDA_DEFAULT_CONTEXT,
            id=template_id,
            type=DDA_TYPE,
            language=data_agreement_model.language,
            version=template_version,
            data_controller=DataControllerModel(
                did=controller_details_record.organisation_did,
                name=controller_details_record.organisation_name,
                legal_id=controller_details_record.organisation_did,
                url=controller_details_record.policy_url,
                industry_sector=controller_details_record.organisation_type,
            ),
            agreement_period=data_agreement_model.data_policy.data_retention_period,
            data_sharing_restrictions=DataSharingRestrictionsModel(
                policy_url=data_agreement_model.data_policy.policy_url,
                jurisdiction=data_agreement_model.data_policy.jurisdiction,
                industry_sector=data_agreement_model.data_policy.industry_sector,
                data_retention_period=data_agreement_model.data_policy.data_retention_period,
                geographic_restriction=data_agreement_model.data_policy.geographic_restriction,
                storage_location=data_agreement_model.data_policy.storage_location,
            ),
            purpose=data_agreement_model.purpose,
            purpose_description=data_agreement_model.purpose_description,
            lawful_basis=data_agreement_model.lawful_basis,
            code_of_conduct=data_agreement_model.data_policy.policy_url,
            personal_data=personal_datas,
        )

        # Create template record
        record = DataDisclosureAgreementTemplateRecord(
            template_id=template_id,
            template_version=template_version,
            state=DataDisclosureAgreementTemplateRecord.STATE_DEFINITION,
            data_disclosure_agreement=dda_model.serialize(),
            industry_sector=dda_model.data_sharing_restrictions.industry_sector.lower(),
            publish_flag=bool_to_str(publish_flag),
            latest_version_flag=bool_to_str(True),
            da_template_id=da_template_id,
            da_template_version=da_template_record.template_version,
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
            "industry_sector": industry_sector.lower()
            if industry_sector
            else industry_sector,
            "publish_flag": publish_flag,
            "delete_flag": delete_flag,
            "latest_version_flag": latest_version_flag,
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataDisclosureAgreementTemplateRecord.query(
            context=self.context, tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.created_at, reverse=True)

        paginate_result = paginate_records(records, page, page_size)

        return paginate_result

    async def update_dda_template_in_wallet(
        self,
        template_id: str,
        *,
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
        existing_template = (
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context, template_id
            )
        )

        assert existing_template, "DDA template not found."

        # Fetch controller details.
        mgr = V2ADAManager(self.context)
        controller_details_record = await mgr.get_controller_details_record()

        # Upgrade the existing template to next version.
        upgraded = await existing_template.upgrade(
            self.context, controller_details_record, bool_to_str(publish_flag)
        )

        # Post update actions
        if publish_flag:
            await self.post_update_dda_template(upgraded)

        return upgraded

    async def delete_dda_template_in_wallet(self, template_id: str):
        """Delete DDA template in wallet.

        Args:
            template_id (str): Template identifier.
        """

        # Fetch the latest template.
        existing_template = (
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context, template_id
            )
        )

        assert existing_template, "DDA template not found."

        # Delete template.
        await existing_template.delete_template(self.context)

        # Post delete actions.
        await self.post_delete_dda_template(template_id)

    async def publish_dda_template_wallet(self, template_id: str):
        """Publish DDA template in wallet.

        Args:
            template_id (str): Template identifier
        """

        # Fetch the latest template.
        existing_template = (
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context, template_id
            )
        )

        await existing_template.publish_template(self.context)

        # Post publish actions.
        await self.post_update_dda_template(existing_template)

    async def send_message_with_return_route_all(
        self, message: AgentMessage, connection_record: ConnectionRecord
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
        message._decorators["transport"] = TransportDecorator(return_route="all")

        # Initialise connection manager
        connection_manager = ConnectionManager(self.context)

        # Fetch connection targets
        connection_targets = await connection_manager.fetch_connection_targets(
            connection_record
        )

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
        headers = {"Content-Type": "application/ssi-agent-wire"}

        # Send request and receive response.
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                connection_target.endpoint, data=packed_message
            ) as response:
                # Assert status code is 200
                assert (
                    response.status == 200
                ), f"HTTP request failed with status code {response.status}"

                message_body = await response.read()

                # Unpack message
                unpacked = await wallet.unpack_message(message_body)
                (message_json, sender_verkey, recipient_verkey) = unpacked

                # Convert message to dict.
                message_dict = json.loads(message_json)

                return (sender_verkey, recipient_verkey, message_dict)

    async def add_marketplace_connection(
        self, connection_id: str
    ) -> MarketplaceConnectionRecord:
        """Set connection as marketplace.

        Args:
            connection_id (str): Connection identifier.

        Returns:
            MarketplaceConnectionRecord: Marketplace connection record.
        """

        # Connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context, connection_id
        )

        record = await MarketplaceConnectionRecord.set_connection_as_marketplace(
            self.context, connection_record.connection_id
        )

        return record

    async def query_marketplace_connections(
        self, connection_id: str, page: int = 1, page_size: int = 10
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
        self, template_record: DataDisclosureAgreementTemplateRecord
    ):
        """Post update DDA template actions.

        Args:
            template_record (DataDisclosureAgreementTemplateRecord): DDA template record.
        """

        # Find all the marketplace connections.
        # Query to find all marketplaces the template is published to.
        tag_filter = {"template_id": template_record.template_id}
        records: typing.List[PublishDDARecord] = await PublishDDARecord.query(
            self.context, tag_filter
        )

        # Notify all the marketplaces about the update.
        for record in records:
            await self.send_publish_dda_message(record, template_record)

    async def send_publish_dda_message(
        self,
        publish_dda_record: PublishDDARecord,
        template_record: DataDisclosureAgreementTemplateRecord,
    ):
        """Send publish DDA message.

        Args:
            publish_dda_record (PublishDDARecord): Publish dda record.
            template_record (DataDisclosureAgreementTemplateRecord): DDA template record.
            connection_id (str): Connection identifier.
        """
        # Create connection invitation
        mgr = V2ADAManager(self.context)
        (
            connection_record_for_marketplace,
            connection_invitation_for_marketplace,
        ) = await mgr.create_invitation(
            auto_accept=True,
            public=False,
            multi_use=True,
            alias=f"DDA_{template_record.template_id}_QR_{publish_dda_record._id}",
        )

        # Publish dda message
        publish_dda_message = PublishDDAMessage(
            body=PublishDDAModel(
                dda=template_record.dda_model,
                connection_url=connection_invitation_for_marketplace.to_url(),
            )
        )

        # Send publish dda message to marketplace connection
        await mgr.send_reply_message(
            publish_dda_message, publish_dda_record.connection_id
        )

    async def publish_dda_template_to_marketplace(
        self, connection_id: str, template_id: str
    ) -> PublishDDARecord:
        """Publish DDA template to marketplace

        Args:
            connection_id (str): Connection ID
            template_id (str): Template ID

        Returns:
            PublishDDARecord: Publish DDA record.
        """

        # Fetch template
        template_record = (
            await DataDisclosureAgreementTemplateRecord.latest_template_by_id(
                self.context, template_id
            )
        )

        assert (
            template_record._publish_flag
        ), "DDA must be published locally before published to marketplace."

        # Connection record
        connection_record: ConnectionRecord = (
            await MarketplaceConnectionRecord.retrieve_connection_record(
                self.context, connection_id
            )
        )

        # Create Publish DDA record.
        # Publish DDA record is mapping of which template is published in which marketplace.
        publish_dda_record = await PublishDDARecord.store_publish_dda_record(
            self.context,
            connection_record.connection_id,
            template_record.template_id,
            template_record.data_disclosure_agreement,
        )

        # Send publish dda message to marketplace.
        await self.send_publish_dda_message(publish_dda_record, template_record)

        return publish_dda_record

    async def fetch_and_save_controller_details_for_connection(
        self, connection_record: ConnectionRecord
    ):
        """Fetch and save controller details for connection

        Args:
            connection_record (ConnectionRecord): Connection record
        """
        controller_details_message = DataControllerDetailsMessage()
        (
            sender_verkey,
            recipient_verkey,
            message_dict,
        ) = await self.send_message_with_return_route_all(
            controller_details_message, connection_record
        )
        # Data controller detail response.
        data_controller_details_response: DataControllerDetailsResponseMessage = (
            DataControllerDetailsResponseMessage.deserialize(message_dict)
        )

        # Save controller details for a connection.
        await ConnectionControllerDetailsRecord.set_controller_details_for_connection(
            self.context, connection_record, data_controller_details_response.body
        )

    async def post_connection_delete_actions(self, connection_id: str):
        """Post connection record delete actions.

        Args:
            connection_id (str): Connection identifier.
        """

        self._logger.info("Performing post delete actions for connection records...")

        # Delete marketplace connection records.
        tag_filter = {"connection_id": connection_id}
        marketplace_records = await MarketplaceConnectionRecord.query(
            self.context, tag_filter
        )
        if marketplace_records:
            marketplace_record = marketplace_records[0]
            await marketplace_record.delete_record(self.context)

        # Delete controller connection records.
        controller_records = await ConnectionControllerDetailsRecord.query(
            self.context, tag_filter
        )
        if controller_records:
            controller_record = controller_records[0]
            await controller_record.delete_record(self.context)

    async def handle_connections_webhook(self, body: dict):
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
        self, message: PublishDDAMessage, message_receipt: MessageReceipt
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
            message.body.connection_url,
        )

    async def query_publish_dda_template_records(
        self, page: int = 1, page_size: int = 10
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
        self, message: DeleteDDAMessage, message_receipt: MessageReceipt
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
            self.context, connection_record.connection_id, template_id
        )

    async def post_delete_dda_template(self, template_id: str):
        """Post delete dda template record actions.

        Inform the data marketplaces the template is deleted.

        Args:
            template_id (str): Template identifier.
        """

        # Construct delete DDA message.
        message = DeleteDDAMessage(body=DeleteDDAModel(template_id=template_id))

        # Query to find all marketplaces the template is published to.
        tag_filter = {"template_id": template_id}
        records: typing.List[PublishDDARecord] = await PublishDDARecord.query(
            self.context, tag_filter
        )

        mgr = V2ADAManager(self.context)

        # Notify all the marketplaces the template is deleted.
        for record in records:
            await mgr.send_reply_message(message, record.connection_id)

            # Delete publish DDA records.
            await record.delete_record(self.context)

    async def list_dda_published_in_marketplace(
        self, page: int = 1, page_size: int = 10
    ) -> PaginationResult:
        """List DDAs published in a marketplace.

        Returns:
            PaginationResult: Pagination result.
        """

        # Fetch all publish dda records.
        tag_filter = {}
        records: typing.List[PublishDDARecord] = await PublishDDARecord.query(
            self.context, tag_filter
        )

        pagination_result = paginate_records(records, page=page, page_size=page_size)

        return pagination_result

    async def send_list_marketplace_dda_message(
        self, connection_id: str
    ) -> PaginationResult:
        """Send list marketplace DDA message.

        Args:
            connection_id (str): Marketplace connection identifier.
        """

        # Retrieve connection record for marketplace connection.
        connection_record = (
            await MarketplaceConnectionRecord.retrieve_connection_record(
                self.context, connection_id
            )
        )

        # Construct the list dda message.
        message = ListMarketplaceDDAMessage()

        (
            sender_verkey,
            recipient_verkey,
            message_dict,
        ) = await self.send_message_with_return_route_all(message, connection_record)

        # Deserialise the message dict into response message.
        response: ListMarketplaceDDAResponseMessage = (
            ListMarketplaceDDAResponseMessage.deserialize(message_dict)
        )

        results = response.body.results

        # Pagination result.
        pagination_result = paginate_records(results, 1, 100000)

        return pagination_result

    async def process_list_marketplace_dda_message(
        self, message: ListMarketplaceDDAMessage, receipt: MessageReceipt
    ):
        """Process list marketplace DDA message.

        Args:
            message (ListMarketplaceDDAMessage): List marketplace DDA message.
            receipt (MessageReceipt): Message receipt.
        """

        # Query published DDAs
        tag_filter = {}
        records: typing.List[
            PublishedDDATemplateRecord
        ] = await PublishedDDATemplateRecord.query(self.context, tag_filter)

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
                    updated_at=record.updated_at,
                )
            )

        # Construct response message.
        response_message = ListMarketplaceDDAResponseMessage(
            body=ListMarketplaceDDAResponseBody(results=results)
        )

        # Initialise ADA manager
        mgr = V2ADAManager(self.context)

        # Send response message.
        await mgr.send_reply_message(response_message)

    async def get_message_class_from_dict(self, message_dict: dict) -> AgentMessage:
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
        self, message: RequestDDAMessage, receipt: MessageReceipt
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
        (
            dda_instance_record,
            dda_instance_model,
        ) = await DataDisclosureAgreementInstanceRecord.build_instance_from_template(
            self.context, template_id, connection_record
        )

        # Fetch customer identification data agreement if available.
        customer_identification_records = await CustomerIdentificationRecord.query(
            self.context, {}
        )

        if customer_identification_records:
            customer_identification_record: CustomerIdentificationRecord = (
                customer_identification_records[0]
            )

            # Fetch DA template.
            da_template_record: DataAgreementTemplateRecord = (
                await customer_identification_record.data_agreement_template_record(
                    self.context
                )
            )

            # Build dda offer message
            offer_dda_message = OfferDDAMessage(
                body=OfferDDAMessageBodyModel(
                    dda=dda_instance_model,
                    customer_identification=CustomerIdentificationModel(
                        schema_id=da_template_record.schema_id,
                        cred_def_id=da_template_record.cred_def_id,
                    ),
                )
            )
        else:
            # Build dda offer message
            offer_dda_message = OfferDDAMessage(
                body=OfferDDAMessageBodyModel(dda=dda_instance_model)
            )

        mgr = V2ADAManager(self.context)

        await mgr.send_reply_message(offer_dda_message, connection_record.connection_id)

    async def request_dda_offer_from_ds(self, connection_id: str, template_id: str):
        """DUS requests DDA offer from DS.

        Args:
            connection_id (str): Connection ID.
            template_id (str): Template ID.
        """

        # Retreive connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context, connection_id
        )

        # Send DDA request message to DS.
        message = RequestDDAMessage(body=RequestDDAModel(template_id=template_id))

        # Initialise ADA manager.
        mgr = V2ADAManager(self.context)

        await mgr.send_reply_message(message, connection_record.connection_id)

    async def fetch_customer_identification_data_agreement(
        self,
    ) -> typing.Union[None, CustomerIdentificationRecord]:
        """Fetch customer identification data agreement.

        Returns:
            typing.Union[None, CustomerIdentificationRecord]: Customer identification record.
        """
        records = await CustomerIdentificationRecord.query(self.context, {})

        return {} if not records else records[0]

    async def configure_customer_identification_data_agreement(
        self, da_template_id: str
    ) -> CustomerIdentificationRecord:
        """Configure customer identification data agreement.

        Args:
            da_template_id (str): DA template ID.

        Returns:
            CustomerIdentificationRecord: _description_
        """

        return await CustomerIdentificationRecord.create_or_update_record(
            self.context, da_template_id
        )

    async def process_offer_dda_message(
        self, message: OfferDDAMessage, message_receipt: MessageReceipt
    ):
        """Process offer dda message.

        Args:
            message (OfferDDAMessage): Offer DDA message.
            message_receipt (MessageReceipt): Message receipt.
        """

        (
            record,
            instance_model,
        ) = await DataDisclosureAgreementInstanceRecord.build_instance_from_dda_offer(
            self.context, message, self.context.connection_record
        )

        # Construct accept DDA message.
        accept_dda_message = AcceptDDAMessage(
            body=AcceptDDAMessageBodyModel(dda=instance_model)
        )

        # Initialise the ADA manager
        mgr = V2ADAManager(self.context)

        # Send the message.
        await mgr.send_reply_message(accept_dda_message)

    async def process_accept_dda_message(
        self, message: AcceptDDAMessage, message_receipt: MessageReceipt
    ):
        """Process accept dda message.

        Args:
            message (AcceptDDAMessage): Accept DDA message.
            message_receipt (MessageReceipt): Message receipt.
        """

        instance_record = (
            await DataDisclosureAgreementInstanceRecord.update_instance_from_dda_accept(
                self.context, message
            )
        )

        # Anchor DDA instance to blochain.
        await self.anchor_dda_instance_to_blockchain_async_task(
            instance_record.instance_id
        )

    async def add_task(
        self,
        context: InjectionContext,
        coro: typing.Coroutine,
        task_complete: typing.Callable = None,
        ident: str = None,
    ) -> PendingTask:
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
        pack_format: PackWireFormat = await context.inject(
            BaseWireFormat, required=False
        )
        return pack_format.task_queue.put(
            coro, lambda x: loop.create_task(task_complete(x)), ident
        )

    async def anchor_dda_instance_to_blockchain_async_task(self, instance_id: str):
        """Async task to anchor DDA instance to blockchain.

        Args:
            instance_id (str): Instance id
        """
        pending_task = await self.add_task(
            self.context,
            self.anchor_dda_instance_to_blockchain(instance_id),
            self.anchor_dda_instance_to_blockchain_async_task_callback,
        )
        self._logger.info(pending_task)

    async def anchor_dda_instance_to_blockchain(self, instance_id: str) -> None:
        """Anchor DDA instance to blockchain.

        Args:
            instance_id (str): Instance id
        """

        eth_client: EthereumClient = await self.context.inject(EthereumClient)

        tag_filter = {"instance_id": instance_id}

        # Fetch DDA instance record.
        dda_instance_records = await DataDisclosureAgreementInstanceRecord.query(
            self.context,
            tag_filter,
        )

        assert dda_instance_records, "Data agreement instance not found."

        dda_instance_record: DataDisclosureAgreementInstanceRecord = (
            dda_instance_records[0]
        )
        dda_model: DataDisclosureAgreementInstanceModel = (
            DataDisclosureAgreementInstanceModel.deserialize(
                dda_instance_record.data_disclosure_agreement
            )
        )

        did_mydata_builder = DIDMyDataBuilder(artefact=dda_model)

        (tx_hash, tx_receipt) = await eth_client.emit_dda_did(
            did_mydata_builder.generate_did("DataDisclosureAgreement")
        )

        return (
            dda_instance_record.instance_id,
            did_mydata_builder.mydata_did,
            tx_hash,
            tx_receipt,
        )

    async def anchor_dda_instance_to_blockchain_async_task_callback(
        self, *args, **kwargs
    ):
        """Anchor DDA instance to blockchain async task callback function"""

        # Obtain the completed task.
        completed_task: CompletedTask = args[0]

        # Obtain the results from the task.
        (instance_id, mydata_did, tx_hash, tx_receipt) = completed_task.task.result()

        tag_filter = {"instance_id": instance_id}

        # Fetch data agreement instance record.
        dda_instance_records = await DataDisclosureAgreementInstanceRecord.query(
            self.context,
            tag_filter,
        )

        assert dda_instance_records, "Data agreement instance not found."

        dda_instance_record: DataDisclosureAgreementInstanceRecord = (
            dda_instance_records[0]
        )

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
                mydata_did=mydata_did,
            )
        )

        # Fetch connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context, dda_instance_record.connection_id
        )

        # Initialise ADA manager
        mgr = V2ADAManager(self.context)

        # Send message
        await mgr.send_reply_message(message, connection_record.connection_id)

    async def query_dda_instances(
        self,
        instance_id: str,
        template_id: str,
        template_version: str,
        connection_id: str,
        page: int = 1,
        page_size: int = 10,
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
            "connection_id": connection_id,
        }

        tag_filter = drop_none_dict(tag_filter)

        records: typing.List[
            DataDisclosureAgreementInstanceRecord
        ] = await DataDisclosureAgreementInstanceRecord.query(
            context=self.context, tag_filter=tag_filter
        )
        records = sorted(records, key=lambda k: k.updated_at, reverse=True)

        records_list = []
        for record in records:
            record_dict = record.serialize()
            record_dict.update({"permissions": []})

            # Fetch permission records for DDA instance.
            permission_records: typing.List[
                DDAInstancePermissionRecord
            ] = await DDAInstancePermissionRecord.query(
                self.context, {"instance_id": record.instance_id}
            )
            permission_records_sorted: typing.List[
                DDAInstancePermissionRecord
            ] = sorted(permission_records, key=lambda k: k.updated_at, reverse=True)

            for permission_record in permission_records_sorted:
                # Update permissions list for DDA instance.
                record_dict["permissions"].append(permission_record.serialize())

            records_list.append(record_dict)

        paginate_result = paginate(records_list, page, page_size)

        return paginate_result

    async def process_dda_negotiation_receipt_message(
        self, message: DDANegotiationReceiptMessage, message_receipt: MessageReceipt
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
        tag_filter = {"instance_id": instance_id}
        instance_record: DataDisclosureAgreementInstanceRecord = (
            await DataDisclosureAgreementInstanceRecord.retrieve_by_tag_filter(
                self.context, tag_filter
            )
        )

        # Update instance record.
        instance_record.blockchain_receipt = blockchain_receipt
        instance_record.blink = blink
        instance_record.mydata_did = mydata_did

        await instance_record.save(self.context)

    async def send_deactivate_dda_message(self, instance_id: str):
        """Send deactivate DDA message.

        Args:
            instance_id (str): Instance ID.
        """

        # Deactivate DDA locally.
        (
            instance_record,
            permission_record,
        ) = await DDAInstancePermissionRecord.deactivate(self.context, instance_id)

        # Send deactivate message.
        message = DeactivateDDAMessage(
            body=DeactivateDDABodyModel(instance_id=instance_id)
        )

        mgr = V2ADAManager(self.context)
        await mgr.send_reply_message(message, instance_record.connection_id)

    async def process_deactivate_dda_message(
        self, message: DeactivateDDAMessage, message_receipt: MessageReceipt
    ):
        """Process deactivate DDA message.

        Args:
            message (DeactivateDDAMessage): Deactivate DDA message.
            message_receipt (MessageReceipt): Message receipt.
        """

        instance_id = message.body.instance_id

        # Deactivate DDA locally.
        await DDAInstancePermissionRecord.deactivate(self.context, instance_id)

    async def process_pulldata_request_message(
        self, message: PullDataRequestMessage, message_receipt: MessageReceipt
    ):
        """Process pull data request message.

        Args:
            message (PullDataRequestMessage): Pull data request message.
            message_receipt (MessageReceipt): Message receipt.
        """

        # Connection record.
        connection_record: ConnectionRecord = self.context.connection_record

        # Fetch wallet from context
        wallet: IndyWallet = await self.context.inject(BaseWallet)

        # Controller did (Public did)
        controller_did = await wallet.get_public_did()

        dda_instance_id = message.dda_instance_id
        nonce = message.nonce

        # Fetch DDA instance.
        tag_filter = {"instance_id": dda_instance_id}
        dda_instance_record: DataDisclosureAgreementInstanceRecord = (
            await DataDisclosureAgreementInstanceRecord.retrieve_by_tag_filter(
                self.context, tag_filter
            )
        )

        assert dda_instance_record, "DDA instance not found."

        # Get permission
        dda_instance_permission_record = (
            await DDAInstancePermissionRecord.get_permission(
                self.context, dda_instance_record.instance_id
            )
        )

        # Check DDA instance is active.
        if (
            dda_instance_permission_record
            and dda_instance_permission_record.state
            != DDAInstancePermissionRecord.STATE_DEACTIVATE
        ) or (not dda_instance_permission_record):

            # Create a jwt token with dda_instance_id, nonce in the claims.
            data = {
                "iat": int(time.time()),
                "exp": int(time.time()) + 7200,
                "dda_instance_id": dda_instance_id,
                "nonce": nonce,
            }
            jwt = await create_jwt(data, controller_did.verkey, wallet)
            # valid = await verify_jwt(jwt, controller_did.verkey, wallet)

            # Initialise connection manager
            connection_manager = ConnectionManager(self.context)

            # Fetch connection targets
            connection_targets = await connection_manager.fetch_connection_targets(
                connection_record
            )

            assert len(connection_targets) > 0, "Zero connection targets found."

            connection_target: ConnectionTarget = connection_targets[0]

            # Pack the token.
            packed = await wallet.pack_message(
                jwt, connection_target.recipient_keys, connection_target.sender_key
            )

            # Create pull data record.
            pull_data_record = PullDataRecord(
                dda_instance_id=dda_instance_id,
                dda_template_id=dda_instance_record.template_id,
                nonce=nonce,
                state=PullDataRecord.STATE_REQUEST,
                token_packed=json.loads(packed.decode()),
                token=jwt,
            )

            # Save the record.
            await pull_data_record.save(self.context)

            # Add token to blockchain
            await self.add_token_to_blockchain_async_task(
                connection_record, packed.decode(), nonce
            )

    async def add_token_to_blockchain_async_task(
        self,
        connection_record: ConnectionRecord,
        jwt: str,
        nonce: str,
    ):
        """Add token to blockchain async task"""

        pending_task = await self.add_task(
            self.context,
            self.add_token_to_blockchain(connection_record, jwt, nonce),
            self.add_token_to_blockchain_async_task_callback,
        )
        self._logger.info(pending_task)

    async def add_token_to_blockchain(
        self, connection_record: ConnectionRecord, jwt: str, nonce: str
    ) -> None:
        """Add token to blockchain"""

        eth_client: EthereumClient = await self.context.inject(EthereumClient)

        (tx_hash, tx_receipt) = await eth_client.add_access_token(nonce, jwt)

        return (
            connection_record,
            nonce,
            tx_hash,
            tx_receipt,
        )

    async def add_token_to_blockchain_async_task_callback(self, *args, **kwargs):
        """Add token to blockchain async task callback function"""

        # Obtain the completed task.
        completed_task: CompletedTask = args[0]

        # Obtain the results from the task.
        (connection_record, nonce, tx_hash, tx_receipt) = completed_task.task.result()

        transaction_receipt = json.loads(to_json(tx_receipt))
        transaction_hash = transaction_receipt.get("transactionHash")

        # Fetch pull data record by nonce
        pulldata_records = await PullDataRecord.query(self.context, {"nonce": nonce})
        if pulldata_records:
            # Update pull data record.
            pulldata_record: PullDataRecord = pulldata_records[0]
            pulldata_record.blink = f"blink:ethereum:rinkeby:{transaction_hash}"
            pulldata_record.blockchain_receipt = transaction_receipt
            pulldata_record.state = PullDataRecord.STATE_RESPONSE
            await pulldata_record.save(self.context)

        # Initialise manager
        mgr = V2ADAManager(self.context)

        # TODO: Send pull data notification to the Individual

        # Send pull data response message to DUS connection.
        eth_client: EthereumClient = await self.context.inject(EthereumClient)

        pulldata_response_message = PullDataResponseMessage(
            ds_eth_address=eth_client.org_account.address, nonce=nonce
        )
        await mgr.send_reply_message(
            pulldata_response_message, connection_record.connection_id
        )

    async def send_pulldata_request_message(
        self, instance_id: str, da_template_id: str = None, connection_id: str = None
    ):
        """Send pull data request message.

        Args:
            instance_id (str): Instance ID.
        """

        # Fetch DDA instance.
        tag_filter = {"instance_id": instance_id}
        dda_instance_record: DataDisclosureAgreementInstanceRecord = (
            await DataDisclosureAgreementInstanceRecord.retrieve_by_tag_filter(
                self.context, tag_filter
            )
        )

        assert dda_instance_record, "DDA instance not found."

        # Get permission
        dda_instance_permission_record = (
            await DDAInstancePermissionRecord.get_permission(
                self.context, dda_instance_record.instance_id
            )
        )

        # Check DDA instance is active.
        if (
            dda_instance_permission_record
            and dda_instance_permission_record.state
            != DDAInstancePermissionRecord.STATE_DEACTIVATE
        ) or (not dda_instance_permission_record):

            if not da_template_id:

                # Construct pull data request message.
                nonce = await generate_pr_nonce()
                message = PullDataRequestMessage(
                    dda_instance_id=instance_id, nonce=nonce
                )

                # Create pull data record.
                pull_data_record = PullDataRecord(
                    dda_instance_id=instance_id,
                    dda_template_id=dda_instance_record.template_id,
                    nonce=nonce,
                    state=PullDataRecord.STATE_REQUEST,
                )

                # Save the record.
                await pull_data_record.save(self.context)

                # Send the pull data request message.
                mgr = V2ADAManager(self.context)
                await mgr.send_reply_message(message, dda_instance_record.connection_id)

            else:

                # Fetch DA template record.
                # Validate if published.
                # Validate method of use is data-using-service.
                # Send presentation request to individual.
                # Once the presentation request is verified.
                # Pull data request is send to DS.

                # Construct pull data request message.
                nonce = await generate_pr_nonce()
                message = PullDataRequestMessage(
                    dda_instance_id=instance_id, nonce=nonce
                )

                # Create pull data record.
                pull_data_record = PullDataRecord(
                    dda_instance_id=instance_id,
                    dda_template_id=dda_instance_record.template_id,
                    nonce=nonce,
                    state=PullDataRecord.STATE_REQUEST,
                )

                # Save the record.
                await pull_data_record.save(self.context)

    async def query_pull_data_records(
        self,
        *,
        dda_instance_id: str = None,
        dda_template_id: str = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginationResult:
        """Query pull data records.

        Args:
            dda_instance_id (str, optional): DDA instance ID. Defaults to None.
            dda_template_id (str, optional): DDA template ID. Defaults to None.
            da_template_id (str, optional): DA template ID. Defaults to None.
            page (int, optional): Page. Defaults to 1.
            page_size (int, optional): Page size. Defaults to 10.

        Returns:
            PaginationResult: Pagination result.
        """

        # Tag filter
        tag_filter = {
            "dda_instance_id": dda_instance_id,
            "dda_template_id": dda_template_id,
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await PullDataRecord.query(
            context=self.context, tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.updated_at, reverse=True)

        paginate_result = paginate_records(records, page, page_size)

        return paginate_result

    async def process_pull_data_response_message(
        self, message: PullDataResponseMessage, message_receipt: MessageReceipt
    ):
        """Process pull data response message.

        Args:
            message (PullDataResponseMessage): Pull data response message.
            message_receipt (MessageReceipt): Message receipt.
        """

        ds_eth_address = message.ds_eth_address
        nonce = message.nonce

        # Fetch data from ethereum.
        eth_client: EthereumClient = await self.context.inject(EthereumClient)

        packed_token = await eth_client.release_access_token(ds_eth_address, nonce)

        # Fetch wallet from context
        wallet: IndyWallet = await self.context.inject(BaseWallet)

        # Pack the token.
        (token, from_verkey, to_verkey) = await wallet.unpack_message(
            packed_token.encode()
        )

        # Update pull data record.

        # Fetch pull data record by nonce
        pulldata_records = await PullDataRecord.query(self.context, {"nonce": nonce})
        if pulldata_records:
            # Update pull data record.
            pulldata_record: PullDataRecord = pulldata_records[0]
            pulldata_record.state = PullDataRecord.STATE_RESPONSE
            pulldata_record.token_packed = json.loads(packed_token)
            pulldata_record.token = token
            await pulldata_record.save(self.context)
