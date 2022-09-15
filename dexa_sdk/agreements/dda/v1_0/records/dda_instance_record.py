import typing
import uuid

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.messaging.valid import UUIDFour
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.wallet.indy import IndyWallet
from dexa_protocol.v1_0.messages.negotiation.accept_dda import AcceptDDAMessage
from dexa_protocol.v1_0.messages.negotiation.offer_dda import OfferDDAMessage
from dexa_protocol.v1_0.models.offer_dda_model import CustomerIdentificationModel
from dexa_sdk.agreements.dda.v1_0.models.dda_instance_models import (
    DataDisclosureAgreementInstanceModel,
    DataUsingServiceModel,
)
from dexa_sdk.agreements.dda.v1_0.records.dda_template_record import (
    DataDisclosureAgreementTemplateRecord,
)
from dexa_sdk.data_controller.records.connection_controller_details_record import (
    ConnectionControllerDetailsRecord,
)
from dexa_sdk.jsonld.core import sign_agreement, verify_agreement
from marshmallow import EXCLUDE, fields, validate
from mydata_did.v1_0.utils.util import (
    bool_to_str,
    current_datetime_in_iso8601,
    str_to_bool,
)


class DataDisclosureAgreementInstanceRecord(BaseRecord):
    """Data disclosure agreement instance record to be persisted in the storage"""

    class Meta:
        # Schema class
        schema_class = "DataDisclosureAgreementInstanceRecordSchema"

    # Record type
    RECORD_TYPE = "data_disclosure_agreement_instance"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = None

    # Record tags
    TAG_NAMES = {
        "~instance_id",
        "~template_id",
        "~template_version",
        "~industry_sector",
        "~delete_flag",
        "~mydata_did",
        "~blink",
        "~connection_id",
        "~state",
    }

    # States of the data disclosure agreement instance.
    STATE_DEFINITION = "DEFINITION"
    STATE_PREPARATION = "PREPARATION"
    STATE_CAPTURE = "CAPTURE"
    STATE_PROOF = "PROOF"

    def __init__(
        self,
        *,
        id: str = None,
        instance_id: str = None,
        template_id: str = None,
        template_version: str = None,
        state: str = None,
        data_disclosure_agreement: dict = None,
        industry_sector: str = None,
        delete_flag: str = "false",
        connection_id: str = None,
        mydata_did: str = None,
        blink: str = None,
        blockchain_receipt: dict = None,
        customer_identification: dict = None,
        **kwargs,
    ):
        """Initialise data disclosure agreement instance record.

        Args:
            id (str, optional): Record ID. Defaults to None.
            instance_id (str, optional): Instance ID. Defaults to None.
            template_id (str, optional): Template ID. Defaults to None.
            template_version (str, optional): Template version. Defaults to None.
            state (str, optional): State of the record. Defaults to None.
            data_disclosure_agreement (dict, optional): DDA. Defaults to None.
            industry_sector (str, optional): Industry sector. Defaults to None.
            delete_flag (str, optional): Delete flag. Defaults to "false".
            connection_id (str, optional): Connection ID. Defaults to None.
            mydata_did (str, optional): MyData DID. Defaults to None.
            blink (str, optional): Blockchain Link. Defaults to None.
            blockchain_receipt (dict, optional): Blockchain Receipt. Defaults to None.
            customer_identification (dict, optional): Customer identification. Defauls to None.
        """

        # Pass identifier and state to parent class
        super().__init__(id, state, **kwargs)

        if not instance_id:
            raise TypeError("Instance identifier is not specified.")

        if not template_id:
            raise TypeError("Template identifier is not specified.")

        if not template_version:
            raise TypeError("Template version is not specified.")

        # Set the record attributes
        self.instance_id = instance_id
        self.template_id = template_id
        self.template_version = template_version
        self.state = state
        self.data_disclosure_agreement = data_disclosure_agreement
        self.industry_sector = industry_sector
        self.delete_flag = delete_flag
        self.connection_id = connection_id
        self.mydata_did = mydata_did
        self.blink = blink
        self.blockchain_receipt = blockchain_receipt
        self.customer_identification = customer_identification

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "instance_id",
                "template_id",
                "template_version",
                "state",
                "data_disclosure_agreement",
                "industry_sector",
                "delete_flag",
                "connection_id",
                "mydata_did",
                "blink",
                "blockchain_receipt",
                "customer_identification",
            )
        }

    @property
    def _delete_flag(self) -> bool:
        """Accessor for delete_flag."""
        return str_to_bool(self.delete_flag)

    @_delete_flag.setter
    def _delete_flag(self, value: bool) -> None:
        """Setter for delete_flag."""
        self.delete_flag = bool_to_str(value)

    @property
    def is_deleted(self) -> bool:
        """Check if data agreemnent is deleted."""
        return self._delete_flag

    @property
    def customer_identification_model(self) -> CustomerIdentificationModel:
        return CustomerIdentificationModel.deserialize(self.customer_identification)

    @staticmethod
    async def build_instance_from_template(
        context: InjectionContext, template_id: str, connection_record: ConnectionRecord
    ) -> typing.Tuple[
        "DataDisclosureAgreementInstanceRecord", DataDisclosureAgreementInstanceModel
    ]:
        """Build instance from DDA template.

        Args:
            context (InjectionContext): Injection context to be used.
            template_id (str): Template ID
            connection_record (ConnectionRecord): Connection record.

        Returns:
            DataDisclosureAgreementInstanceRecord: DDA instance record.
        """

        # Fetch latest template record.
        template_record = (
            await DataDisclosureAgreementTemplateRecord.latest_published_template_by_id(
                context, template_id
            )
        )

        assert template_record, "DDA template not found."

        # Sign the template.

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

        # DDA
        dda_template_dict = template_record.data_disclosure_agreement
        dda_template_model = template_record.dda_model

        # Add versions and ids
        instance_id = str(uuid.uuid4())
        instance_version = "1.0.0"
        template_id = dda_template_model.id
        template_version = dda_template_model.version
        dda_template_dict.update({"@id": instance_id})
        dda_template_dict.update({"version": instance_version})
        dda_template_dict.update({"templateId": template_id})
        dda_template_dict.update({"templateVersion": template_version})

        # Add DUS info.
        # Fetch controller details for the DUS connection
        tag_filter = {"connection_id": connection_record.connection_id}
        dus_connection_controller_details_record: ConnectionControllerDetailsRecord = (
            await ConnectionControllerDetailsRecord.retrieve_by_tag_filter(
                context, tag_filter
            )
        )
        data_controller_model = (
            dus_connection_controller_details_record.controller_details_model
        )
        dus_model = DataUsingServiceModel(
            did=data_controller_model.organisation_did,
            name=data_controller_model.organisation_name,
            url=data_controller_model.policy_url,
            legal_id=data_controller_model.organisation_did,
            industry_sector=data_controller_model.organisation_type,
            usage_purposes=dda_template_model.purpose,
            jurisdiction=dda_template_model.data_sharing_restrictions.jurisdiction,
            withdrawal=data_controller_model.policy_url,
            privacy_rights=data_controller_model.policy_url,
            signature_contact=data_controller_model.organisation_did,
        )
        dda_template_dict.update({"dataUsingService": dus_model.serialize()})

        # Sign the DDA
        signed_dda = await sign_agreement(
            agreement=dda_template_dict,
            verkey=controller_did.verkey,
            wallet=wallet,
            signature_options=signature_options,
        )

        dda_instance_model: DataDisclosureAgreementInstanceModel = (
            DataDisclosureAgreementInstanceModel.deserialize(signed_dda)
        )

        # Create and save DDA instance record.
        dda_instance_record = DataDisclosureAgreementInstanceRecord(
            instance_id=instance_id,
            template_id=template_id,
            template_version=template_version,
            state=DataDisclosureAgreementInstanceRecord.STATE_DEFINITION,
            data_disclosure_agreement=dda_instance_model.serialize(),
            industry_sector=template_record.industry_sector,
            connection_id=connection_record.connection_id,
        )

        await dda_instance_record.save(context)

        return (dda_instance_record, dda_instance_model)

    @classmethod
    async def build_instance_from_dda_offer(
        cls,
        context: InjectionContext,
        dda_offer_message: OfferDDAMessage,
        connection_record: ConnectionRecord,
    ) -> typing.Tuple[
        "DataDisclosureAgreementInstanceRecord", DataDisclosureAgreementInstanceModel
    ]:
        """Build instance from DDA offer.

        Args:
            dda_offer_message (OfferDDAMessage): DDA offer message.
            connection_record (ConnectionRecord): Connection record.

        Returns:
            DataDisclosureAgreementInstanceRecord: DDA instance record.
        """

        # Fetch wallet from context.
        wallet: IndyWallet = await context.inject(BaseWallet)

        # DUS public did
        dus_did = await wallet.get_public_did()

        customer_identification_details = dda_offer_message.body.customer_identification
        dda_offer = dda_offer_message.body.dda
        dda_offer_dict = dda_offer.serialize()

        # Verify the dda offer.
        valid = await verify_agreement(agreement=dda_offer_dict.copy(), wallet=wallet)

        assert valid, "DDA instance verification failed."

        # Signature options
        signature_options = {
            "id": f"did:sov:{dus_did.did}#1",
            "type": "Ed25519Signature2018",
            "created": current_datetime_in_iso8601(),
            "verificationMethod": f"{dus_did.verkey}",
            "proofPurpose": "authentication",
        }

        # Sign the DDA
        signed_dda = await sign_agreement(
            agreement=dda_offer_dict,
            verkey=dus_did.verkey,
            wallet=wallet,
            signature_options=signature_options,
        )

        dda_instance_model: DataDisclosureAgreementInstanceModel = (
            DataDisclosureAgreementInstanceModel.deserialize(signed_dda)
        )

        # Create and save DDA instance record.
        dda_instance_record = DataDisclosureAgreementInstanceRecord(
            instance_id=dda_instance_model.id,
            template_id=dda_instance_model.template_id,
            template_version=dda_instance_model.template_version,
            state=DataDisclosureAgreementInstanceRecord.STATE_CAPTURE,
            data_disclosure_agreement=dda_instance_model.serialize(),
            industry_sector=dda_instance_model.data_using_service.industry_sector,
            connection_id=connection_record.connection_id,
        )

        if customer_identification_details:
            dda_instance_record.customer_identification = (
                customer_identification_details.serialize()
            )

        await dda_instance_record.save(context)

        return (dda_instance_record, dda_instance_model)

    @classmethod
    async def update_instance_from_dda_accept(
        cls, context: InjectionContext, dda_accept_message: AcceptDDAMessage
    ) -> "DataDisclosureAgreementInstanceRecord":
        """Update instance from DDA accept.

        Args:
            context (InjectionContext): Injection context to be used.
            dda_accept_message (AcceptDDAMessage): DDA accept message.
            connection_record (ConnectionRecord): Connection record.

        Returns:
            DataDisclosureAgreementInstanceRecord: DDA instance record.
        """
        # Fetch wallet from context.
        wallet: IndyWallet = await context.inject(BaseWallet)

        dda_instance_model = dda_accept_message.body.dda
        dda_accept_dict = dda_instance_model.serialize()

        # Fetch instance record.
        tag_filter = {"instance_id": dda_instance_model.id}
        instance_record: DataDisclosureAgreementInstanceRecord = (
            await DataDisclosureAgreementInstanceRecord.retrieve_by_tag_filter(
                context, tag_filter
            )
        )

        # Verify the dda accept.
        valid = await verify_agreement(agreement=dda_accept_dict.copy(), wallet=wallet)

        assert valid, "DDA instance verification failed."

        instance_record.data_disclosure_agreement = dda_accept_dict
        instance_record.state = DataDisclosureAgreementInstanceRecord.STATE_CAPTURE
        await instance_record.save(context)

        return instance_record

    async def fetch_controller_details(
        self, context: InjectionContext
    ) -> ConnectionControllerDetailsRecord:
        """Fetch controller details.

        Args:
            context (InjectionContext): Injection context to be used.

        Returns:
            ConnectionControllerDetailsRecord: Connection controller details record.
        """

        tag_filter = {"connection_id": self.connection_id}
        dus_connection_controller_details_record: ConnectionControllerDetailsRecord = (
            await ConnectionControllerDetailsRecord.retrieve_by_tag_filter(
                context, tag_filter
            )
        )

        return dus_connection_controller_details_record


