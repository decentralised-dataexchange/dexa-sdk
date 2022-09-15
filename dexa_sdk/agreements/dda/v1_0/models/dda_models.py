import typing

from aries_cloudagent.messaging.models.base import BaseModel, BaseModelSchema
from dexa_sdk.agreements.dda.v1_0.models.fields.context_field import ContextField
from marshmallow import EXCLUDE, fields

DDA_DEFAULT_CONTEXT = [
    (
        "https://raw.githubusercontent.com/decentralised-dataexchange/data-exchange-agreements"
        "/main/interface-specs/jsonld/contexts/dexa-context.jsonld"
    ),
    "https://w3id.org/security/v2",
]

DDA_TYPE = ["DataDisclosureAgreement"]


class DataControllerModel(BaseModel):
    """Data controller model class"""

    class Meta:
        """Meta data"""

        # Schema class
        schema_class = "DataControllerSchema"

    def __init__(
        self,
        *,
        did: str = None,
        name: str = None,
        legal_id: str = None,
        url: str = None,
        industry_sector: str = None,
        **kwargs
    ):
        # Call the parent constructor
        super().__init__(**kwargs)

        # Set model attributes
        self.did = did
        self.name = name
        self.legal_id = legal_id
        self.url = url
        self.industry_sector = industry_sector


class DataControllerSchema(BaseModelSchema):
    """Data controller schema class"""

    class Meta:
        # Model class
        model_class = DataControllerModel

        # Unknown fields are excluded
        unknown = EXCLUDE

    # This is the DID of the data source preparing the agreement
    did = fields.Str(data_key="did", required=False)

    # The name of the data source exposing the data
    name = fields.Str(data_key="name", required=True)

    # This is the legal ID to the data source.
    # E.g. Swedish Organisation Number
    legal_id = fields.Str(data_key="legalId", required=False)

    # This is the data source organisation URL
    url = fields.Str(data_key="url", required=False)

    # Industry sector that the DS belongs to
    industry_sector = fields.Str(data_key="industrySector", required=True)


class DataSharingRestrictionsModel(BaseModel):
    """Data sharing restrictions model"""

    class Meta:
        # Schema class
        schema_class = "DataSharingRestrictionsSchema"

    def __init__(
        self,
        *,
        policy_url: str,
        jurisdiction: str,
        industry_sector: str,
        data_retention_period: int,
        geographic_restriction: str,
        storage_location: str,
        **kwargs
    ):
        # Call the parent constructor
        super().__init__(**kwargs)

        # Set model attributes
        self.policy_url = policy_url
        self.jurisdiction = jurisdiction
        self.industry_sector = industry_sector
        self.data_retention_period = data_retention_period
        self.geographic_restriction = geographic_restriction
        self.storage_location = storage_location


class DataSharingRestrictionsSchema(BaseModelSchema):
    """Data sharing restrictions schema"""

    class Meta:
        # Model class
        model_class = DataSharingRestrictionsModel

        # Unknown fields are excluded
        unknown = EXCLUDE

    # URL to the privacy policy document of the data source organisation
    policy_url = fields.Str(data_key="policyUrl", required=True)

    # The jurisdiction associated with the data source exposing
    # the personal data that the privacy regulation is followed.
    # These can be country, economic union, law, location or region.
    # [value based on W3C Location and Jurisdiction]
    jurisdiction = fields.Str(data_key="jurisdiction", required=True)

    # The sector to which the data source restricts the use of data
    # by any data using services. If no restriction, leave blank
    industry_sector = fields.Str(data_key="industrySector", required=True)

    # The amount of time that the data source holds onto
    # any personal data, in seconds.
    data_retention_period = fields.Int(data_key="dataRetentionPeriod", required=True)

    # The country or economic union is restricted from
    # processing personal data.[value based on W3C
    # Location and Jurisdiction] for the data source
    geographic_restriction = fields.Str(data_key="geographicRestriction", required=True)

    # The geographic location where the personal
    # data is stored by the data source
    storage_location = fields.Str(data_key="storageLocation", required=True)


class PersonalDataModel(BaseModel):
    """Personal data model class"""

    class Meta:
        schema_class = "PersonalDataSchema"

    def __init__(
        self,
        *,
        attribute_id: str = None,
        attribute_name: str = None,
        attribute_description: str = None,
        attribute_sensitive: str = None,
        attribute_category: str = None,
        **kwargs
    ):
        # Call the parent constructor
        super().__init__(**kwargs)

        # Set the model attributes
        self.attribute_id = attribute_id
        self.attribute_name = attribute_name
        self.attribute_sensitive = attribute_sensitive
        self.attribute_category = attribute_category
        self.attribute_description = attribute_description


