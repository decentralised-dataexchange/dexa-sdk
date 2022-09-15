import asyncio
import base64
import json
import typing
import uuid

import aiohttp
from aries_cloudagent.cache.basic import BaseCache
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.connections.models.connection_target import ConnectionTarget
from aries_cloudagent.core.dispatcher import Dispatcher, DispatcherResponder
from aries_cloudagent.core.error import BaseError
from aries_cloudagent.indy.util import generate_pr_nonce
from aries_cloudagent.messaging.agent_message import AgentMessage
from aries_cloudagent.messaging.decorators.attach_decorator import AttachDecorator
from aries_cloudagent.messaging.decorators.default import DecoratorSet
from aries_cloudagent.messaging.decorators.transport_decorator import TransportDecorator
from aries_cloudagent.messaging.jsonld.create_verify_data import create_verify_data
from aries_cloudagent.messaging.models.base_record import match_post_filter
from aries_cloudagent.messaging.responder import BaseResponder
from aries_cloudagent.protocols.connections.v1_0.manager import (
    ConnectionManager,
    ConnectionManagerError,
)
from aries_cloudagent.protocols.connections.v1_0.messages.connection_invitation import (
    ConnectionInvitation,
)
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange,
)
from aries_cloudagent.protocols.present_proof.v1_0.message_types import (
    ATTACH_DECO_IDS,
    PRESENTATION_REQUEST,
)
from aries_cloudagent.protocols.present_proof.v1_0.messages.presentation_request import (
    PresentationRequest,
)
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange,
)
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.transport.inbound.receipt import MessageReceipt
from aries_cloudagent.transport.pack_format import BaseWireFormat, PackWireFormat
from aries_cloudagent.utils.task_queue import CompletedTask, PendingTask
from aries_cloudagent.wallet.base import BaseWallet, DIDInfo
from aries_cloudagent.wallet.indy import IndyWallet
from dexa_sdk.agreements.da.v1_0.models.da_instance_models import (
    DataAgreementInstanceModel,
)
from dexa_sdk.agreements.da.v1_0.models.da_models import (
    DA_DEFAULT_CONTEXT,
    DA_TYPE,
    DataAgreementModel,
    DataAgreementPersonalDataModel,
)
from dexa_sdk.agreements.da.v1_0.records.da_instance_permission_record import (
    DAInstancePermissionRecord,
)
from dexa_sdk.agreements.da.v1_0.records.da_instance_record import (
    DataAgreementInstanceRecord,
)
from dexa_sdk.agreements.da.v1_0.records.da_qrcode_record import (
    DataAgreementQRCodeRecord,
)
from dexa_sdk.agreements.da.v1_0.records.da_template_record import (
    DataAgreementTemplateRecord,
)
from dexa_sdk.agreements.da.v1_0.records.personal_data_record import PersonalDataRecord
from dexa_sdk.agreements.dda.v1_0.records.dda_instance_record import (
    DataDisclosureAgreementInstanceRecord,
)
from dexa_sdk.agreements.dda.v1_0.records.dda_template_record import (
    DataDisclosureAgreementTemplateRecord,
)
from dexa_sdk.connections.records.existing_connections_record import (
    ExistingConnectionRecord,
)
from dexa_sdk.data_controller.records.connection_controller_details_record import (
    ConnectionControllerDetailsRecord,
)
from dexa_sdk.data_controller.records.controller_details_record import (
    ControllerDetailsRecord,
)
from dexa_sdk.did_mydata.core import DIDMyDataBuilder
from dexa_sdk.ledgers.ethereum.core import EthereumClient
from dexa_sdk.ledgers.indy.core import (
    create_cred_def_and_anchor_to_ledger,
    create_schema_def_and_anchor_to_ledger,
)
from dexa_sdk.marketplace.records.marketplace_connection_record import (
    MarketplaceConnectionRecord,
)
from dexa_sdk.utils import (
    PaginationResult,
    bump_major_for_semver_string,
    drop_none_dict,
    fetch_org_details_from_intermediary,
    generate_firebase_dynamic_link,
    paginate,
    paginate_records,
)
from loguru import logger
from marshmallow.exceptions import ValidationError
from mydata_did.patched_protocols.present_proof.v1_0.manager import PresentationManager
from mydata_did.v1_0.decorators.data_agreement_context_decorator import (
    DataAgreementContextDecorator,
)
from mydata_did.v1_0.message_types import (
    DATA_AGREEMENT_NEGOTIATION_ACCEPT,
    DATA_AGREEMENT_NEGOTIATION_OFFER,
)
from mydata_did.v1_0.messages.da_negotiation_receipt import (
    DataAgreementNegotiationReceiptBody,
    DataAgreementNegotiationReceiptMessage,
)
from mydata_did.v1_0.messages.da_permissions import (
    DAPermissionsBodyModel,
    DAPermissionsMessage,
)
from mydata_did.v1_0.messages.data_agreement_accept import (
    DataAgreementNegotiationAcceptMessage,
)
from mydata_did.v1_0.messages.data_agreement_offer import (
    DataAgreementNegotiationOfferMessage,
)
from mydata_did.v1_0.messages.data_agreement_qr_code_initiate import (
    DataAgreementQrCodeInitiateMessage,
)
from mydata_did.v1_0.messages.data_controller_details import (
    DataControllerDetailsMessage,
)
from mydata_did.v1_0.messages.data_controller_details_response import (
    DataControllerDetailsResponseMessage,
)
from mydata_did.v1_0.messages.existing_connections import ExistingConnectionsMessage
from mydata_did.v1_0.messages.fetch_preferences import FetchPreferencesMessage
from mydata_did.v1_0.messages.fetch_preferences_response import (
    FetchPreferencesResponseMessage,
)
from mydata_did.v1_0.messages.json_ld_processed import (
    JSONLDProcessedBody,
    JSONLDProcessedMessage,
)
from mydata_did.v1_0.messages.json_ld_processed_response import (
    JSONLDProcessedResponseBody,
    JSONLDProcessedResponseMessage,
)
from mydata_did.v1_0.models.data_agreement_qr_code_initiate_model import (
    DataAgreementQrCodeInitiateBody,
)
from mydata_did.v1_0.models.data_controller_model import DataController
from mydata_did.v1_0.models.existing_connections_model import ExistingConnectionsBody
from mydata_did.v1_0.models.fetch_preferences_response_model import (
    FetchPreferencesResponseBody,
    FPRControllerDetailsModel,
    FPRDUSModel,
    FPRPrefsModel,
)
from mydata_did.v1_0.utils.util import bool_to_str, str_to_bool
from web3._utils.encoding import to_json


class V2ADAManagerError(BaseError):
    """ADA manager error"""


