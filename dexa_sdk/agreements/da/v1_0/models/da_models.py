import typing
import uuid
from typing import List

from aries_cloudagent.messaging.models.base import BaseModel, BaseModelSchema
from aries_cloudagent.messaging.valid import UUIDFour
from dexa_sdk.agreements.dda.v1_0.models.fields.context_field import ContextField
from marshmallow import EXCLUDE, fields, validate

DA_DEFAULT_CONTEXT = [
    (
        "https://raw.githubusercontent.com/decentralised-dataexchange/data-exchange-agreements"
        "/main/interface-specs/jsonld/contexts/dexa-context.jsonld"
    ),
    "https://w3id.org/security/v2",
]

DA_TYPE = ["DataAgreement"]


class DataAgreementDataPolicyModel(BaseModel):
    """
    Data policy model class
    """

    class Meta:
        # Schema class
        schema_class = "DataAgreementDataPolicySchema"

    def __init__(
        self,
        *,
        data_retention_period: int,
        policy_url: str,
        jurisdiction: str,
        industry_sector: str,
        geographic_restriction: str,
        storage_location: str,
        third_party_data_sharing: bool,
        **kwargs,
    ):
        """
        Initialize data policy model
        """

        # Call parent constructor
        super().__init__(**kwargs)

        # Set attributes
        self.policy_url = policy_url
        self.jurisdiction = jurisdiction
        self.industry_sector = industry_sector
        self.data_retention_period = data_retention_period
        self.geographic_restriction = geographic_restriction
        self.storage_location = storage_location
        self.third_party_data_sharing = third_party_data_sharing


class DataAgreementDataPolicySchema(BaseModelSchema):
    """
    Data policy schema class
    """

    class Meta:
        # Model class
        model_class = DataAgreementDataPolicyModel

        # Unknown fields are excluded
        unknown = EXCLUDE

    # Policy URL
    policy_url = fields.Str(
        data_key="policyUrl",
        example="https://clarifyhealth.com/privacy-policy/",
        required=True,
    )

    # Jurisdiction
    jurisdiction = fields.Str(
        data_key="jurisdiction",
        example="Sweden",
        required=True,
    )

    # Industry sector
    industry_sector = fields.Str(
        data_key="industrySector",
        example="Healthcare",
        required=False,
    )

    # Data retention period
    data_retention_period = fields.Int(
        data_key="dataRetentionPeriod",
        example=365,
        description="Data retention period in days",
        required=True,
    )

    # Geographic restriction
    geographic_restriction = fields.Str(
        data_key="geographicRestriction",
        example="Europe",
        required=True,
    )

    # Storage location
    storage_location = fields.Str(
        data_key="storageLocation",
        example="Europe",
        required=True,
    )

    third_party_data_sharing = fields.Bool(
        data_key="thirdPartyDataSharing",
        example=False,
        description="Third party data sharing",
        required=True,
    )


class DataAgreementDPIAModel(BaseModel):
    """
    DPIA model class
    """

    class Meta:
        # Schema class
        schema_class = "DataAgreementDPIASchema"

    def __init__(self, *, dpia_date: str, dpia_summary_url: str, **kwargs):
        """
        Initialize DPIA model
        """
        # Call parent constructor
        super().__init__(**kwargs)

        # Set attributes
        self.dpia_date = dpia_date
        self.dpia_summary_url = dpia_summary_url


class DataAgreementDPIASchema(BaseModelSchema):
    """
    DPIA schema class
    """

    class Meta:
        # Model class
        model_class = DataAgreementDPIAModel

        # Unknown fields are excluded
        unknown = EXCLUDE

    # DPIA date
    dpia_date = fields.Str(
        data_key="dpiaDate",
        example="2011-10-05T14:48:00.000Z",
        required=False,
    )

    # DPIA summary URL
    dpia_summary_url = fields.Str(
        data_key="dpiaSummaryUrl",
        example="https://org.com/dpia_results.html",
        required=False,
    )


class DataAgreementPersonalDataRestrictionModel(BaseModel):
    """
    Personal data restriction model class
    """

    class Meta:
        # Schema class
        schema_class = "DataAgreementPersonalDataRestrictionSchema"

    def __init__(self, *, schema_id: str = None, cred_def_id: str = None, **kwargs):
        """
        Initialise personal data restriction model.
        """

        # Call parent constructor
        super().__init__(**kwargs)

        # Set attributes
        self.schema_id = schema_id
        self.cred_def_id = cred_def_id