class PersonalDataSchema(BaseModelSchema):
    """Personal data schema"""

    class Meta:
        # Model class
        model_class = PersonalDataModel

        # Exclude unknown fields
        unknown = EXCLUDE

    # Identifier of the attribute
    attribute_id = fields.Str(data_key="attributeId", required=False)

    # Name of the attributes that is being shared
    attribute_name = fields.Str(data_key="attributeName", required=True)

    # Defines the sensitivity of the data as per PII
    attribute_sensitive = fields.Str(data_key="attributeSensitive", required=False)

    # An explicit list of personal data categories to be shared.
    # The categories shall be defined using language meaningful to
    # the users and consistent with the purposes of the processing.
    # [values based on W3C DPV-DP]
    attribute_category = fields.Str(data_key="attributeCategory", required=False)

    # Attribute description.
    attribute_description = fields.Str(data_key="attributeDescription", required=True)


class DataDisclosureAgreementModel(BaseModel):
    """Data disclosure agreement model"""

    class Meta:
        # Schema class
        schema_class = "DataDisclosureAgreementSchema"

    def __init__(
        self,
        *,
        context: typing.Union[str, typing.List[str]] = DDA_DEFAULT_CONTEXT,
        id: str,
        type: typing.List[str] = DDA_TYPE,
        language: str,
        version: str,
        data_controller: DataControllerModel,
        agreement_period: int,
        data_sharing_restrictions: DataSharingRestrictionsModel,
        purpose: str,
        purpose_description: str,
        lawful_basis: str,
        personal_data: typing.List[PersonalDataModel],
        code_of_conduct: str,
        **kwargs
    ):
        # Call the parent constructor
        super().__init__(**kwargs)

        # Set model attributes
        self.context = context
        self.id = id
        self.type = type
        self.version = version
        self.language = language
        self.data_controller = data_controller
        self.agreement_period = agreement_period
        self.data_sharing_restrictions = data_sharing_restrictions
        self.purpose = purpose
        self.purpose_description = purpose_description
        self.lawful_basis = lawful_basis
        self.personal_data = personal_data
        self.code_of_conduct = code_of_conduct


class DataDisclosureAgreementSchema(BaseModelSchema):
    """Data disclosure agreement schema"""

    class Meta:
        # Model class
        model_class = DataDisclosureAgreementModel

        # Exclude unknown fields
        unknown = EXCLUDE

    # Defines the context of this document. E.g. the link the JSON-LD
    context = ContextField(
        data_key="@context", required=True, example=DDA_DEFAULT_CONTEXT
    )

    # Data disclosure agreement template identifier
    id = fields.Str(data_key="@id", required=True)

    # Type of the agreement
    type = fields.List(fields.Str, data_key="@type", required=True, example=DDA_TYPE)

    # Data disclosure agreement version
    version = fields.Str(data_key="version", required=True)

    # language used. If not present default language is English
    language = fields.Str(data_key="language", required=True)

    # Encapsulates the data controller data
    data_controller = fields.Nested(
        DataControllerSchema, data_key="dataController", required=True
    )

    # Duration of the agreement after which the
    # data disclosure agreement expires
    agreement_period = fields.Int(data_key="agreementPeriod", required=True)

    # Used by the DS to configure any data sharing restrictions
    # towards the DUS. This could reuse the
    # data agreement policy parameters as is.
    data_sharing_restrictions = fields.Nested(
        DataSharingRestrictionsSchema, data_key="dataSharingRestrictions", required=True
    )

    # Describes the purpose for which the data source shares
    # personal data as described in the
    # data agreement [values based on W3C DPV Purposes]
    purpose = fields.Str(data_key="purpose", required=True)

    # Additional description of the purpose
    # for which the data source shares personal data
    purpose_description = fields.Str(data_key="purposeDescription", required=True)

    # Indicate the lawful basis for sharing personal data.
    # These can be consent, legal obligation, contract, vital interest,
    # public task or legitimate_interest. [values based on W3C DPV legal basis]
    lawful_basis = fields.Str(data_key="lawfulBasis", required=True)

    # Encapsulates the attributes shared by the data source
    personal_data = fields.List(
        fields.Nested(PersonalDataSchema), data_key="personalData", required=True
    )

    # The code of conduct is followed by the data source.
    # This provides the proper application of privacy regulation
    # taking into account specific features within a sector.
    # The code of conduct shall reference the name of the code of conduct
    # and with a publicly accessible reference.
    code_of_conduct = fields.Str(data_key="codeOfConduct", required=True)