class DataDisclosureAgreementInstanceRecordSchema(BaseRecordSchema):
    """Data agreement instance record schema"""

    class Meta:
        # Model class
        model_class = DataDisclosureAgreementInstanceRecord

        # Unknown fields are excluded
        unknown = EXCLUDE

    # DDA instance identifier
    instance_id = fields.Str(required=True)

    # Data disclosure agreement template identifier
    template_id = fields.Str(required=True, example=UUIDFour.EXAMPLE)

    # Data disclosure agreement template version
    template_version = fields.Str(required=False)

    # State of the data agreement.
    state = fields.Str(
        required=True,
        example=DataDisclosureAgreementInstanceRecord.STATE_PREPARATION,
        validate=validate.OneOf(
            [
                DataDisclosureAgreementInstanceRecord.STATE_DEFINITION,
                DataDisclosureAgreementInstanceRecord.STATE_PREPARATION,
            ]
        ),
    )

    # Data disclosure agreement
    data_disclosure_agreement = fields.Dict(required=True)

    # Industry sector
    industry_sector = fields.Str(required=False)

    # Is deleted or not
    delete_flag = fields.Str(
        required=True,
        example="false",
        validate=validate.OneOf(
            [
                "true",
                "false",
            ]
        ),
    )

    # Connection identifier
    connection_id = fields.Str(required=False)

    # did:mydata identifier
    mydata_did = fields.Str(required=False)

    # Blockchain link
    blink = fields.Str(required=False)

    # Blockchain receipt
    blockchain_receipt = fields.Dict(required=False)
