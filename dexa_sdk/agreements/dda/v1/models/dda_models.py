import typing
from marshmallow import fields, EXCLUDE
from aries_cloudagent.messaging.models.base import BaseModel, BaseModelSchema
from .fields.context_field import ContextField


class DataControllerModel(BaseModel):
    """Data controller model class"""

    class Meta:
        """Meta data"""

        # Schema class
        schema_class = "DataControllerSchema"

    def __init__(
        self,
        *,
        did: str,
        name: str,
        legal_id: str,
        url: str,
        industry_sector: str,
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
        model_class = "DataControllerModel"

        # Unknown fields are excluded
        unknown = EXCLUDE

    # This is the DID of the data source preparing the agreement
    did = fields.Str(data_key="did", required=True)

    # The name of the data source exposing the data
    name = fields.Str(data_key="name", required=True)

    # This is the legal ID to the data source.
    # E.g. Swedish Organisation Number
    legal_id = fields.Str(data_key="legalId", required=True)

    # This is the data source organisation URL
    url = fields.Str(data_key="url", required=True)

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
        model_class = "DataSharingRestrictionsModel"

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
    data_retention_period = fields.Str(data_key="dataRetentionPeriod", required=True)

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
        attribute_id: str,
        attribute_name: str,
        attribute_sensitive: str = "true",
        attribute_category: str = "personalData",
        **kwargs
    ):
        # Call the parent constructor
        super().__init__(**kwargs)

        # Set the model attributes
        self.attribute_id = attribute_id
        self.attribute_name = attribute_name
        self.attribute_sensitive = attribute_sensitive
        self.attribute_category = attribute_category


class PersonalDataSchema(BaseModelSchema):
    """Personal data schema"""

    class Meta:
        # Model class
        model_class = "PersonalDataModel"

        # Exclude unknown fields
        unknown = EXCLUDE

    # Identifier of the attribute
    attribute_id = fields.Str(data_key="attributeId")

    # Name of the attributes that is being shared
    attribute_name = fields.Str(data_key="attributeName")

    # Defines the sensitivity of the data as per PII
    attribute_sensitive = fields.Str(data_key="attributeSensitive")

    # An explicit list of personal data categories to be shared.
    # The categories shall be defined using language meaningful to
    # the users and consistent with the purposes of the processing.
    # [values based on W3C DPV-DP]
    attribute_category = fields.Str(data_key="attributeCategory")


class DataUsingServiceModel(BaseModel):
    """Data using service model"""

    class Meta:
        # Schema class
        schema_class = "DataUsingServiceSchema"

    def __init__(
        self,
        *,
        did: str,
        name: str,
        legal_id: str,
        url: str,
        industry_sector: str,
        usage_purposes: str,
        jurisdiction: str,
        withdrawal: str,
        privacy_rights: str,
        signature_contact: str,
        **kwargs
    ):
        # Call the parent constructor
        super().__init__(**kwargs)

        # Set the model attributes
        self.did = did
        self.name = name
        self.legal_id = legal_id
        self.url = url
        self.industry_sector = industry_sector
        self.usage_purposes = usage_purposes
        self.jurisdiction = jurisdiction
        self.withdrawal = withdrawal
        self.privacy_rights = privacy_rights
        self.signature_contact = signature_contact


class DataUsingServiceSchema(BaseModelSchema):
    """Data using service schema"""

    class Meta:
        # Model class
        model_class = "DataUsingServiceModel"

        # Exclude unknown fields
        unknown = EXCLUDE

    did = fields.Str(data_key="did", required=True)
    name = fields.Str(data_key="name", required=True)
    legal_id = fields.Str(data_key="legalId", required=True)
    url = fields.Str(data_key="url", required=True)
    industry_sector = fields.Str(data_key="industrySector", required=True)
    usage_purposes = fields.Str(data_key="usagePurposes", required=True)
    jurisdiction = fields.Str(data_key="jurisdiction", required=True)
    withdrawal = fields.Str(data_key="withdrawal", required=True)
    privacy_rights = fields.Str(data_key="privacyRights", required=True)
    signature_contact = fields.Str(data_key="signatureContact", required=True)