class V2ADAManager:
    """Manages ADA related functions (v2)"""

    def __init__(self, context: InjectionContext) -> None:
        """Initialise ADA manager

        Args:
            context (InjectionContext): _description_
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

    async def create_invitation(
        self,
        my_label: str = None,
        my_endpoint: str = None,
        their_role: str = None,
        auto_accept: bool = None,
        public: bool = False,
        multi_use: bool = False,
        alias: str = None,
    ) -> typing.Tuple[ConnectionRecord, ConnectionInvitation]:
        """Generate new connection invitation."""

        if not my_label:
            my_label = self.context.settings.get("default_label")

        image_url = None

        # Fetch organisation details from intermediary.
        org_details = await fetch_org_details_from_intermediary(self.context)

        my_label = org_details["Name"]
        image_url = org_details["LogoImageURL"] + "/web"

        wallet: BaseWallet = await self.context.inject(BaseWallet)

        if public:
            if not self.context.settings.get("public_invites"):
                raise ConnectionManagerError("Public invitations are not enabled")

            public_did = await wallet.get_public_did()
            if not public_did:
                raise ConnectionManagerError(
                    "Cannot create public invitation with no public DID"
                )

            if multi_use:
                raise ConnectionManagerError(
                    "Cannot use public and multi_use at the same time"
                )

            # FIXME - allow ledger instance to format public DID with prefix?
            invitation = ConnectionInvitation(
                label=my_label, did=f"did:sov:{public_did.did}", image_url=image_url
            )
            return None, invitation

        invitation_mode = ConnectionRecord.INVITATION_MODE_ONCE
        if multi_use:
            invitation_mode = ConnectionRecord.INVITATION_MODE_MULTI

        if not my_endpoint:
            my_endpoint = self.context.settings.get("default_endpoint")
        accept = (
            ConnectionRecord.ACCEPT_AUTO
            if (
                auto_accept
                or (
                    auto_accept is None
                    and self.context.settings.get("debug.auto_accept_requests")
                )
            )
            else ConnectionRecord.ACCEPT_MANUAL
        )

        # Create and store new invitation key
        connection_key = await wallet.create_signing_key()

        # Create connection record
        connection = ConnectionRecord(
            initiator=ConnectionRecord.INITIATOR_SELF,
            invitation_key=connection_key.verkey,
            their_role=their_role,
            state=ConnectionRecord.STATE_INVITATION,
            accept=accept,
            invitation_mode=invitation_mode,
            alias=alias,
        )

        await connection.save(self.context, reason="Created new invitation")

        # Create connection invitation message
        # Note: Need to split this into two stages to support inbound routing of invites
        # Would want to reuse create_did_document and convert the result
        invitation = ConnectionInvitation(
            label=my_label,
            recipient_keys=[connection_key.verkey],
            endpoint=my_endpoint,
            image_url=image_url,
        )
        await connection.attach_invitation(self.context, invitation)

        return connection, invitation

    async def create_and_store_ledger_payloads_for_da_template(
        self,
        *,
        template_record: DataAgreementTemplateRecord,
        pd_records: typing.List[PersonalDataRecord] = None,
        schema_id: str = None,
    ) -> DataAgreementTemplateRecord:
        """Create and store ledger payloads for a da template

        Args:
            template_record (DataAgreementTemplateRecord): Data agreement template record
            pd_records (typing.List[PersonalDataRecord]): Personal data records
            schema_id (str): Schema identifier if available

        Returns:
            DataAgreementTemplateRecord: Record with ledger payloads
        """
        if (
            template_record.method_of_use
            == DataAgreementTemplateRecord.METHOD_OF_USE_DATA_SOURCE
        ):

            # Create schema if not existing
            if not schema_id:
                data_agreement = template_record.data_agreement
                # Schema name
                schema_name = data_agreement.get("purpose")
                # Schema version
                schema_version = data_agreement.get("version")
                # Schema attributes
                attributes = [
                    personal_data.attribute_name for personal_data in pd_records
                ]
                # Creata schema and anchor to ledger
                (schema_id, schema_def) = await create_schema_def_and_anchor_to_ledger(
                    context=self.context,
                    schema_name=schema_name,
                    schema_version=schema_version,
                    attributes=attributes,
                )

            # Create credential definition and anchor to ledger

            (cred_def_id, cred_def, novel) = await create_cred_def_and_anchor_to_ledger(
                context=self.context, schema_id=schema_id
            )

            template_record.cred_def_id = cred_def_id
            template_record.schema_id = schema_id
            await template_record.save(self.context)

        else:
            data_agreement = template_record.data_agreement

            # Usage purpose
            usage_purpose = data_agreement.get("purpose")

            # Usage purpose description
            usage_purpose_description = data_agreement.get("purposeDescription")

            # Data agreement template version
            da_template_version = data_agreement.get("version")

            # Create presentation request
            presentation_request = self.construct_presentation_request(
                usage_purpose=usage_purpose,
                usage_purpose_description=usage_purpose_description,
                da_template_version=da_template_version,
                personal_data=pd_records,
            )

            template_record.presentation_request = presentation_request
            await template_record.save(self.context)

        return template_record

    def construct_presentation_request(
        self,
        *,
        usage_purpose: str,
        usage_purpose_description: str,
        da_template_version: str,
        personal_data: typing.List[PersonalDataRecord],
    ) -> dict:
        """
        Construct presentation request

        Args:
            usage_purpose: Usage purpose.
            usage_purpose_description: Usage purpose description.
            da_template_version: Data agreement template version.
            personal_data: List of personal data.

        Returns:
            :rtype: dict: Proof request

        """

        presentation_request_dict: dict = {
            "name": usage_purpose,
            "comment": usage_purpose_description,
            "version": da_template_version,
            "requested_attributes": {},
            "requested_predicates": {},
        }

        index = 1
        requested_attributes = {}

        for pd in personal_data:

            requested_attributes["additionalProp" + str(index)] = {
                "name": pd.attribute_name,
                "restrictions": pd.restrictions if pd.restrictions else [],
            }
            if pd.restrictions:
                restrictions = [
                    {
                        "schema_id": restriction.get("schemaId"),
                        "cred_def_id": restriction.get("credDefId"),
                    }
                    for restriction in pd.restrictions
                ]
                requested_attributes["additionalProp" + str(index)].update(
                    {"restrictions": restrictions}
                )
            else:
                requested_attributes["additionalProp" + str(index)].update({})
            index += 1

        presentation_request_dict["requested_attributes"] = requested_attributes

        return presentation_request_dict

    async def create_and_store_da_template_in_wallet(
        self, data_agreement: dict, *, publish_flag: bool = True, schema_id: str = None
    ) -> DataAgreementTemplateRecord:
        """Create and store data agreement template in wallet

        Args:
            data_agreement (dict): Data agreement
            publish_flag (bool): Publish flag
            schema_id (str): Schema identifier
        """

        # Temp hack
        template_version = "1.0.0"
        template_id = str(uuid.uuid4())
        data_agreement.update({"@context": DA_DEFAULT_CONTEXT})
        data_agreement.update({"@id": template_id})
        data_agreement.update({"@type": DA_TYPE})
        data_agreement.update({"version": template_version})

        try:
            # Validate the data agreement.
            data_agreement: DataAgreementModel = DataAgreementModel.deserialize(
                data_agreement
            )
        except ValidationError as err:
            raise V2ADAManagerError(f"Failed to create data agreement; Reason: {err}")

        # Create personal data records
        pds = data_agreement.personal_data
        pd_records = []
        pd_models_with_id = []
        for pd in pds:
            pd_record: PersonalDataRecord = (
                await PersonalDataRecord.build_and_save_record_from_pd_model(
                    self.context, template_id, template_version, pd
                )
            )
            pd_records.append(pd_record)
            pd_models_with_id.append(pd_record.convert_record_to_pd_model())

        # Update the personal data with attribute identifiers to the agreement
        data_agreement.personal_data = pd_models_with_id

        # Create template record
        record = DataAgreementTemplateRecord(
            template_id=template_id,
            template_version=template_version,
            state=DataAgreementTemplateRecord.STATE_DEFINITION,
            method_of_use=data_agreement.method_of_use,
            data_agreement=data_agreement.serialize(),
            publish_flag=bool_to_str(publish_flag),
            schema_id=schema_id,
            existing_schema_flag=bool_to_str(True) if schema_id else bool_to_str(False),
            third_party_data_sharing=bool_to_str(
                data_agreement.data_policy.third_party_data_sharing
            ),
        )

        await record.save(self.context)

        if publish_flag:
            # Create ledger payloads
            record = await self.create_and_store_ledger_payloads_for_da_template(
                template_record=record, pd_records=pd_records, schema_id=schema_id
            )

        return record

    async def query_da_templates_in_wallet(
        self,
        *,
        template_id: str = None,
        delete_flag: str = "false",
        method_of_use: str = None,
        publish_flag: str = "true",
        template_version: str = None,
        latest_version_flag: str = "true",
        third_party_data_sharing: str = "false",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginationResult:
        """Query DA templates in wallet

        Args:
            template_id (str, optional): Template identifier. Defaults to None.
            delete_flag (str, optional): Delete flag. Defaults to false.
            method_of_use (str, optional): Method of use. Defaults to None.
            publish_flag (str, optional): Publish flag. Defaults to true.
            latest_version_flag (str, optional): Latest version flag. Defaults to true.
            template_version (str, optional): Template version. Defaults to None.
            third_party_data_sharing (str, optional): Third party data sharing.
                Defaults to false.
            page (int, optional): Page. Defaults to 1.

        Returns:
            PaginationResult: Pagination results.
        """

        # Query by version is only possible if the template id is provided
        if template_version:
            assert template_id, "Template identifier is required to query by version"

        # Tag filter
        tag_filter = {
            "delete_flag": delete_flag,
            "publish_flag": publish_flag,
            "method_of_use": method_of_use,
            "template_id": template_id,
            "template_version": template_version,
            "latest_version_flag": latest_version_flag,
            "third_party_data_sharing": third_party_data_sharing,
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataAgreementTemplateRecord.query(
            context=self.context, tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.created_at, reverse=True)

        paginate_result = paginate_records(records, page, page_size)

        return paginate_result

    async def publish_da_template_in_wallet(
        self, template_id: str
    ) -> DataAgreementTemplateRecord:
        """Publish data agreement template.

        Args:
            template_id (str): Template identifier

        Returns:
            DataAgreementTemplateRecord: Template record.
        """

        tag_filter = {
            "delete_flag": bool_to_str(False),
            "publish_flag": bool_to_str(False),
            "latest_version_flag": bool_to_str(True),
            "template_id": template_id,
        }

        records = await DataAgreementTemplateRecord.query(
            context=self.context, tag_filter=tag_filter
        )

        assert records, "Data agreement template not found."

        record: DataAgreementTemplateRecord = records[0]

        await record.publish_template(self.context)

        pd_records = await record.fetch_personal_data_records(self.context)

        # Create ledger payloads
        record = await self.create_and_store_ledger_payloads_for_da_template(
            template_record=record, pd_records=pd_records, schema_id=record.schema_id
        )

        return record

    async def update_and_store_da_template_in_wallet(
        self,
        template_id: str,
        data_agreement: dict,
        *,
        publish_flag: bool = True,
        schema_id: str = None,
    ) -> DataAgreementTemplateRecord:
        """Update and store data agreement template in wallet.

        Args:
            template_id (str): Template identifier
            data_agreement (dict): Data agreement
            publish_flag (bool): Publish flag
            schema_id (str): Schema identifier

        Returns:
            DataAgreementTemplateRecord: Updated record.
        """

        # Tag filter
        tag_filter = {
            "delete_flag": bool_to_str(False),
            "template_id": template_id,
            "latest_version_flag": bool_to_str(True),
        }

        # Fetch data agreement record
        record: DataAgreementTemplateRecord = (
            await DataAgreementTemplateRecord.retrieve_by_tag_filter(
                self.context, tag_filter
            )
        )

        # Validate the data agreement.
        previous_da: DataAgreementModel = DataAgreementModel.deserialize(
            record.data_agreement
        )

        assert previous_da.method_of_use == data_agreement.get(
            "methodOfUse"
        ), "Method of use cannot be updated."

        assert previous_da.data_policy.third_party_data_sharing == data_agreement.get(
            "dataPolicy"
        ).get("thirdPartyDataSharing"), "Third party data sharing cannot be updated."

        # Copy the id, version from previous da to new da
        template_version = bump_major_for_semver_string(previous_da.version)
        template_id = previous_da.id
        data_agreement.update({"@context": DA_DEFAULT_CONTEXT})
        data_agreement.update({"@type": DA_TYPE})
        data_agreement.update({"@id": template_id})
        data_agreement.update({"version": template_version})

        updated_da: DataAgreementModel = DataAgreementModel.deserialize(data_agreement)

        # Create personal data records
        pds = updated_da.personal_data
        pd_records = []
        pd_models_with_id = []
        for pd in pds:
            pd_record: PersonalDataRecord = (
                await PersonalDataRecord.build_and_save_record_from_pd_model(
                    self.context, template_id, template_version, pd
                )
            )
            pd_records.append(pd_record)
            pd_models_with_id.append(pd_record.convert_record_to_pd_model())

        # Update the personal data with attribute identifiers to the agreement
        updated_da.personal_data = pd_models_with_id

        record.data_agreement = updated_da.serialize()
        record.publish_flag = bool_to_str(publish_flag)
        record.schema_id = schema_id
        record.existing_schema_flag = (
            bool_to_str(True) if schema_id else bool_to_str(False)
        )
        record.template_version = template_version

        await record.upgrade(self.context)

        if publish_flag:
            # Create ledger payloads
            record = await self.create_and_store_ledger_payloads_for_da_template(
                template_record=record, pd_records=pd_records, schema_id=schema_id
            )

        return record

    async def delete_da_template_in_wallet(self, template_id: str) -> str:
        """Deactivate DA template in wallet.

        This is not a normal delete operation of a specific version of template. Instead it
        marks the template with latest version flag as deleted i.e. Any version under this
        template is no longer active.

        Args:
            template_id (str): Template identifier
            template_version (str): Template version

        Returns:
            record_id: Record identifier for the deleted template.
        """
        # Query for the data agreement by id
        data_agreement_records: DataAgreementTemplateRecord = (
            await DataAgreementTemplateRecord.non_deleted_template_by_id(
                self.context, template_id
            )
        )

        assert data_agreement_records, "Data agreement template not found."
        data_agreement_record = data_agreement_records[0]

        # Mark the data agreement as deleted and save.
        return await data_agreement_record.delete_template(self.context)

    async def query_pd_of_da_template_from_wallet(
        self,
        template_id: str = None,
        method_of_use: str = None,
        third_party_data_sharing: str = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginationResult:
        """Query personal data for DA template.

        Args:
            template_id (str): Template identifier
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Page size. Defaults to 10.

        Returns:
            PaginationResult: Pagination results
        """

        # Tag filter
        tag_filter = {
            "delete_flag": bool_to_str(False),
            "method_of_use": method_of_use,
            "template_id": template_id,
            "latest_version_flag": bool_to_str(True),
            "third_party_data_sharing": third_party_data_sharing,
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataAgreementTemplateRecord.query(
            context=self.context, tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.created_at, reverse=True)

        # Fetch personal data records
        pd_records = []
        for record in records:
            pd_records.extend(await record.fetch_personal_data_records(self.context))

        paginate_result = paginate_records(pd_records, page, page_size)

        return paginate_result

    async def update_personal_data_description(
        self, attribute_id: str, desc: str
    ) -> PersonalDataRecord:
        """Update personal data description

        Args:
            attribute_id (str): Attribute id
            desc (str): Description

        Returns:
            PersonalDataRecord: Personal data record
        """

        # Fetch personal data record by id
        pd_record: PersonalDataRecord = await PersonalDataRecord.retrieve_by_id(
            self.context, attribute_id
        )

        # Fetch the associated data agreement record
        da_template_record: DataAgreementTemplateRecord = (
            await DataAgreementTemplateRecord.latest_template_by_id(
                self.context, pd_record.data_agreement_template_id
            )
        )

        assert da_template_record, "Matching data agreement template not found."
        assert (
            da_template_record.template_version
            == pd_record.data_agreement_template_version
        ), "Matching data agreement template with same version not found."

        # Update the personal data record.
        pd_record.attribute_description = desc
        await pd_record.save(self.context)

        pd_model: DataAgreementPersonalDataModel = (
            pd_record.convert_record_to_pd_model()
        )

        # Update the data agreement record with new personal data.
        da: DataAgreementModel = DataAgreementModel.deserialize(
            da_template_record.data_agreement
        )
        # Iterate through the existing personal data in data agreements
        # And update the personal data matching the attribute id
        da_pds = []
        for da_pd in da.personal_data:
            if da_pd.attribute_id != pd_model.attribute_id:
                da_pds.append(da_pd)
        da_pds.append(pd_model)
        da.personal_data = da_pds

        da_template_record.data_agreement = da.serialize()
        await da_template_record.save(self.context)

        return pd_record

    async def delete_personal_data(self, attribute_id: str) -> None:
        """Delete personal data record.

        On deleting personal data record, the associated data agreement template is
        updated. If the personal data record deleted, is the last one in the template,
        proceed to delete the template record.

        Args:
            attribute_id (str): _description_
        """

        # Fetch personal data record by id
        pd_record: PersonalDataRecord = await PersonalDataRecord.retrieve_by_id(
            self.context, attribute_id
        )

        # Fetch the associated data agreement record
        da_template_record: DataAgreementTemplateRecord = (
            await DataAgreementTemplateRecord.latest_template_by_id(
                self.context, pd_record.data_agreement_template_id
            )
        )

        assert da_template_record, "Matching data agreement template not found."
        assert (
            da_template_record.template_version
            == pd_record.data_agreement_template_version
        ), "Matching data agreement template with same version not found."

        da: DataAgreementModel = DataAgreementModel.deserialize(
            da_template_record.data_agreement
        )

        # Iterate through the existing personal data in data agreements
        # And remove the deleted personal data.
        da_pds = []
        for da_pd in da.personal_data:
            if da_pd.attribute_id != pd_record.attribute_id:
                da_pd.attribute_id = None
                da_pds.append(da_pd)

        da.personal_data = da_pds

        if len(da_pds) == 0:
            await da_template_record.delete_template(self.context)
        else:
            # Update template record with new agreement.
            await self.update_and_store_da_template_in_wallet(
                pd_record.data_agreement_template_id,
                da.serialize(),
                publish_flag=str_to_bool(da_template_record.publish_flag),
            )

    async def build_data_agreement_offer_for_credential_exchange(
        self,
        template_id: str,
        connection_record: ConnectionRecord,
        cred_ex_record: V10CredentialExchange,
    ) -> DataAgreementNegotiationOfferMessage:
        """Build data agreement offer for credential exchange.

        Args:
            context (InjectionContext): Injection context to be used.
            template_id (str): Data agreement template identifier.
            connection_record (ConnectionRecord): Connection record.
            cred_ex_record (V10CredentialExchange): Credential exchange record.

        Returns:
            DataAgreementNegotiationOfferMessage: Offer message.
        """

        # Build instance record
        (
            da_instance_record,
            da_instance_model,
        ) = await DataAgreementInstanceRecord.build_instance_from_template(
            self.context,
            template_id,
            connection_record,
            cred_ex_record.credential_exchange_id,
        )

        # Build negotiation offer agent message
        agent_message = DataAgreementNegotiationOfferMessage(body=da_instance_model)

        return agent_message

    async def build_data_agreement_offer_for_presentation_exchange(
        self,
        template_id: str,
        connection_record: ConnectionRecord,
        pres_ex_record: V10PresentationExchange,
    ) -> DataAgreementNegotiationOfferMessage:
        """Build data agreement offer for presentaton exchange.

        Args:
            context (InjectionContext): Injection context to be used.
            template_id (str): Data agreement template identifier.
            connection_record (ConnectionRecord): Connection record.
            pres_ex_record (V10PresentationExchange): Presentation exchange record.

        Returns:
            DataAgreementNegotiationOfferMessage: Offer message.
        """

        # Build instance record
        (
            da_instance_record,
            da_instance_model,
        ) = await DataAgreementInstanceRecord.build_instance_from_template(
            self.context,
            template_id,
            connection_record,
            pres_ex_record.presentation_exchange_id,
        )

        # Build negotiation offer agent message
        agent_message = DataAgreementNegotiationOfferMessage(body=da_instance_model)

        return agent_message

    async def process_decorator_with_da_offer_message(
        self,
        decorator_set: DecoratorSet,
        data_ex_record: typing.Union[V10CredentialExchange, V10PresentationExchange],
        connection_record: ConnectionRecord,
    ) -> DataAgreementInstanceRecord:
        """Process data agreement context decorator with DA offer message

        Args:
            decorator_set (DecoratorSet): Decorator set
            cred_ex_record (V10CredentialExchange): Credential exchange record
            connection_record (ConnectionRecord): Connection record

        Returns:
            DataAgreementInstanceRecord: Data agreement instance record.
        """

        # Check if data agreement context decorator is present
        if "data-agreement-context" not in decorator_set.keys():
            self._logger.info(
                "Data agreement context decorator is not present in the incoming message."
            )
            return None

        # Deserialize data agreement context decorator
        da_decorator_dict = decorator_set["data-agreement-context"]
        da_decorator_model: DataAgreementContextDecorator = (
            DataAgreementContextDecorator.deserialize(da_decorator_dict)
        )

        assert (
            da_decorator_model.message_type == "protocol"
        ), "DA context message type must be 'protocol'."

        message_type = da_decorator_model.message.get("@type")
        assert (
            DATA_AGREEMENT_NEGOTIATION_OFFER in message_type
        ), f"DA context protocol message type must be '{DATA_AGREEMENT_NEGOTIATION_OFFER}'"

        da_offer_message: DataAgreementNegotiationOfferMessage = (
            DataAgreementNegotiationOfferMessage.deserialize(da_decorator_model.message)
        )

        # Build and save data agreement instance record.
        if data_ex_record.__class__.__name__ == V10CredentialExchange.__name__:
            return await DataAgreementInstanceRecord.build_instance_from_da_offer(
                self.context,
                da_offer_message,
                connection_record,
                data_ex_record.credential_exchange_id,
            )
        else:
            return await DataAgreementInstanceRecord.build_instance_from_da_offer(
                self.context,
                da_offer_message,
                connection_record,
                data_ex_record.presentation_exchange_id,
            )

    async def process_decorator_with_da_accept_message(
        self,
        decorator_set: DecoratorSet,
        data_ex_record: typing.Union[V10CredentialExchange, V10PresentationExchange],
        connection_record: ConnectionRecord,
    ) -> DataAgreementInstanceRecord:
        """Process data agreement context decorator with DA accept message

        Args:
            decorator_set (DecoratorSet): Decorator set
            data_ex_record (typing.Union[V10CredentialExchange, V10PresentationExchange]):
                Data exchange record.
            connection_record (ConnectionRecord): Connection record

        Returns:
            DataAgreementInstanceRecord: Data agreement instance record.
        """

        # Check if data agreement context decorator is present
        if "data-agreement-context" not in decorator_set.keys():
            self._logger.info(
                "Data agreement context decorator is not present in the incoming message."
            )
            return None

        # Deserialize data agreement context decorator
        da_decorator_dict = decorator_set["data-agreement-context"]
        da_decorator_model: DataAgreementContextDecorator = (
            DataAgreementContextDecorator.deserialize(da_decorator_dict)
        )

        assert (
            da_decorator_model.message_type == "protocol"
        ), "DA context message type must be 'protocol'."

        message_type = da_decorator_model.message.get("@type")
        assert (
            DATA_AGREEMENT_NEGOTIATION_ACCEPT in message_type
        ), f"DA context protocol message type must be '{DATA_AGREEMENT_NEGOTIATION_ACCEPT}'"

        da_accept_message: DataAgreementNegotiationAcceptMessage = (
            DataAgreementNegotiationAcceptMessage.deserialize(
                da_decorator_model.message
            )
        )

        # Build and save data agreement instance record.
        if data_ex_record.__class__.__name__ == V10CredentialExchange.__name__:
            # Build and save data agreement instance record.
            instance_record = (
                await DataAgreementInstanceRecord.update_instance_from_da_accept(
                    self.context,
                    da_accept_message,
                    data_ex_record.credential_exchange_id,
                )
            )
        else:
            # Build and save data agreement instance record.
            instance_record = (
                await DataAgreementInstanceRecord.update_instance_from_da_accept(
                    self.context,
                    da_accept_message,
                    data_ex_record.presentation_exchange_id,
                )
            )

        # Anchor da to blockchain.
        await self.anchor_da_instance_to_blockchain_async_task(
            instance_record.instance_id
        )

        return instance_record

    async def build_data_agreement_negotiation_accept_by_instance_id(
        self, instance_id: str, connection_record: ConnectionRecord
    ) -> DataAgreementNegotiationAcceptMessage:
        # Counter sign da
        (
            da_instance_record,
            da_instance_model,
        ) = await DataAgreementInstanceRecord.counter_sign_instance(
            self.context,
            instance_id,
            connection_record,
        )

        # Build negotiation accept agent message
        agent_message = DataAgreementNegotiationAcceptMessage(body=da_instance_model)

        return agent_message

    async def build_data_agreement_accept_for_data_ex_record(
        self,
        connection_record: ConnectionRecord,
        data_ex_record: typing.Union[V10CredentialExchange, V10PresentationExchange],
    ) -> DataAgreementNegotiationAcceptMessage:
        """Build data agreement accept message for credential exchange.

        Args:
            context (InjectionContext): Injection context to be used.
            template_id (str): Data agreement template identifier.
            connection_record (ConnectionRecord): Connection record.
            data_ex_record (typing.Union[V10CredentialExchange, V10PresentationExchange]):
                Data exchange record.

        Returns:
            DataAgreementNegotiationAcceptMessage: Accept message.
        """
        if data_ex_record.__class__.__name__ == V10CredentialExchange.__name__:
            # Fetch data agreement instance matching credential exchange record.
            instance_record = await DataAgreementInstanceRecord.fetch_by_data_ex_id(
                self.context, data_ex_record.credential_exchange_id
            )
        else:
            # Fetch data agreement instance matching credential exchange record.
            instance_record = await DataAgreementInstanceRecord.fetch_by_data_ex_id(
                self.context, data_ex_record.presentation_exchange_id
            )

        # Build instance record
        (
            da_instance_record,
            da_instance_model,
        ) = await DataAgreementInstanceRecord.counter_sign_instance(
            self.context, instance_record.instance_id, connection_record
        )

        # Build negotiation accept agent message
        agent_message = DataAgreementNegotiationAcceptMessage(body=da_instance_model)

        return agent_message

    async def query_data_agreement_instances(
        self,
        instance_id: str,
        template_id: str,
        template_version: str,
        method_of_use: str,
        third_party_data_sharing: str,
        data_ex_id: str,
        data_subject_did: str,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginationResult:
        """Query data agreement instances

        Args:
            instance_id (str): Instance identifier
            template_id (str): Template identifier
            template_version (str): Template version
            method_of_use (str): Method of use
            third_party_data_sharing (str): Third party data sharing
            data_ex_id (str): Data exchange id
            data_subject_did (str): Data subject did
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
            "method_of_use": method_of_use,
            "third_party_data_sharing": third_party_data_sharing,
            "data_ex_id": data_ex_id,
            "data_subject_did": data_subject_did,
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataAgreementInstanceRecord.query(
            context=self.context, tag_filter=tag_filter
        )

        records: typing.List[DataAgreementInstanceRecord] = sorted(
            records, key=lambda k: k.updated_at, reverse=True
        )

        da_instances_with_permissions = []
        for record in records:
            record_dict = record.serialize()
            record_dict.update({"permissions": []})

            # Fetch permissions for the DA instance.
            permissions: typing.List[
                DAInstancePermissionRecord
            ] = await DAInstancePermissionRecord.query(
                self.context, {"instance_id": record.instance_id}
            )

            permissions = sorted(permissions, key=lambda k: k.updated_at, reverse=True)

            for permission in permissions:
                # Update permissions list for DDA instance.
                record_dict["permissions"].append(permission.serialize())

            da_instances_with_permissions.append(record_dict)

        paginate_result = paginate(da_instances_with_permissions, page, page_size)

        return paginate_result

    async def delete_da_instance_by_data_ex_id(self, cred_ex_id: str) -> None:
        """Delete da instance by cred ex id.

        Args:
            cred_ex_id (str): Credential exchange identifier.
        """

        # Data agreement instance
        instance = await DataAgreementInstanceRecord.fetch_by_data_ex_id(
            self.context, cred_ex_id
        )

        await instance.delete_record(self.context)

    async def anchor_da_instance_to_blockchain_async_task_callback(
        self, *args, **kwargs
    ):
        """Anchor DA instance to blockchain async task callback function"""

        # Obtain the completed task.
        completed_task: CompletedTask = args[0]

        # Obtain the results from the task.
        (instance_id, mydata_did, tx_hash, tx_receipt) = completed_task.task.result()

        tag_filter = {"instance_id": instance_id}

        # Fetch data agreement instance record.
        da_instance_records = await DataAgreementInstanceRecord.query(
            self.context,
            tag_filter,
        )

        assert da_instance_records, "Data agreement instance not found."

        da_instance_record: DataAgreementInstanceRecord = da_instance_records[0]

        transaction_receipt = json.loads(to_json(tx_receipt))
        transaction_hash = transaction_receipt.get("transactionHash")

        # Update the data agreement with blockchain metadata.
        da_instance_record.blink = f"blink:ethereum:rinkeby:{transaction_hash}"
        da_instance_record.mydata_did = mydata_did
        da_instance_record.blockchain_receipt = transaction_receipt

        await da_instance_record.save(self.context)

        # Send receipt.
        message = DataAgreementNegotiationReceiptMessage(
            body=DataAgreementNegotiationReceiptBody(
                instance_id=da_instance_record.instance_id,
                blockchain_receipt=transaction_receipt,
                blink=f"blink:ethereum:rinkeby:{transaction_hash}",
                mydata_did=mydata_did,
            )
        )

        # Find the connection record.
        data_subject_did = da_instance_record.data_subject_did.replace("did:sov:", "")
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_did(
            self.context,
            their_did=data_subject_did,
        )

        await self.send_reply_message(message, connection_record.connection_id)

    async def anchor_da_instance_to_blockchain_async_task(self, instance_id: str):
        """Async task to anchor da instance to blockchain.

        Args:
            instance_id (str): Instance id
        """
        pending_task = await self.add_task(
            self.context,
            self.anchor_da_instance_to_blockchain(instance_id),
            self.anchor_da_instance_to_blockchain_async_task_callback,
        )
        self._logger.info(pending_task)

    async def anchor_da_instance_to_blockchain(self, instance_id: str) -> None:
        """Anchor da instance to blockchain.

        Args:
            instance_id (str): Instance id
        """

        eth_client: EthereumClient = await self.context.inject(EthereumClient)

        tag_filter = {"instance_id": instance_id}

        # Fetch data agreement instance record.
        da_instance_records = await DataAgreementInstanceRecord.query(
            self.context,
            tag_filter,
        )

        assert da_instance_records, "Data agreement instance not found."

        da_instance_record: DataAgreementInstanceRecord = da_instance_records[0]
        da_model: DataAgreementInstanceModel = DataAgreementInstanceModel.deserialize(
            da_instance_record.data_agreement
        )

        did_mydata_builder = DIDMyDataBuilder(artefact=da_model)

        (tx_hash, tx_receipt) = await eth_client.emit_da_did(
            did_mydata_builder.mydata_did
        )

        return (
            da_instance_record.instance_id,
            did_mydata_builder.mydata_did,
            tx_hash,
            tx_receipt,
        )

    async def create_data_agreement_qr_code(
        self, template_id: str, multi_use_flag: bool
    ) -> dict:
        """Create data agreement qr code

        Args:
            template_id (str): Template identifier
            multi_use_flag (bool): Multi use flag

        Returns:
            dict: Qr code.
        """

        qr_record = DataAgreementQRCodeRecord(
            template_id=template_id, multi_use_flag=bool_to_str(multi_use_flag)
        )
        await qr_record.save(self.context)

        (connection, invitation) = await self.create_invitation(
            auto_accept=True,
            public=False,
            multi_use=multi_use_flag,
            alias=f"DA_{template_id}_QR_{qr_record._id}",
        )

        qr_record.connection_id = connection.connection_id
        await qr_record.save(self.context)

        res = {"qr_id": qr_record._id, "invitation": invitation.serialize()}

        res_base64 = base64.b64encode(json.dumps(res).encode()).decode()
        payload = (
            self.context.settings.get("default_endpoint") + "?qt=2&qp=" + res_base64
        )

        firebase_dynamic_link = await generate_firebase_dynamic_link(
            self.context, payload
        )
        qr_record.dynamic_link = firebase_dynamic_link
        await qr_record.save(self.context)

        res.update({"dynamic_link": firebase_dynamic_link})

        return res

    async def create_connection_qr_code(self, connection_id: str) -> dict:
        """Create connection QR code.

        Args:
            connection_id (str): Connection identifier.

        Returns:
            dict: Dict with dynamic link.
        """

        # Connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context, connection_id
        )

        # Connection invitation
        connection_invitation: ConnectionInvitation = (
            await connection_record.retrieve_invitation(self.context)
        )

        # Generate firebase dynamic link.
        payload = connection_invitation.to_url()
        firebase_dynamic_link = await generate_firebase_dynamic_link(
            self.context, payload
        )

        res = {"dynamic_link": firebase_dynamic_link}

        return res

    async def query_data_agreement_qr_codes(
        self,
        template_id: str,
    ) -> PaginationResult:
        """Query data agreement qr codes

        Returns:
            PaginationResult: List of qr code records.
        """

        records = await DataAgreementQRCodeRecord.query(
            self.context, {"template_id": template_id}
        )
        pagination_result = paginate_records(records, page=1, page_size=1000000)
        return pagination_result

    async def send_reply_message(
        self, message: AgentMessage, connection_id: str = None
    ) -> None:
        """Send reply message to remote agent.

        Args:
            message (AgentMessage): Agent message.
            connection_id (str): Connection identifier
        """
        # Responder instance
        responder: DispatcherResponder = await self.context.inject(
            BaseResponder, required=False
        )

        if responder:
            await responder.send_reply(message, connection_id=connection_id)

    async def send_problem_report_message(
        self, explain: str, connection_id: str
    ) -> None:
        """Send problem report message as reply.

        Args:
            explain (str): Explaination.
            connection_id (str): Connection id.
        """

        # Responder instance
        responder: DispatcherResponder = await self.context.inject(
            BaseResponder, required=False
        )

        problem_report = ProblemReport(explain_ltxt=explain)

        if responder:
            await responder.send_reply(problem_report, connection_id=connection_id)

    async def delete_data_agreement_qr_code(self, template_id: str, qr_id: str) -> None:
        """Delete data agreement qr code."""
        record = await DataAgreementQRCodeRecord.retrieve_by_id(self.context, qr_id)
        assert record.template_id == template_id, "Data agreement not found."
        await record.delete_record(self.context)

    async def process_data_agreement_qr_code_initiate_message(
        self, message: DataAgreementQrCodeInitiateMessage, receipt: MessageReceipt
    ):
        """Process data QR code initiate message.

        Args:
            message (DataAgreementQrCodeInitiateMessage): Data agreement QR code initiate message.
            receipt (MessageReceipt): Message receipt.
        """
        qr_id = message.body.qr_id
        connection_id = self.context.connection_record.connection_id

        connection_record = await ConnectionRecord.retrieve_by_id(
            self.context, connection_id
        )

        # Fetch the qr code record.
        record: DataAgreementQRCodeRecord = (
            await DataAgreementQRCodeRecord.retrieve_by_id(self.context, qr_id)
        )

        if record._multi_use_flag:
            record._scanned_flag = True
            await record.save(self.context)
        else:
            if record._scanned_flag:
                explain = "Qr code cannot be scanned twice"
                await self.send_problem_report_message(explain, connection_id)
                raise Exception(explain)

        # Fetch data agreement template record.
        template_record: DataAgreementTemplateRecord = (
            await DataAgreementTemplateRecord.latest_template_by_id(
                self.context, record.template_id
            )
        )

        # Construct presentation request
        preset_presentation_request = template_record.presentation_request
        comment = preset_presentation_request.pop("comment")
        if not preset_presentation_request.get("nonce"):
            preset_presentation_request["nonce"] = await generate_pr_nonce()

        presentation_request = PresentationRequest(
            comment=comment,
            request_presentations_attach=[
                AttachDecorator.from_indy_dict(
                    indy_dict=preset_presentation_request,
                    ident=ATTACH_DECO_IDS[PRESENTATION_REQUEST],
                )
            ],
        )

        # Construct presentation exchange record
        presentation_manager = PresentationManager(self.context)
        (pres_ex_record) = await presentation_manager.create_exchange_for_request(
            connection_id=self.context.connection_record.connection_id,
            presentation_request_message=presentation_request,
        )

        # Update qr code with record id.
        record.data_ex_id = pres_ex_record.presentation_exchange_id
        await record.save(self.context)

        offer_message = await self.build_data_agreement_offer_for_presentation_exchange(
            template_record.template_id, connection_record, pres_ex_record
        )

        # Add data agreement context decorator
        presentation_request._decorators[
            "data-agreement-context"
        ] = DataAgreementContextDecorator(
            message_type="protocol", message=offer_message.serialize()
        )

        pres_ex_record.presentation_request_dict = presentation_request.serialize()
        pres_ex_record.template_id = template_record.template_id
        await pres_ex_record.save(self.context)

        await self.send_reply_message(presentation_request, connection_id)

    async def send_qr_code_initiate_message(self, qr_id, connection_id):
        """Send data agreement qr code initiate message.

        Args:
            qr_id (_type_): QR id
            connection_id (_type_): connection id
        """

        message = DataAgreementQrCodeInitiateMessage(
            body=DataAgreementQrCodeInitiateBody(qr_id=qr_id)
        )

        await self.send_reply_message(message, connection_id)

    async def send_data_controller_details_message(self, connection_id: str):
        """Send data controller details message

        Args:
            connection_id (str): Connection ID
        """

        message = DataControllerDetailsMessage()
        await self.send_reply_message(message, connection_id)

    async def get_controller_details_record(self) -> ControllerDetailsRecord:
        """Get controller details record.

        Returns:
            ControllerDetailsRecord: Controller details record.
        """

        # Query controller records.
        records = await ControllerDetailsRecord.query(self.context, {})

        if not records:
            wallet: BaseWallet = await self.context.inject(BaseWallet)
            controller_did = await wallet.get_public_did()
            qualified_controller_did = f"did:sov:{controller_did.did}"

            # Fetch details from intermediary.
            org_details = await fetch_org_details_from_intermediary(self.context)

            record = ControllerDetailsRecord(
                organisation_did=qualified_controller_did,
                organisation_name=org_details["Name"],
                cover_image_url=org_details["CoverImageURL"] + "/web",
                logo_image_url=org_details["LogoImageURL"] + "/web",
                location=org_details["Location"],
                organisation_type=org_details["Type"]["Type"],
                description=org_details["Description"],
                policy_url=org_details["PolicyURL"],
                eula_url=org_details["EulaURL"],
            )

            await record.save(self.context)
        else:
            record = records[0]

        return record

    async def process_data_controller_details_message(
        self, message: DataControllerDetailsMessage, receipt: MessageReceipt
    ):
        """Process data controller details message.

        Args:
            message (DataControllerDetailsMessage): Data controller details message.
            receipt (MessageReceipt): Message receipt.
        """

        # Query controller records.
        records = await ControllerDetailsRecord.query(self.context, {})

        connection_id = self.context.connection_record.connection_id

        if not records:
            wallet: BaseWallet = await self.context.inject(BaseWallet)
            controller_did = await wallet.get_public_did()

            cache: BaseCache = await self.context.inject(BaseCache, required=False)
            cache_key = f"did:sov:{controller_did.did}"

            assert cache, "Cache not available."

            controller_details = None
            async with cache.acquire(cache_key) as entry:
                if entry.result:
                    cached = entry.result
                    controller_details = DataController.deserialize(cached)
                else:
                    org_details = await fetch_org_details_from_intermediary(
                        self.context
                    )

                    # Organisation did
                    organisation_did = f"did:sov:{controller_did.did}"

                    controller_details = DataController(
                        organisation_did=organisation_did,
                        organisation_name=org_details["Name"],
                        cover_image_url=org_details["CoverImageURL"] + "/web",
                        logo_image_url=org_details["LogoImageURL"] + "/web",
                        location=org_details["Location"],
                        organisation_type=org_details["Type"]["Type"],
                        description=org_details["Description"],
                        policy_url=org_details["PolicyURL"],
                        eula_url=org_details["EulaURL"],
                    )
                    cache_val = controller_details.serialize()
                    await entry.set_result(cache_val, 3600)

                response_message = DataControllerDetailsResponseMessage(
                    body=controller_details
                )

                await self.send_reply_message(response_message, connection_id)
        else:
            # If found update record.
            record: ControllerDetailsRecord = records[0]

            controller_details = DataController(
                organisation_did=record.organisation_did,
                organisation_name=record.organisation_name,
                cover_image_url=record.cover_image_url,
                logo_image_url=record.logo_image_url,
                location=record.location,
                organisation_type=record.organisation_type,
                description=record.description,
                policy_url=record.policy_url,
                eula_url=record.eula_url,
            )

            response_message = DataControllerDetailsResponseMessage(
                body=controller_details
            )

            await self.send_reply_message(response_message, connection_id)

    async def update_controller_details(
        self,
        organisation_name: str = None,
        cover_image_url: str = None,
        logo_image_url: str = None,
        location: str = None,
        organisation_type: str = None,
        description: str = None,
        policy_url: str = None,
        eula_url: str = None,
    ) -> ControllerDetailsRecord:
        """Update controller details

        Args:
            organisation_name (str, optional): Organisation name. Defaults to None.
            cover_image_url (str, optional): Cover image URL. Defaults to None.
            logo_image_url (str, optional): Logo image URL. Defaults to None.
            location (str, optional): Location. Defaults to None.
            organisation_type (str, optional): Organisation type. Defaults to None.
            description (str, optional): Description. Defaults to None.
            policy_url (str, optional): Policy URL. Defaults to None.
            eula_url (str, optional): EULA URL. Defaults to None.

        Returns:
            ControllerDetailsRecord: Controller details record.
        """

        # Query controller records.
        records = await ControllerDetailsRecord.query(self.context, {})
        if not records:

            wallet: BaseWallet = await self.context.inject(BaseWallet)

            controller_did = await wallet.get_public_did()

            organisation_did = f"did:sov:{controller_did.did}"

            # If not found, create new record.
            record = ControllerDetailsRecord(
                organisation_did=organisation_did,
                organisation_name=organisation_name,
                cover_image_url=cover_image_url,
                logo_image_url=logo_image_url,
                location=location,
                organisation_type=organisation_type,
                description=description,
                policy_url=policy_url,
                eula_url=eula_url,
            )

            await record.save(self.context)
        else:
            # If found update record.
            record: ControllerDetailsRecord = records[0]
            record.organisation_name = organisation_name
            record.cover_image_url = cover_image_url
            record.logo_image_url = logo_image_url
            record.location = location
            record.organisation_type = organisation_type
            record.description = description
            record.policy_url = policy_url
            record.eula_url = eula_url

            await record.save(self.context)

        return record

    async def process_existing_connections_message(
        self, message: ExistingConnectionsMessage, message_receipt: MessageReceipt
    ):
        """Process existing connections message.

        Args:
            message (ExistingConnectionsMessage): Existing connections message.
            message_receipt (MessageReceipt): Message receipt.
        """

        # Invitation key.
        invitation_key = message_receipt.recipient_verkey

        # Fetch current connection record using invitation key
        connection_record = await ConnectionRecord.retrieve_by_invitation_key(
            self.context, invitation_key
        )

        # Fetch existing connections record for the current connection.
        tag_filter = {"connection_id": connection_record.connection_id}
        existing_connection_records = await ExistingConnectionRecord.query(
            self.context, tag_filter
        )

        if existing_connection_records:
            # Existing connection record.
            existing_connection_record: ExistingConnectionRecord = (
                existing_connection_records[0]
            )

            # Delete the record.
            await existing_connection_record.delete_record(self.context)

        # Fetch associated connection record.
        old_connection_record = await ConnectionRecord.retrieve_by_did(
            self.context, their_did=None, my_did=message.body.theirdid
        )

        # Create a new existing connection record.
        existing_connection_record = ExistingConnectionRecord(
            existing_connection_id=old_connection_record.connection_id,
            my_did=old_connection_record.my_did,
            connection_status="available",
            connection_id=connection_record.connection_id,
        )

        await existing_connection_record.save(self.context)

        # updating the current connection invitation status to inactive
        connection_record.state = ConnectionRecord.STATE_INACTIVE
        await connection_record.save(context=self.context)

    async def get_existing_connection_record_for_new_connection_id(
        self, connection_id: str
    ) -> ExistingConnectionRecord:
        """Get existing connection record for new connection id.

        Args:
            connection_id (str): Connection id.

        Returns:
            ExistingConnectionRecord: Existing connection record.
        """

        # Tag filter.
        tag_filter = {"connection_id": connection_id}

        # Fetch existing connection records.
        existing_connection_records = await ExistingConnectionRecord.query(
            self.context, tag_filter
        )

        res = None
        if existing_connection_records:
            res = existing_connection_records[0]

        return res

    async def send_message_with_connection_invitation_and_return_route_all(
        self,
        message: AgentMessage,
        connection_id: str,
    ) -> typing.Tuple[str, str, dict]:
        """Send message with connection invitation and return route all.

        Args:
            message (AgentMessage): Agent message.
            connection_id (str): Connection id.

        Returns:
            typing.Tuple[str, str, dict]: sender_verkey, recipient_verkey, message_dict
        """
        # Fetch connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context, connection_id
        )

        # Get invitation key.
        invitation_key = connection_record.invitation_key
        # Service enpoint
        invitation = await connection_record.retrieve_invitation(self.context)
        service_endpoint = invitation.endpoint

        # Fetch wallet from context
        wallet: IndyWallet = await self.context.inject(BaseWallet)

        # Set transport return route all
        message._decorators["transport"] = TransportDecorator(return_route="all")

        # Create a local did
        did: DIDInfo = await wallet.create_local_did()

        sender_key = did.verkey
        packed_message = await wallet.pack_message(
            message.to_json(), [invitation_key], sender_key
        )

        headers = {"Content-Type": "application/ssi-agent-wire"}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(service_endpoint, data=packed_message) as response:
                if response.status == 200:
                    message_body = await response.read()

                    # Unpack message
                    unpacked = await wallet.unpack_message(message_body)
                    (message_json, sender_verkey, recipient_verkey) = unpacked

                    # Convert message to dict.
                    message_dict = json.loads(message_json)

                    return (sender_verkey, recipient_verkey, message_dict)

    async def send_message_with_connection_invitation(
        self,
        message: AgentMessage,
        connection_id: str,
    ) -> None:
        """Send message with connection invitation.

        Args:
            message (AgentMessage): Agent message.
            connection_id (str): Connection id.
        """
        # Fetch connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context, connection_id
        )

        # Get invitation key.
        invitation_key = connection_record.invitation_key
        # Service enpoint
        invitation = await connection_record.retrieve_invitation(self.context)
        service_endpoint = invitation.endpoint

        # Fetch wallet from context
        wallet: IndyWallet = await self.context.inject(BaseWallet)

        # Create a local did
        did: DIDInfo = await wallet.create_local_did()

        sender_key = did.verkey
        packed_message = await wallet.pack_message(
            message.to_json(), [invitation_key], sender_key
        )

        headers = {"Content-Type": "application/ssi-agent-wire"}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(service_endpoint, data=packed_message) as response:
                if response.status == 200:
                    self._logger.info("Posted existing connection message...")

    async def send_existing_connections_message(
        self, theirdid: str, connection_id: str
    ):
        """Send existing connections notification message.

        Args:
            theirdid (str): Their DID of remote agent in old connection.
            connection_id (str): Connection identifier.
        """

        # Construct existing connection message.
        message = ExistingConnectionsMessage(
            body=ExistingConnectionsBody(theirdid=theirdid)
        )

        # Send the message to remote agent.
        await self.send_message_with_connection_invitation(message, connection_id)

    async def query_connections_and_categorise_results(
        self,
        tag_filter: dict = None,
        post_filter_positive: dict = None,
        page: int = 1,
        page_size: int = 10,
        org_flag: bool = False,
        marketplace_flag: bool = False,
    ) -> PaginationResult:

        # Query the connection records.
        records = await ConnectionRecord.query(
            self.context, tag_filter, post_filter_positive
        )

        # Sort the connection records.
        records = sorted(records, key=lambda k: k.updated_at, reverse=True)

        res = []
        for record in records:
            tag_filter = {"connection_id": record.connection_id}

            # Fetch controller details attached to the connection.
            controller_details: typing.List[
                ConnectionControllerDetailsRecord
            ] = await ConnectionControllerDetailsRecord.query(self.context, tag_filter)

            # Fetch marketplace connection record.
            marketplace_connections: typing.List[
                MarketplaceConnectionRecord
            ] = await MarketplaceConnectionRecord.query(self.context, tag_filter)

            connection = record.serialize()

            # Update controller details to the connection dict.
            if controller_details:
                connection.update(
                    {
                        "org_flag": True,
                        "controller_details": controller_details[0].controller_details,
                    }
                )
            else:
                connection.update({"controller_details": {}, "org_flag": False})

            if marketplace_connections:
                connection.update({"marketplace_flag": True})
            else:
                connection.update({"marketplace_flag": False})

            # Apply category filter on connections.
            categorise_filter = {
                "org_flag": org_flag,
                "marketplace_flag": marketplace_flag,
            }

            categorise_filter = drop_none_dict(categorise_filter)

            if match_post_filter(connection, categorise_filter, True):
                res.append(connection)

        pagination_result = paginate(
            res, page if page else 1, page_size if page_size else 10
        )

        return pagination_result

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

    async def process_da_negotiation_receipt_message(
        self,
        message: DataAgreementNegotiationReceiptMessage,
        message_receipt: MessageReceipt,
    ):
        """Process DA negotiation receipt message.

        Args:
            message (DataAgreementNegotiationReceiptMessage): DA negotiation receipt message.
            message_receipt (MessageReceipt): Message receipt.
        """

        instance_id = message.body.instance_id
        blockchain_receipt = message.body.blockchain_receipt
        blink = message.body.blink
        mydata_did = message.body.mydata_did

        # Fetch the DDA instance record.
        tag_filter = {"instance_id": instance_id}
        instance_record: DataAgreementInstanceRecord = (
            await DataAgreementInstanceRecord.retrieve_by_tag_filter(
                self.context, tag_filter
            )
        )

        # Update instance record.
        instance_record.blockchain_receipt = blockchain_receipt
        instance_record.blink = blink
        instance_record.mydata_did = mydata_did

        await instance_record.save(self.context)

    async def process_json_ld_processed_message(
        self, json_ld_processed_message: JSONLDProcessedMessage, receipt: MessageReceipt
    ) -> None:
        """Process JSONLD processed message.

        Args:
            json_ld_processed_message (JSONLDProcessedMessage): JSONLD processed message.
            receipt (MessageReceipt): Message receipt.
        """

        # Responder instance
        responder: DispatcherResponder = await self.context.inject(
            BaseResponder, required=False
        )

        # Base64 decode data
        data = base64.b64decode(json_ld_processed_message.body.data_base64)
        data_dict = json.loads(data)

        # Base64 decode signature options
        signature_options = base64.b64decode(
            json_ld_processed_message.body.signature_options_base64
        )
        signature_options_dict = json.loads(signature_options)

        # Create normalised data for JSONLD proofs
        framed, combine_hash = create_verify_data(data_dict, signature_options_dict)

        # Base64 encode framed
        framed_base64_encoded = base64.b64encode(
            json.dumps(framed).encode("utf-8")
        ).decode("utf-8")

        # Base64 encode combine_hash
        combine_hash_base64_encoded = base64.b64encode(
            combine_hash.encode("utf-8")
        ).decode("utf-8")

        # Send response message.
        json_ld_processed_response_message = JSONLDProcessedResponseMessage(
            body=JSONLDProcessedResponseBody(
                framed_base64=framed_base64_encoded,
                combined_hash_base64=combine_hash_base64_encoded,
            ),
        )

        if responder:
            await responder.send_reply(json_ld_processed_response_message)

    async def send_json_ld_processed_message(
        self,
        *,
        connection_id: str,
        data: dict,
        signature_options: dict,
    ) -> None:
        """Send JSONLD processed message.

        Args:
            connection_id (str): Connection ID
            data (dict): Data
            signature_options (dict): Signature options
        """

        # Retrieve connection record by id
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context, connection_id
        )

        # Base64 encode data
        data_base64 = base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")

        # Base64 encode signature options
        signature_options_base64 = base64.b64encode(
            json.dumps(signature_options).encode("utf-8")
        ).decode("utf-8")

        # Construct JSONLD Processed Message
        message = JSONLDProcessedMessage(
            body=JSONLDProcessedBody(
                data_base64=data_base64,
                signature_options_base64=signature_options_base64,
            )
        )

        # Send JSONLD Processed Message
        await self.send_reply_message(message, connection_record.connection_id)

    async def send_da_permissions_message(
        self, instance_id: str, state: str
    ) -> DAInstancePermissionRecord:
        """Send DA permission message.

        Args:
            instance_id (str): Instance ID
            state (str): State of the permission.

        Returns:
            DAInstancePermissionRecord: DA instance permission record.
        """

        # Set permissions locally.
        (
            instance_record,
            permission_record,
        ) = await DAInstancePermissionRecord.add_permission(
            self.context, instance_id, state
        )

        # Send DA permissions message.
        message = DAPermissionsMessage(
            body=DAPermissionsBodyModel(instance_id=instance_id, state=state)
        )

        mgr = V2ADAManager(self.context)
        connection_record = await instance_record.get_connection_record(self.context)
        await mgr.send_reply_message(message, connection_record.connection_id)

        return permission_record

    async def process_da_permissions_message(
        self, message: DAPermissionsMessage, message_receipt: MessageReceipt
    ):
        """Process DA permissions message.

        Args:
            message (DAPermissionsMessage): DA permissions message.
            message_receipt (MessageReceipt): Message receipt.
        """

        instance_id = message.body.instance_id
        state = message.body.state

        # Set permissions.
        await DAInstancePermissionRecord.add_permission(
            self.context, instance_id, state
        )

    async def process_fetch_preference_message(
        self, message: FetchPreferencesMessage, message_receipt: MessageReceipt
    ):
        """Process fetch preference message.

        Args:
            message (FetchPreferencesMessage): Fetch preference message.
            message_receipt (MessageReceipt): Message receipt.
        """
        # Connection record.
        connection_record: ConnectionRecord = self.context.connection_record

        # Fetch all the data agreement instances against this connection.
        # Only those with third party data sharing enabled.
        tag_filter = {
            "connection_id": connection_record.connection_id,
            "third_party_data_sharing": bool_to_str(True),
        }
        instance_records: typing.List[
            DataAgreementInstanceRecord
        ] = await DataAgreementInstanceRecord.query(self.context, tag_filter)

        instance_records = sorted(
            instance_records, key=lambda k: k.updated_at, reverse=True
        )

        # Industry sectors.
        sectors = []

        # Preferences.
        prefs: typing.List[FPRPrefsModel] = []
        for instance_record in instance_records:

            # DA model
            da_model = instance_record.data_agreement_model

            # Sector
            sector = da_model.data_policy.industry_sector.lower()

            # Add to sectors list.
            sectors.append(sector)

            # Fetch permission record for the DA.
            da_permission_record = await DAInstancePermissionRecord.get_latest(
                self.context, instance_record.instance_id
            )

            if not da_permission_record:
                # Add default permission for the DA.

                da_permission_record = await self.send_da_permissions_message(
                    instance_record.instance_id, DAInstancePermissionRecord.STATE_ALLOW
                )

            # Fetch DDA template by DA template ID
            dda_template_tag_filter: dict = {
                "delete_flag": bool_to_str(False),
                "da_template_id": instance_record.template_id,
                "latest_version_flag": bool_to_str(True),
            }
            dda_template_record: typing.List[
                DataDisclosureAgreementTemplateRecord
            ] = await DataDisclosureAgreementTemplateRecord.query(
                self.context, dda_template_tag_filter
            )

            # Data using services.
            dus: typing.List[FPRDUSModel] = []

            if dda_template_record:
                # Fetch DDA instances by DDA template.
                dda_instances: typing.List[
                    DataDisclosureAgreementInstanceRecord
                ] = await DataDisclosureAgreementInstanceRecord.query(
                    self.context,
                    {
                        "template_id": dda_template_record[0].template_id,
                        "state": DataDisclosureAgreementInstanceRecord.STATE_CAPTURE,
                    },
                )

                for dda_instance in dda_instances:
                    connection_controller_details_record: ConnectionControllerDetailsRecord = await dda_instance.fetch_controller_details(
                        self.context
                    )
                    controller_details_model: DataController = (
                        connection_controller_details_record.controller_details_model
                    )
                    dus.append(
                        FPRDUSModel(
                            dda_instance_id=dda_instance.instance_id,
                            controller_details=FPRControllerDetailsModel(
                                organisation_did=controller_details_model.organisation_did,
                                organisation_name=controller_details_model.organisation_name,
                                cover_image_url=controller_details_model.cover_image_url,
                                logo_image_url=controller_details_model.logo_image_url,
                                location=controller_details_model.location,
                                organisation_type=controller_details_model.organisation_type,
                                description=controller_details_model.description,
                                policy_url=controller_details_model.policy_url,
                                eula_url=controller_details_model.eula_url,
                            ),
                        )
                    )

            prefs.append(
                FPRPrefsModel(
                    instance_id=instance_record.instance_id,
                    instance_permission_state=da_permission_record.state,
                    dus=dus,
                    sector=sector,
                )
            )

        # Filter all the duplicate sectors.
        sectors = list(set(sectors))

        # Construct response message.
        res_message = FetchPreferencesResponseMessage(
            body=FetchPreferencesResponseBody(prefs=prefs, sectors=sectors)
        )

        # Send the message.
        await self.send_reply_message(res_message)

    async def send_fetch_preference_message(
        self, connection_id: str
    ) -> FetchPreferencesResponseMessage:
        """Send fetch preference message.

        Args:
            connection_id (str): Connection ID.

        Returns:
            FetchPreferencesResponseMessage: Fetch preferences response message.
        """

        # Construct fetch preference message.
        message = FetchPreferencesMessage()

        # Fetch connection record
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            self.context, connection_id
        )

        (
            sender_verkey,
            recipient_verkey,
            message_dict,
        ) = await self.send_message_with_return_route_all(message, connection_record)

        res_message: FetchPreferencesResponseMessage = (
            await self.get_message_class_from_dict(message_dict)
        )

        return res_message

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

    async def process_fetch_preference_response_message(
        self, message: FetchPreferencesResponseMessage, message_receipt: MessageReceipt
    ):
        """Process fetch preference response message.

        Args:
            message (FetchPreferencesResponseMessage): Fetch preference response message.
            message_receipt (MessageReceipt): Message receipt.
        """
        self._logger.info(json.dumps(message.serialize(), indent=4))
