import asyncio
import uuid
import typing
import json
from loguru import logger
from web3._utils.encoding import to_json
from marshmallow.exceptions import ValidationError
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.error import BaseError
from aries_cloudagent.utils.task_queue import CompletedTask, PendingTask
from aries_cloudagent.transport.pack_format import BaseWireFormat, PackWireFormat
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.messaging.decorators.default import DecoratorSet
from aries_cloudagent.messaging.responder import BaseResponder
from aries_cloudagent.protocols.basicmessage.v1_0.messages.basicmessage import BasicMessage
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange
)
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange
)
from mydata_did.v1_0.utils.util import bool_to_str
from mydata_did.v1_0.messages.data_agreement_offer import (
    DataAgreementNegotiationOfferMessage
)
from mydata_did.v1_0.messages.data_agreement_accept import (
    DataAgreementNegotiationAcceptMessage
)
from mydata_did.v1_0.message_types import (
    DATA_AGREEMENT_NEGOTIATION_OFFER,
    DATA_AGREEMENT_NEGOTIATION_ACCEPT,
)
from mydata_did.v1_0.decorators.data_agreement_context_decorator import (
    DataAgreementContextDecorator,
)
from ..agreements.da.v1_0.models.da_models import (
    DataAgreementModel,
    DA_DEFAULT_CONTEXT,
    DA_TYPE
)
from ..agreements.da.v1_0.records.da_instance_record import DataAgreementInstanceRecord
from ..agreements.da.v1_0.records.da_template_record import DataAgreementTemplateRecord
from ..agreements.da.v1_0.records.personal_data_record import PersonalDataRecord
from ..agreements.da.v1_0.models.da_models import DataAgreementPersonalDataModel
from ..agreements.da.v1_0.models.da_instance_models import DataAgreementInstanceModel
from ..ledgers.indy.core import (
    create_cred_def_and_anchor_to_ledger,
    create_schema_def_and_anchor_to_ledger
)
from ..utils import paginate_records, PaginationResult, drop_none_dict, bump_major_for_semver_string
from ..did_mydata.core import DIDMyDataBuilder
from ..ledgers.ethereum.core import EthereumClient


class V2ADAManagerError(BaseError):
    """ADA manager error"""