class ProofModel(BaseModel):
    """Proof model"""

    class Meta:
        # Schema class
        schema_class = "ProofSchema"

    def __init__(
        self,
        *,
        id: str,
        type: str,
        created: str,
        verification_method: str,
        proof_purpose: str,
        proof_value: str,
        **kwargs
    ):
        # Call the parent constructor
        super().__init__(**kwargs)

        # Set the model attributes
        self.id = id
        self.type = type
        self.created = created
        self.verification_method = verification_method
        self.proof_purpose = proof_purpose
        self.proof_value = proof_value


class ProofSchema(BaseModelSchema):
    """Proof schema"""

    class Meta:
        # Model class
        model_class = "ProofModel"

        # Exclude unknown fields
        unknown = EXCLUDE

    # Proof identifier
    id = fields.Str(data_key="id", required=True)

    # Signature schema type (For e.g. ed25519, es256 e.t.c.)
    type = fields.Str(data_key="type", required=True)

    # Proof creation time (ISO 8601 UTC)
    created = fields.Str(data_key="created", required=True)

    # Should match the data_using_service did
    verification_method = fields.Str(data_key="verificationMethod", required=True)

    # Contract agreement (Type inferred from JSON-LD spec)
    proof_purpose = fields.Str(data_key="proofPurpose", required=True)

    # Proof value
    proof_value = fields.Str(data_key="proofValue", required=True)


class DataDisclosureAgreementModel(BaseModel):
    """Data disclosure agreement model"""

    class Meta:
        # Schema class
        schema_class = "DataDisclosureAgreementSchema"

    def __init__(
        self,
        *,
        context: typing.Union[str, typing.List[str]],
        id: str,
        type: typing.List[str],
        language: str,
        version: str,
        template_id: str = None,
        template_version: str = None,
        data_controller: DataControllerModel,
        agreement_period: int,
        data_sharing_restrictions: DataSharingRestrictionsModel,
        purpose: str,
        purpose_description: str,
        lawful_basis: str,
        personal_data: typing.List[PersonalDataModel],
        code_of_conduct: str,
        data_using_service: DataUsingServiceModel,
        proof: ProofModel = None,
        proof_chain: typing.List[ProofModel] = None,
        **kwargs
    ):
        # Call the parent constructor
        super().__init__(**kwargs)

        # Set model attributes
        self.context = context
        self.id = id
        self.type = type
        self.version = version
        self.template_id = template_id
        self.template_version = template_version
        self.language = language
        self.data_controller = data_controller
        self.agreement_period = agreement_period
        self.data_sharing_restrictions = data_sharing_restrictions
        self.purpose = purpose
        self.purpose_description = purpose_description
        self.lawful_basis = lawful_basis
        self.personal_data = personal_data
        self.code_of_conduct = code_of_conduct
        self.data_using_service = data_using_service
        self.proof = proof
        self.proof_chain = proof_chain


class DataDisclosureAgreementSchema(BaseModelSchema):
    """Data disclosure agreement schema"""

    class Meta:
        # Model class
        model_class = "DataDisclosureAgreementModel"

        # Exclude unknown fields
        unknown = EXCLUDE

    # Defines the context of this document. E.g. the link the JSON-LD
    context = ContextField(data_key="@context", required=True)

    # Identifier to the data disclosure agreement instance
    # addressed to a specific DUS
    id = fields.Str(data_key="@id", required=True)

    # Type of the agreement
    type = fields.List(fields.Str, data_key="@type", required=True)

    # Version number of the data disclosure agreement
    version = fields.Str(data_key="version", required=True)

    # Identifier to the template of the data disclosure agreement
    template_id = fields.Str(data_key="templateId", required=False)

    # Version number of the data disclosure agreement template
    template_version = fields.Str(data_key="templateVersion", required=False)

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
    purpose_description = fields.Str(data_key="purpose_description", required=True)

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

    # The data using services that have signed up for consuming data.
    # This get populated after the data disclosure agreement
    # is proposed by the data using service
    data_using_service = fields.Nested(
        DataUsingServiceSchema, data_key="dataUsingService", required=True
    )

    # Encapsulates the event signatures that allows anyone (e.g. an auditor)
    # to verify the authencity and source of the data disclosure agreement.
    # Its uses linked data proofs as per W3C and contains a set of attributes
    # that represent a Linked Data digital proof
    # and the parameters required to verify it.
    proof = fields.Nested(ProofSchema, data_key="proof", required=False)

    proof_chain = fields.List(
        fields.Nested(ProofSchema), data_key="proofChain", required=False
    )