class DataAgreementPersonalDataRestrictionSchema(BaseModelSchema):
    """
    Personal data restriction schema class
    """

    class Meta:
        # Model class
        model_class = DataAgreementPersonalDataRestrictionModel

    schema_id = fields.Str(
        description="Schema identifier",
        data_key="schemaId",
        example="WgWxqztrNooG92RXvxSTWv:2:schema_name:1.0",
        required=False,
    )

    cred_def_id = fields.Str(
        description="Credential definition identifier",
        data_key="credDefId",
        example="WgWxqztrNooG92RXvxSTWv:3:CL:20:tag",
        required=False,
    )


class DataAgreementPersonalDataModel(BaseModel):
    """
    Personal data model class
    """

    class Meta:
        # Schema class
        schema_class = "DataAgreementPersonalDataSchema"

    def __init__(
        self,
        *,
        attribute_id: str = None,
        attribute_name: str = None,
        attribute_sensitive: bool = True,
        attribute_category: str = None,
        attribute_description: str = None,
        restrictions: List[DataAgreementPersonalDataRestrictionModel] = None,
        **kwargs,
    ):
        """
        Initialize personal data model
        """

        # Call parent constructor
        super().__init__(**kwargs)

        # Set attributes
        self.attribute_id = attribute_id
        self.attribute_name = attribute_name
        self.attribute_sensitive = attribute_sensitive
        self.attribute_category = attribute_category
        self.attribute_description = attribute_description
        self.restrictions = restrictions


class DataAgreementPersonalDataSchema(BaseModelSchema):
    """
    Personal data schema class
    """

    class Meta:
        # Model class
        model_class = DataAgreementPersonalDataModel

    # Attribute identifier
    attribute_id = fields.Str(
        data_key="attributeId", example=UUIDFour.EXAMPLE, required=False
    )

    # Attribute name
    attribute_name = fields.Str(example="Name", data_key="attributeName", required=True)

    # Attribute sensitive
    attribute_sensitive = fields.Bool(
        example=True, data_key="attributeSensitive", required=False
    )

    # Attribute category
    attribute_category = fields.Str(
        example="Personal", required=False, data_key="attributeCategory"
    )

    # Attribute description
    attribute_description = fields.Str(
        required=True, example="Name of the customer", data_key="attributeDescription"
    )

    restrictions = fields.List(
        fields.Nested(DataAgreementPersonalDataRestrictionSchema),
        required=False,
        data_key="restrictions",
    )


class DataAgreementModel(BaseModel):
    """
    Data agreement model class
    """

    class Meta:
        # Schema class
        schema_class = "DataAgreementSchema"

    def __init__(
        self,
        *,
        context: typing.Union[str, typing.List[str]] = DA_DEFAULT_CONTEXT,
        id: str = str(uuid.uuid4()),
        type: typing.List[str] = DA_TYPE,
        version: str,
        language: str = "en",
        data_controller_name: str = None,
        data_controller_url: str = None,
        data_policy: DataAgreementDataPolicyModel = None,
        purpose: str = None,
        purpose_description: str = None,
        lawful_basis: str = None,
        method_of_use: str = None,
        personal_data: List[DataAgreementPersonalDataModel] = None,
        dpia: DataAgreementDPIAModel = None,
        **kwargs,
    ):
        """
        Initialize data agreement model
        """

        # Call parent constructor
        super().__init__(**kwargs)

        # Set attributes
        self.context = context
        self.id = id
        self.type = type
        self.version = version
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


class DataAgreementSchema(BaseModelSchema):
    """
    Data agreement schema class
    """

    class Meta:
        # Model class
        model_class = DataAgreementModel

        # Unknown fields are excluded
        unknown = EXCLUDE

    # Defines the context of this document. E.g. the link the JSON-LD
    context = ContextField(
        data_key="@context",
        required=True,
        example=DA_DEFAULT_CONTEXT,
        default=DA_DEFAULT_CONTEXT,
    )

    # Data agreement template identifier
    # i.e. identifier of the "prepared" data agreement template
    id = fields.Str(data_key="@id", required=True, default=str(uuid.uuid4()))

    # Type of the agreement
    type = fields.List(
        fields.Str, data_key="@type", required=True, example=DA_TYPE, default=DA_TYPE
    )

    # Data agreement template version
    # i.e. version of the "prepared" data agreement template
    version = fields.Str(data_key="version", required=True)

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
