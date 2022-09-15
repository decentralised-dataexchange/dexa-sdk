import typing
import uuid

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.messaging.valid import UUIDFour
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.wallet.indy import IndyWallet
from dexa_sdk.agreements.da.v1_0.models.da_instance_models import (
    DataAgreementInstanceModel,
)
from dexa_sdk.agreements.da.v1_0.records.da_template_record import (
    DataAgreementTemplateRecord,
)
from dexa_sdk.jsonld.core import sign_agreement, verify_agreement
from loguru import logger
from marshmallow import EXCLUDE, fields, validate
from mydata_did.v1_0.messages.data_agreement_accept import (
    DataAgreementNegotiationAcceptMessage,
)
from mydata_did.v1_0.messages.data_agreement_offer import (
    DataAgreementNegotiationOfferMessage,
)
from mydata_did.v1_0.utils.util import bool_to_str, current_datetime_in_iso8601


class DataAgreementInstanceRecord(BaseRecord):
    """Data agreement instance record to be persisted in the storage"""

    class Meta:
        # Schema class
        schema_class = "DataAgreementInstanceRecordSchema"

    # Record type
    RECORD_TYPE = "data_agreement_instance"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = "data_agreement_instance"

    # Record tags
    TAG_NAMES = {
        "~instance_id",
        "~template_id",
        "~template_version",
        "~method_of_use",
        "~third_party_data_sharing",
        "~data_ex_id",
        "~data_subject_did",
        "~controller_did",
        "~mydata_did",
        "~blink",
        "~connection_id",
        "~state",
    }

    # States of the data agreement.
    STATE_DEFINITION = "DEFINITION"
    STATE_PREPARATION = "PREPARATION"
    STATE_CAPTURE = "CAPTURE"
    STATE_PROOF = "PROOF"

    METHOD_OF_USE_DATA_SOURCE = "data-source"
    METHOD_OF_USE_DATA_USING_SERVICE = "data-using-service"

    def __init__(
        self,
        *,
        id: str = None,
        instance_id: str = None,
        template_id: str = None,
        template_version: str = None,
        state: str = None,
        method_of_use: str = None,
        data_agreement: dict = None,
        third_party_data_sharing: str = "false",
        data_ex_id: str = None,
        data_subject_did: str = None,
        controller_did: str = None,
        mydata_did: str = None,
        blink: str = None,
        blockchain_receipt: dict = None,
        connection_id: str = None,
        **kwargs,
    ):
        """Instantiate data agreement instance record

        Args:
            id (str, optional): Record id. Defaults to None.
            instance_id (str, optional): Instance id. Defaults to None.
            template_id (str, optional): Template id. Defaults to None.
            template_version (str, optional): Template version. Defaults to None.
            state (str, optional): State. Defaults to None.
            method_of_use (str, optional): Method of use. Defaults to None.
            data_agreement (dict, optional): Data agreement. Defaults to None.
            third_party_data_sharing (str, optional): Third party data sharing. Defaults to "false".
            cred_ex_id (str, optional): Credential exchange identifier. Defaults to None.
            pres_ex_id (str, optional): Presentation exchange identifier. Defaults to None.
            data_subject_did (str, optional): Data subject did. Defaults to None.
            controller_did (str, optional): Controller did. Defaults to None.
            mydata_did (str, optional): did:mydata identifier for the instance. Defaults to None.
            blink (str, optional): blockchain link for mydata_did. Defaults to None.
            blockchain_receipt (dict, optional): Blockchain receipt. Defaults to None.
            connection_id (str, optional): Connection ID. Defaults to None.
        """

        # Pass identifier and state to parent class
        super().__init__(id, state, **kwargs)

        if not template_id:
            raise TypeError("Template identifier is not specified.")

        if not instance_id:
            raise TypeError("Instance identifier is not specified.")

        if not template_version:
            raise TypeError("Template version is not specified.")

        # Set the record attributes
        self.instance_id = instance_id
        self.template_id = template_id
        self.template_version = template_version
        self.method_of_use = method_of_use
        self.state = state
        self.data_agreement = data_agreement
        self.third_party_data_sharing = third_party_data_sharing
        self.data_ex_id = data_ex_id
        self.data_subject_did = data_subject_did
        self.controller_did = controller_did
        self.mydata_did = mydata_did
        self.blink = blink
        self.blockchain_receipt = blockchain_receipt
        self.connection_id = connection_id

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "instance_id",
                "template_id",
                "template_version",
                "method_of_use",
                "state",
                "data_agreement",
                "third_party_data_sharing",
                "data_ex_id",
                "data_subject_did",
                "controller_did",
                "mydata_did",
                "blink",
                "blockchain_receipt",
                "connection_id",
            )
        }

    @staticmethod
    async def build_instance_from_da_offer(
        context: InjectionContext,
        da_offer: DataAgreementNegotiationOfferMessage,
        connection_record: ConnectionRecord,
        data_ex_id: str,
    ) -> "DataAgreementInstanceRecord":
        """Build instance from da offer.

        Args:
            context (InjectionContext): Injection context to be used.
            da_offer (DataAgreementNegotiationOfferMessage): Data Agreement offer
            connection_record (ConnectionRecord): Connection record.
            data_ex_id (str): Data exchange record identifier.

        Returns:
            DataAgreementInstanceRecord: Data agreement instance record.
        """

        # Data agreement
        da_model: DataAgreementInstanceModel = da_offer.body

        da_instance = DataAgreementInstanceRecord(
            instance_id=da_model.id,
            template_id=da_model.template_id,
            template_version=da_model.template_version,
            state=DataAgreementInstanceRecord.STATE_PREPARATION,
            method_of_use=da_model.method_of_use,
            data_agreement=da_model.serialize(),
            third_party_data_sharing=bool_to_str(
                da_model.data_policy.third_party_data_sharing
            ),
            data_ex_id=data_ex_id,
            data_subject_did=f"did:sov:{connection_record.my_did}",
            controller_did=f"did:sov:{connection_record.their_did}",
            connection_id=connection_record.connection_id,
        )

        await da_instance.save(context)

        return da_instance

    @staticmethod
    async def update_instance_from_da_accept(
        context: InjectionContext,
        da_accept: DataAgreementNegotiationAcceptMessage,
        data_ex_id: str,
    ) -> "DataAgreementInstanceRecord":
        """Update instance record with da accept message.

        Args:
            context (InjectionContext): Injection context to be used.
            da_accept (DataAgreementNegotiationAcceptMessage): DA accept message.
            data_ex_id (str): Data exchange record identifier.

        Returns:
            DataAgreementInstanceRecord: Data agreement instance record.
        """

        # Fetch instance record matching the credential exchange record identifier
        tag_filter = {"data_ex_id": data_ex_id}
        instance_records = await DataAgreementInstanceRecord.query(context, tag_filter)

        assert instance_records, "Data agreement instance record not found."
        instance_record: DataAgreementInstanceRecord = instance_records[0]

        # Fetch wallet from context
        wallet: IndyWallet = await context.inject(BaseWallet)

        # Verify agreement
        valid = await verify_agreement(
            agreement=da_accept.body.serialize(), wallet=wallet
        )

        assert valid, "Data agreement instance verification failed."
        logger.info(
            f"Data agreement({instance_record.instance_id}) successfully verified."
        )

        instance_record.state = DataAgreementInstanceRecord.STATE_CAPTURE
        instance_record.data_agreement = da_accept.body.serialize()
        await instance_record.save(context)

        return instance_record

    @staticmethod
    async def build_instance_from_template(
        context: InjectionContext,
        template_id: str,
        connection_record: ConnectionRecord,
        data_ex_id: str,
    ) -> typing.Union["DataAgreementInstanceRecord", DataAgreementInstanceModel]:
        """Build instance from template.

        Args:
            context (InjectionContext): Injection context to be used.
            template_id (str): Template identifier
        """

        # Fetch the data agreement template.
        template: DataAgreementTemplateRecord = (
            await DataAgreementTemplateRecord.latest_template_by_id(
                context, template_id
            )
        )

        assert template._publish_flag, "Data agreement template is not published."

        da = template.data_agreement

        # Fetch wallet from context
        wallet: IndyWallet = await context.inject(BaseWallet)

        # Controller did (Public did)
        controller_did = await wallet.get_public_did()

        # Signature options
        signature_options = {
            "id": f"did:sov:{controller_did.did}#1",
            "type": "Ed25519Signature2018",
            "created": current_datetime_in_iso8601(),
            "verificationMethod": f"{controller_did.verkey}",
            "proofPurpose": "authentication",
        }

        # Add template id, version, data subject did to da
        instance_id = str(uuid.uuid4())
        instance_version = "1.0.0"
        da.update({"templateId": template.template_id})
        da.update({"templateVersion": template.template_version})
        da.update({"@id": instance_id})
        da.update({"version": instance_version})
        da.update({"dataSubjectDid": f"did:sov:{connection_record.their_did}"})

        # Sign the data agreement
        signed_da = await sign_agreement(
            agreement=da,
            verkey=controller_did.verkey,
            wallet=wallet,
            signature_options=signature_options,
        )

        da_model: DataAgreementInstanceModel = DataAgreementInstanceModel.deserialize(
            signed_da
        )

        da_instance = DataAgreementInstanceRecord(
            instance_id=instance_id,
            template_id=template.template_id,
            template_version=template.template_version,
            state=DataAgreementInstanceRecord.STATE_PREPARATION,
            method_of_use=template.method_of_use,
            data_agreement=da_model.serialize(),
            third_party_data_sharing=template.third_party_data_sharing,
            data_ex_id=data_ex_id,
            data_subject_did=f"did:sov:{connection_record.their_did}",
            controller_did=f"did:sov:{controller_did.did}",
            connection_id=connection_record.connection_id,
        )

        await da_instance.save(context)

        return (da_instance, da_model)

    @staticmethod
    async def counter_sign_instance(
        context: InjectionContext, instance_id: str, connection_record: ConnectionRecord
    ) -> typing.Union["DataAgreementInstanceRecord", DataAgreementInstanceModel]:
        """Counter sign data agreement instance"""

        # Fetch wallet from context
        wallet: IndyWallet = await context.inject(BaseWallet)

        data_subject_did = await wallet.get_local_did(connection_record.my_did)

        tag_filter = {"instance_id": instance_id}

        # Fetch data agreement instance record.
        da_instance_records = await DataAgreementInstanceRecord.query(
            context,
            tag_filter,
        )

        assert da_instance_records, "DA instance record not found."
        da_instance_record: DataAgreementInstanceRecord = da_instance_records[0]

        da = da_instance_record.data_agreement

        # Verify agreement
        valid = await verify_agreement(agreement=da.copy(), wallet=wallet)

        assert valid, "Data agreement instance verification failed."
        logger.info(
            f"Data agreement({da_instance_record.instance_id}) successfully verified."
        )

        # Signature options
        signature_options = {
            "id": f"did:sov:{data_subject_did.did}#1",
            "type": "Ed25519Signature2018",
            "created": current_datetime_in_iso8601(),
            "verificationMethod": f"{data_subject_did.verkey}",
            "proofPurpose": "authentication",
        }

        # Sign the data agreement
        signed_da = await sign_agreement(
            agreement=da,
            verkey=data_subject_did.verkey,
            wallet=wallet,
            signature_options=signature_options,
        )

        da_model: DataAgreementInstanceModel = DataAgreementInstanceModel.deserialize(
            signed_da
        )

        da_instance_record.state = DataAgreementInstanceRecord.STATE_CAPTURE
        da_instance_record.data_agreement = da_model.serialize()
        await da_instance_record.save(context)

        return (da_instance_record, da_model)

    @staticmethod
    async def fetch_by_data_ex_id(
        context: InjectionContext, data_ex_id: str
    ) -> "DataAgreementInstanceRecord":
        """Fetch by data exchange record identifier

        Args:
            context (InjectionContext): Injection context to be used.
            data_ex_id (str): Data exchange record identifier

        Returns:
            DataAgreementInstanceRecord: Data agreement instance record.
        """

        tag_filter = {"data_ex_id": data_ex_id}
        instances = await DataAgreementInstanceRecord.query(context, tag_filter)

        assert instances, "Data agreement instance not found."

        return instances[0]

    async def get_connection_record(
        self, context: InjectionContext
    ) -> ConnectionRecord:
        """Get connection record.

        Args:
            context (InjectionContext): Injection context to be used.

        Returns:
            ConnectionRecord: Connection record.
        """

        # Find the connection record.
        connection_record: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            context, self.connection_id
        )

        return connection_record

    @property
    def data_agreement_model(self) -> DataAgreementInstanceModel:
        """Accessor for data agreement instance model.

        Returns:
            DataAgreementInstanceModel: DA instance model.
        """
        return DataAgreementInstanceModel.deserialize(self.data_agreement)