class V2ADAManager:
    """Manages ADA related functions (v2)
    """

    def __init__(self, context: InjectionContext) -> None:
        """Initialise ADA manager

        Args:
            context (InjectionContext): _description_
        """

        # Injection context
        self._context = context

        # Logger
        self._logger = logger

    @ property
    def context(self) -> InjectionContext:
        """Accessor for injection context

        Returns:
            InjectionContext: Injection context
        """
        return self._context

    async def create_and_store_ledger_payloads_for_da_template(
            self,
            *,
            template_record: DataAgreementTemplateRecord,
            pd_records: typing.List[PersonalDataRecord] = None,
            schema_id: str = None
    ) -> DataAgreementTemplateRecord:
        """Create and store ledger payloads for a da template

        Args:
            template_record (DataAgreementTemplateRecord): Data agreement template record
            pd_records (typing.List[PersonalDataRecord]): Personal data records
            schema_id (str): Schema identifier if available

        Returns:
            DataAgreementTemplateRecord: Record with ledger payloads
        """
        if template_record.method_of_use == DataAgreementTemplateRecord.METHOD_OF_USE_DATA_SOURCE:

            # Create schema if not existing
            if not schema_id:
                data_agreement = template_record.data_agreement
                # Schema name
                schema_name = data_agreement.get("purpose")
                # Schema version
                schema_version = data_agreement.get("version")
                # Schema attributes
                attributes = [
                    personal_data.attribute_name
                    for personal_data in pd_records
                ]
                # Creata schema and anchor to ledger
                (schema_id, schema_def) = await create_schema_def_and_anchor_to_ledger(
                    context=self.context,
                    schema_name=schema_name,
                    schema_version=schema_version,
                    attributes=attributes
                )

            # Create credential definition and anchor to ledger

            (cred_def_id, cred_def, novel) = await create_cred_def_and_anchor_to_ledger(
                context=self.context,
                schema_id=schema_id
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
                personal_data=pd_records
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
            personal_data: typing.List[PersonalDataRecord]
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
            "requested_predicates": {}
        }

        index = 1
        requested_attributes = {}

        for pd in personal_data:

            requested_attributes["additionalProp" + str(index)] = {
                "name": pd.attribute_name,
                "restrictions": pd.restrictions if pd.restrictions else []
            }
            if pd.restrictions:
                restrictions = [
                    {
                        "schema_id": restriction.get("schemaId"),
                        "cred_def_id": restriction.get("credDefId")
                    }
                    for restriction in pd.restrictions
                ]
                requested_attributes["additionalProp" +
                                     str(index)].update({"restrictions": restrictions})
            else:
                requested_attributes["additionalProp" + str(index)].update({})
            index += 1

        presentation_request_dict["requested_attributes"] = requested_attributes

        return presentation_request_dict

    async def create_and_store_da_template_in_wallet(
            self,
            data_agreement: dict,
            *,
            publish_flag: bool = True,
            schema_id: str = None
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
            data_agreement: DataAgreementModel = DataAgreementModel.deserialize(data_agreement)
        except ValidationError as err:
            raise V2ADAManagerError(
                f"Failed to create data agreement; Reason: {err}"
            )

        # Create personal data records
        pds = data_agreement.personal_data
        pd_records = []
        pd_models_with_id = []
        for pd in pds:
            pd_record: PersonalDataRecord = \
                await PersonalDataRecord.build_and_save_record_from_pd_model(
                    self.context,
                    template_id,
                    template_version,
                    pd
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
                data_agreement.data_policy.third_party_data_sharing)
        )

        await record.save(self.context)

        if publish_flag:
            # Create ledger payloads
            record = await self.create_and_store_ledger_payloads_for_da_template(
                template_record=record,
                pd_records=pd_records,
                schema_id=schema_id
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

        # Sample queue snippet
        await self.sample_queue_snippet()

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
            "third_party_data_sharing": third_party_data_sharing
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataAgreementTemplateRecord.query(
            context=self.context,
            tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.created_at, reverse=True)

        paginate_result = paginate_records(records, page, page_size)

        return paginate_result

    async def publish_da_template_in_wallet(self,
                                            template_id: str) -> DataAgreementTemplateRecord:
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
            "template_id": template_id
        }

        records = await DataAgreementTemplateRecord.query(
            context=self.context,
            tag_filter=tag_filter
        )

        assert records, "Data agreement template not found."

        record: DataAgreementTemplateRecord = records[0]

        await record.publish_template(self.context)

        pd_records = await record.fetch_personal_data_records(self.context)

        # Create ledger payloads
        record = await self.create_and_store_ledger_payloads_for_da_template(
            template_record=record,
            pd_records=pd_records,
            schema_id=record.schema_id
        )

        return record

    async def update_and_store_da_template_in_wallet(
            self,
            template_id: str,
            data_agreement: dict,
            *,
            publish_flag: bool = True,
            schema_id: str = None
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
            "latest_version_flag": bool_to_str(True)
        }

        # Fetch data agreement record
        record: DataAgreementTemplateRecord = \
            await DataAgreementTemplateRecord.retrieve_by_tag_filter(self.context, tag_filter)

        # Validate the data agreement.
        previous_da: DataAgreementModel = DataAgreementModel.deserialize(record.data_agreement)

        assert previous_da.method_of_use == data_agreement.get(
            "methodOfUse"), "Method of use cannot be updated."

        assert previous_da.data_policy.third_party_data_sharing \
            == data_agreement.get("dataPolicy").get("thirdPartyDataSharing"), \
            "Third party data sharing cannot be updated."

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
            pd_record: PersonalDataRecord = \
                await PersonalDataRecord.build_and_save_record_from_pd_model(
                    self.context,
                    template_id,
                    template_version,
                    pd
                )
            pd_records.append(pd_record)
            pd_models_with_id.append(pd_record.convert_record_to_pd_model())

        # Update the personal data with attribute identifiers to the agreement
        updated_da.personal_data = pd_models_with_id

        record.data_agreement = updated_da.serialize()
        record.publish_flag = bool_to_str(publish_flag)
        record.schema_id = schema_id
        record.existing_schema_flag = bool_to_str(True) if schema_id else bool_to_str(False)
        record.template_version = template_version

        await record.upgrade(self.context)

        if publish_flag:
            # Create ledger payloads
            record = await self.create_and_store_ledger_payloads_for_da_template(
                template_record=record,
                pd_records=pd_records,
                schema_id=schema_id
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
        data_agreement_records: DataAgreementTemplateRecord = \
            await DataAgreementTemplateRecord.non_deleted_template_by_id(
                self.context,
                template_id
            )

        assert data_agreement_records, "Data agreement template not found."
        data_agreement_record = data_agreement_records[0]

        # Mark the data agreement as deleted and save.
        return await data_agreement_record.delete_template(self.context)

    async def query_pd_of_da_template_from_wallet(self,
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
            "third_party_data_sharing": third_party_data_sharing
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataAgreementTemplateRecord.query(
            context=self.context,
            tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.created_at, reverse=True)

        # Fetch personal data records
        pd_records = []
        for record in records:
            pd_records.extend(await record.fetch_personal_data_records(self.context))

        paginate_result = paginate_records(pd_records, page, page_size)

        return paginate_result

    async def update_personal_data_description(self,
                                               attribute_id: str,
                                               desc: str) -> PersonalDataRecord:
        """Update personal data description

        Args:
            attribute_id (str): Attribute id
            desc (str): Description

        Returns:
            PersonalDataRecord: Personal data record
        """

        # Fetch personal data record by id
        pd_record: PersonalDataRecord = await PersonalDataRecord.retrieve_by_id(
            self.context,
            attribute_id
        )

        # Fetch the associated data agreement record
        da_template_record: DataAgreementTemplateRecord = \
            await DataAgreementTemplateRecord.latest_template_by_id(
                self.context,
                pd_record.data_agreement_template_id
            )

        assert da_template_record, "Matching data agreement template not found."
        assert da_template_record.template_version == \
            pd_record.data_agreement_template_version, \
            "Matching data agreement template with same version not found."

        # Update the personal data record.
        pd_record.attribute_description = desc
        await pd_record.save(self.context)

        pd_model: DataAgreementPersonalDataModel = pd_record.convert_record_to_pd_model()

        # Update the data agreement record with new personal data.
        da: DataAgreementModel = DataAgreementModel.deserialize(da_template_record.data_agreement)
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
            self.context,
            attribute_id
        )

        # Fetch the associated data agreement record
        da_template_record: DataAgreementTemplateRecord = \
            await DataAgreementTemplateRecord.latest_template_by_id(
                self.context,
                pd_record.data_agreement_template_id
            )

        assert da_template_record, "Matching data agreement template not found."
        assert da_template_record.template_version == \
            pd_record.data_agreement_template_version, \
            "Matching data agreement template with same version not found."

        # Delete personal data record
        await pd_record.delete_record(self.context)

        da: DataAgreementModel = DataAgreementModel.deserialize(da_template_record.data_agreement)

        # Iterate through the existing personal data in data agreements
        # And remove the deleted personal data.
        da_pds = []
        for da_pd in da.personal_data:
            if da_pd.attribute_id != pd_record.attribute_id:
                da_pds.append(da_pd)

        da.personal_data = da_pds

        da_template_record.data_agreement = da.serialize()
        await da_template_record.upgrade(self.context)

        # Mark data agreement template as deleted if number of personal data is zero
        if len(da_pds) == 0:
            await da_template_record.delete_template(self.context)
        else:

            pd_records = await da_template_record.fetch_personal_data_records(self.context)

            if da_template_record._publish_flag:
                # Create ledger payloads
                await self.create_and_store_ledger_payloads_for_da_template(
                    template_record=da_template_record,
                    pd_records=pd_records,
                    schema_id=None
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
        (da_instance_record, da_instance_model) = \
            await DataAgreementInstanceRecord.build_instance_from_template(
            self.context,
            template_id,
            connection_record,
            cred_ex_record.credential_exchange_id
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
        (da_instance_record, da_instance_model) = \
            await DataAgreementInstanceRecord.build_instance_from_template(
            self.context,
            template_id,
            connection_record,
            pres_ex_record.presentation_exchange_id
        )

        # Build negotiation offer agent message
        agent_message = DataAgreementNegotiationOfferMessage(body=da_instance_model)

        return agent_message

    async def process_decorator_with_da_offer_message(
        self,
        decorator_set: DecoratorSet,
        data_ex_record: typing.Union[V10CredentialExchange, V10PresentationExchange],
        connection_record: ConnectionRecord
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
                "Data agreement context decorator is not present in the incoming message.")
            return None

        # Deserialize data agreement context decorator
        da_decorator_dict = decorator_set["data-agreement-context"]
        da_decorator_model: DataAgreementContextDecorator = \
            DataAgreementContextDecorator.deserialize(da_decorator_dict)

        assert da_decorator_model.message_type == "protocol", \
            "DA context message type must be 'protocol'."

        message_type = da_decorator_model.message.get("@type")
        assert DATA_AGREEMENT_NEGOTIATION_OFFER in message_type, \
            f"DA context protocol message type must be '{DATA_AGREEMENT_NEGOTIATION_OFFER}'"

        da_offer_message: DataAgreementNegotiationOfferMessage = \
            DataAgreementNegotiationOfferMessage.deserialize(da_decorator_model.message)

        # Build and save data agreement instance record.
        if data_ex_record.__class__.__name__ == V10CredentialExchange.__name__:
            return await DataAgreementInstanceRecord.build_instance_from_da_offer(
                self.context,
                da_offer_message,
                connection_record,
                data_ex_record.credential_exchange_id
            )
        else:
            return await DataAgreementInstanceRecord.build_instance_from_da_offer(
                self.context,
                da_offer_message,
                connection_record,
                data_ex_record.presentation_exchange_id
            )

    async def process_decorator_with_da_accept_message(
        self,
        decorator_set: DecoratorSet,
        data_ex_record: typing.Union[V10CredentialExchange, V10PresentationExchange],
        connection_record: ConnectionRecord
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
                "Data agreement context decorator is not present in the incoming message.")
            return None

        # Deserialize data agreement context decorator
        da_decorator_dict = decorator_set["data-agreement-context"]
        da_decorator_model: DataAgreementContextDecorator = \
            DataAgreementContextDecorator.deserialize(da_decorator_dict)

        assert da_decorator_model.message_type == "protocol", \
            "DA context message type must be 'protocol'."

        message_type = da_decorator_model.message.get("@type")
        assert DATA_AGREEMENT_NEGOTIATION_ACCEPT in message_type, \
            f"DA context protocol message type must be '{DATA_AGREEMENT_NEGOTIATION_ACCEPT}'"

        da_accept_message: DataAgreementNegotiationAcceptMessage = \
            DataAgreementNegotiationAcceptMessage.deserialize(da_decorator_model.message)

        # Build and save data agreement instance record.
        if data_ex_record.__class__.__name__ == V10CredentialExchange.__name__:
            # Build and save data agreement instance record.
            instance_record = await DataAgreementInstanceRecord.update_instance_from_da_accept(
                self.context,
                da_accept_message,
                data_ex_record.credential_exchange_id
            )
        else:
            # Build and save data agreement instance record.
            instance_record = await DataAgreementInstanceRecord.update_instance_from_da_accept(
                self.context,
                da_accept_message,
                data_ex_record.presentation_exchange_id
            )

        # Anchor da to blockchain.
        await self.anchor_da_instance_to_blockchain_async_task(instance_record.instance_id)

        return instance_record

    async def build_data_agreement_negotiation_accept_by_instance_id(
        self,
        instance_id: str,
        connection_record: ConnectionRecord
    ) -> DataAgreementNegotiationAcceptMessage:
        # Counter sign da
        (da_instance_record, da_instance_model) = \
            await DataAgreementInstanceRecord.counter_sign_instance(
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
                self.context,
                data_ex_record.credential_exchange_id
            )
        else:
            # Fetch data agreement instance matching credential exchange record.
            instance_record = await DataAgreementInstanceRecord.fetch_by_data_ex_id(
                self.context,
                data_ex_record.presentation_exchange_id
            )

        # Build instance record
        (da_instance_record, da_instance_model) = \
            await DataAgreementInstanceRecord.counter_sign_instance(
            self.context,
            instance_record.instance_id,
            connection_record
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
        page_size: int = 10
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
            "data_subject_did": data_subject_did
        }

        tag_filter = drop_none_dict(tag_filter)

        records = await DataAgreementInstanceRecord.query(
            context=self.context,
            tag_filter=tag_filter
        )

        records = sorted(records, key=lambda k: k.created_at, reverse=True)

        paginate_result = paginate_records(records, page, page_size)

        return paginate_result

    async def delete_da_instance_by_data_ex_id(
        self,
        cred_ex_id: str
    ) -> None:
        """Delete da instance by cred ex id.

        Args:
            cred_ex_id (str): Credential exchange identifier.
        """

        # Data agreement instance
        instance = await DataAgreementInstanceRecord.fetch_by_data_ex_id(
            self.context,
            cred_ex_id
        )

        await instance.delete_record(self.context)

    async def anchor_da_instance_to_blockchain_async_task_callback(
        self, *args, **kwargs
    ):
        """Anchor DA instance to blockchain async task callback function
        """

        # Obtain the completed task.
        completed_task: CompletedTask = args[0]

        # Obtain the results from the task.
        (instance_id, mydata_did, tx_hash, tx_receipt) = completed_task.task.result()

        tag_filter = {
            "instance_id": instance_id
        }

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

    async def anchor_da_instance_to_blockchain_async_task(
        self,
        instance_id: str
    ):
        """Async task to anchor da instance to blockchain.

        Args:
            instance_id (str): Instance id
        """
        pending_task = await self.add_task(
            self.context,
            self.anchor_da_instance_to_blockchain(instance_id),
            self.anchor_da_instance_to_blockchain_async_task_callback
        )
        self._logger.info(pending_task)

    async def anchor_da_instance_to_blockchain(
        self,
        instance_id: str
    ) -> None:
        """Anchor da instance to blockchain.

        Args:
            instance_id (str): Instance id
        """

        eth_client: EthereumClient = await self.context.inject(EthereumClient)

        tag_filter = {
            "instance_id": instance_id
        }

        # Fetch data agreement instance record.
        da_instance_records = await DataAgreementInstanceRecord.query(
            self.context,
            tag_filter,
        )

        assert da_instance_records, "Data agreement instance not found."

        da_instance_record: DataAgreementInstanceRecord = da_instance_records[0]
        da_model: DataAgreementInstanceModel = \
            DataAgreementInstanceModel.deserialize(da_instance_record.data_agreement)

        did_mydata_builder = DIDMyDataBuilder(
            artefact=da_model
        )

        (tx_hash, tx_receipt) = await eth_client.emit_da_did(did_mydata_builder.mydata_did)

        return (da_instance_record.instance_id, did_mydata_builder.mydata_did, tx_hash, tx_receipt)

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

    async def sample_queue_snippet(self):
        """Sample queue snippet"""
        pending_task = await self.add_task(self.context,
                                           self.long_running_task(),
                                           self.queue_callback)
        print(pending_task)

    async def long_running_task(self):
        """Sample long running task"""
        print("Long running task commenced...")
        await asyncio.sleep(10)
        return "msg: Hi from long running task!"

    async def queue_callback(self, *args, **kwargs):
        """Sample queue callback function"""
        print("Recieved call back...")
        completed_task: CompletedTask = args[0]
        result: str = completed_task.task.result()

        print(result)
        print(self.context)

        # Send a basic message to available active connection
        tag_filter = {}
        post_filter = {"state": "active"}
        records: typing.List[ConnectionRecord] = await ConnectionRecord.query(
            self.context,
            tag_filter,
            post_filter
        )

        responder: BaseResponder = await self.context.inject(BaseResponder, required=False)
        basic_message = BasicMessage(content="Triggered by task queue callback...")
        if responder:
            for record in records:
                await responder.send(basic_message, connection_id=record.connection_id)
