import typing
import uuid

from aries_cloudagent.messaging.models.base import BaseModel, BaseModelSchema
from dexa_sdk.agreements.da.v1_0.models.da_models import (
    DA_DEFAULT_CONTEXT,
    DA_TYPE,
    DataAgreementDataPolicyModel,
    DataAgreementDataPolicySchema,
    DataAgreementDPIAModel,
    DataAgreementDPIASchema,
    DataAgreementPersonalDataModel,
    DataAgreementPersonalDataSchema,
)
from dexa_sdk.agreements.dda.v1_0.models.fields.context_field import ContextField
from marshmallow import EXCLUDE, fields, validate


class DataAgreementProofModel(BaseModel):
    """
    Data agreement proof model class
    """

    class Meta:
        # Schema class
        schema_class = "DataAgreementProofSchema"

        # Unknown fields are excluded
        unknown = EXCLUDE

    def __init__(
        self,
        *,
        proof_id: str = None,
        proof_type: str = None,
        created: str = None,
        verification_method: str = None,
        proof_purpose: str = None,
        proof_value: str = None,
        **kwargs,
    ):
        # Call parent constructor
        super().__init__(**kwargs)

        # Set attributes
        self.proof_id = proof_id
        self.proof_type = proof_type
        self.created = created
        self.verification_method = verification_method
        self.proof_purpose = proof_purpose
        self.proof_value = proof_value


class DataAgreementProofSchema(BaseModelSchema):
    """
    Data agreement proof schema class
    """

    class Meta:
        # Model class
        model_class = DataAgreementProofModel

        # Unknown fields are excluded
        unknown = EXCLUDE

    # Proof identifier
    proof_id = fields.Str(data_key="id", required=True)

    # Proof type
    proof_type = fields.Str(data_key="type", required=True)

    # Created
    created = fields.Str(data_key="created", required=True)

    # Verification method
    verification_method = fields.Str(data_key="verificationMethod", required=True)

    # Proof purpose
    proof_purpose = fields.Str(data_key="proofPurpose", required=True)

    # Proof value
    proof_value = fields.Str(data_key="proofValue", required=True)


class DataAgreementInstanceModel(BaseModel):
    """Data agreement instance model"""

    class Meta:
        # Schema class
        schema_class = "DataAgreementInstanceSchema"

    def __init__(
        self,
        *,
        context: typing.Union[str, typing.List[str]] = DA_DEFAULT_CONTEXT,
        id: str = str(uuid.uuid4()),
        type: typing.List[str] = DA_TYPE,
        version: str,
        template_id: str,
        template_version: str,
        language: str = "en",
        data_controller_name: str = None,
        data_controller_url: str = None,
        data_policy: DataAgreementDataPolicyModel = None,
        purpose: str = None,
        purpose_description: str = None,
        lawful_basis: str = None,
        method_of_use: str = None,
        personal_data: typing.List[DataAgreementPersonalDataModel] = None,
        dpia: DataAgreementDPIAModel = None,
        proof_chain: typing.List[DataAgreementProofModel] = None,
        proof: DataAgreementProofModel = None,
        data_subject_did: str = None,
        **kwargs,
    ):
        """
        Initialize data agreement instance model
        """

        # Call parent constructor
        super().__init__(**kwargs)

        # Set attributes
        self.context = context
        self.id = id
        self.type = type
        self.version = version
        self.template_id = template_id
        self.template_version = template_version
        self.language = language
        self.data_controller_name = data_controller_name
        self.data_controller_url = data_controller_url
        self.data_policy = data_policy
        self.purpose = purpose
        self.purpose_description = purpose_description
        self.lawful_basis = lawful_basis
        self.method_of_use = method_of_use
        self.personal_data = personal_data
        self.dpia = dpia
        self.proof_chain = proof_chain
        self.proof = proof
        self.data_subject_did = data_subject_did


class DataAgreementInstanceSchema(BaseModelSchema):
    """Data agreement instance schema"""

    class Meta:
        # Model class
        model_class = DataAgreementInstanceModel

        # Unknown fields are excluded
        unknown = EXCLUDE

    # Defines the context of this document. E.g. the link the JSON-LD
    context = ContextField(
        data_key="@context",
        required=True,
        example=DA_DEFAULT_CONTEXT,
        default=DA_DEFAULT_CONTEXT,
    )

    # Data agreement instance identifier
    id = fields.Str(data_key="@id", required=True, default=str(uuid.uuid4()))

    # Type of the agreement
    type = fields.List(
        fields.Str, data_key="@type", required=True, example=DA_TYPE, default=DA_TYPE
    )

    # Data agreement instance version
    version = fields.Str(data_key="version", required=True)

    # Data agreement template identifier
    template_id = fields.Str(data_key="templateId", required=True)

    # Data agreement template version
    template_version = fields.Str(data_key="templateVersion", required=True)

    # language used. If not present default language is English
    language = fields.Str(data_key="language", default="en")

    # Data agreement data controller name
    # i.e. Organization name of the data controller
    data_controller_name = fields.Str(
        data_key="dataControllerName",
        example="Happy Shopping AB",
        required=True,
    )

    # Data agreement data controller URL
    data_controller_url = fields.Str(
        data_key="dataControllerUrl",
        example="https://www.happyshopping.com",
    )

    # Data agreement data policy
    data_policy = fields.Nested(
        DataAgreementDataPolicySchema, required=True, data_key="dataPolicy"
    )

    # Data agreement usage purpose
    purpose = fields.Str(
        data_key="purpose",
        example="Customized shopping experience",
        required=True,
    )

    # Data agreement usage purpose description
    purpose_description = fields.Str(
        data_key="purposeDescription",
        example="Collecting user data for offering custom tailored shopping experience",
        required=True,
    )

    # Data agreement legal basis
    lawful_basis = fields.Str(
        data_key="lawfulBasis",
        example="consent",
        description="Legal basis of processing",
        required=True,
        validate=validate.OneOf(
            [
                "consent",
                "legal_obligation",
                "contract",
                "vital_interest",
                "public_task",
                "legitimate_interest",
            ]
        ),
    )

    # Data agreement method of use (i.e. how the data is used)
    # 2 method of use: "data-source" and "data-using-service"
    method_of_use = fields.Str(
        data_key="methodOfUse",
        example="data-using-service",
        description="Method of use (or data exchange mode)",
        required=True,
        validate=validate.OneOf(
            [
                "data-source",
                "data-using-service",
            ]
        ),
    )

    # Data agreement personal data (attributes)
    personal_data = fields.List(
        fields.Nested(DataAgreementPersonalDataSchema),
        required=True,
        validate=validate.Length(min=1),
        data_key="personalData",
    )

    # Data agreement DPIA metadata
    dpia = fields.Nested(DataAgreementDPIASchema, required=False, data_key="dpia")

    # Data subject did:sov identifier
    data_subject_did = fields.Str(data_key="dataSubjectDid", required=False)

    # Proof chain
    proof_chain = fields.List(
        fields.Nested(DataAgreementProofSchema), data_key="proofChain", required=False
    )

    # Data agreement proof
    proof = fields.Nested(DataAgreementProofSchema, required=False)