class DataAgreementInstanceRecordSchema(BaseRecordSchema):
    """Data agreement instance record schema"""

    class Meta:
        # Model class
        model_class = DataAgreementInstanceRecord

        # Unknown fields are excluded
        unknown = EXCLUDE

    # Data agreement instance identifier
    instance_id = fields.Str(required=True, example=UUIDFour.EXAMPLE)

    # Data agreement template identifier
    template_id = fields.Str(required=True, example=UUIDFour.EXAMPLE)

    # Data agreement template version
    template_version = fields.Str(required=False)

    # State of the data agreement.
    state = fields.Str(
        required=True,
        example=DataAgreementInstanceRecord.STATE_PREPARATION,
        validate=validate.OneOf(
            [
                DataAgreementInstanceRecord.STATE_DEFINITION,
                DataAgreementInstanceRecord.STATE_PREPARATION,
            ]
        ),
    )

    # Method of use for the data agreement.
    method_of_use = fields.Str(
        required=True,
        example="data-source",
        validate=validate.OneOf(
            [
                DataAgreementInstanceRecord.METHOD_OF_USE_DATA_SOURCE,
                DataAgreementInstanceRecord.METHOD_OF_USE_DATA_USING_SERVICE,
            ]
        ),
    )

    # Data agreement
    data_agreement = fields.Dict(required=True)

    # Third party data sharing
    third_party_data_sharing = fields.Str(
        required=True,
        example="false",
        validate=validate.OneOf(
            [
                "true",
                "false",
            ]
        ),
    )

    # Data exchange identifier
    data_ex_id = fields.Str(required=False)

    # Data subject did
    data_subject_did = fields.Str(required=False)

    # Controller did
    controller_did = fields.Str(required=False)

    # did:mydata identifier for the data agreement instance
    mydata_did = fields.Str(required=False)

    # blockchain link for the data agreement instance.
    blink = fields.Str(required=False)

    # Blockchain receipt
    blockchain_receipt = fields.Dict(required=False)

    # Connection ID
    connection_id = fields.Str(required=False)
