import typing
from pydantic import Field, BaseModel
from .base import DataDisclosureAgreementBaseModel


class DataControllerModel(DataDisclosureAgreementBaseModel):
    # This is the DID of the data source preparing the agreement
    did: str

    # The name of the data source exposing the data
    name: str

    # This is the legal ID to the data source.
    # E.g. Swedish Organisation Number
    legal_id: str = Field(alias="legalId")

    # This is the data source organisation URL
    url: str

    # Industry sector that the DS belongs to
    industry_sector: str = Field(alias="industrySector")


class DataSharingRestrictionsModel(DataDisclosureAgreementBaseModel):

    # URL to the privacy policy document of the data source organisation
    policy_url: str = Field(alias="policyUrl")

    # The jurisdiction associated with the data source exposing
    # the personal data that the privacy regulation is followed.
    # These can be country, economic union, law, location or region.
    # [value based on W3C Location and Jurisdiction]
    jurisdiction: str

    # The sector to which the data source restricts the use of data
    # by any data using services. If no restriction, leave blank
    industry_sector: str = Field(alias="industrySector")

    # The amount of time that the data source holds onto
    # any personal data, in seconds.
    data_retention_period: int = Field(alias="dataRetentionPeriod")

    # The country or economic union is restricted from
    # processing personal data.[value based on W3C
    # Location and Jurisdiction] for the data source
    geographic_restriction: str = Field(alias="geographicRestriction")

    # The geographic location where the personal
    # data is stored by the data source
    storage_location: str = Field(alias="storageLocation")


class PersonalDataModel(DataDisclosureAgreementBaseModel):

    # Identifier of the attribute
    attribute_id: str = Field(alias="attributeId")

    # Name of the attributes that is being shared
    attribute_name: str = Field(alias="attributeName")

    # Defines the sensitivity of the data as per PII
    attribute_sensitive: str = Field(alias="attributeSensitive")

    # An explicit list of personal data categories to be shared.
    # The categories shall be defined using language meaningful to
    # the users and consistent with the purposes of the processing.
    # [values based on W3C DPV-DP]
    attribute_category: str = Field(alias="attributeCategory")


class DataUsingServiceModel(DataDisclosureAgreementBaseModel):

    # This is the DID of the data using service signing the agreement
    did: str

    # Name of the DUS signing the agreement
    name: str

    # The legal ID of the data using service
    legal_id: str = Field(alias="legalId")

    # This is the data using service organisation URL
    url: str

    # Industry sector that the DUS belongs to
    industry_sector: str = Field(alias="industrySector")

    # The purpose for which the data is being used by the DUS
    usage_purposes: str = Field(alias="usagePurposes")

    # The jurisdiction associated with the data using service
    # consuming personal data that the privacy regulation is followed.
    # These can be country, economic union, law, location or region.
    # [value based on W3C Location and Jurisdiction]
    jurisdiction: str

    # Reference to how data subject may withdraw.
    withdrawal: str

    # Reference to information on how to exercise
    # privacy rights (ex. erasure, objection, withdrawal, copy)
    privacy_rights: str = Field(alias="privacyRights")

    # The responsible entity or person in the organisation
    # signing the data disclosure agreement
    signature_contact: str = Field(alias="signatureContact")


class ProofModel(DataDisclosureAgreementBaseModel):
    # Proof identifier
    id: str

    # Signature schema type (For e.g. ed25519, es256 e.t.c.)
    type: str

    # Proof creation time (ISO 8601 UTC)
    created: str

    # Should match the data_using_service did
    verification_method: str = Field(alias="verificationMethod")

    # Contract agreement (Type inferred from JSON-LD spec)
    proof_purpose: str = Field(alias="proofPurpose")

    # Proof value
    proof_value: str = Field(alias="proofValue")


class DataDisclosureAgreementModel(DataDisclosureAgreementBaseModel):

    # Defines the context of this document. E.g. the link the JSON-LD
    context: typing.Union[typing.List[str], str] = Field(alias="@context")

    # Identifier to the data disclosure agreement instance
    # addressed to a specific DUS
    id: str = Field(alias="@id")

    # Type of the agreement
    type: typing.List[str] = Field(alias="@type")

    # Version number of the data disclosure agreement
    version: str

    # Identifier to the template of the data disclosure agreement
    template_id: str = Field(alias="templateId")

    # Version number of the data disclosure agreement template
    template_version: str = Field(alias="templateVersion")

    # language used. If not present default language is English
    language: str

    # Encapsulates the data controller data
    data_controller: DataControllerModel = Field(alias="dataController")

    # Duration of the agreement after which the
    # data disclosure agreement expires
    agreement_period: int = Field(alias="agreementPeriod")

    # Used by the DS to configure any data sharing restrictions
    # towards the DUS. This could reuse the
    # data agreement policy parameters as is.
    data_sharing_restrictions: DataSharingRestrictionsModel = Field(
        alias="dataSharingRestrictions")

    # Describes the purpose for which the data source shares
    # personal data as described in the
    # data agreement [values based on W3C DPV Purposes]
    purpose: str

    # Additional description of the purpose
    # for which the data source shares personal data
    purpose_description: str = Field(
        alias="purposeDescription")

    # Indicate the lawful basis for sharing personal data.
    # These can be consent, legal obligation, contract, vital interest,
    # public task or legitimate_interest. [values based on W3C DPV legal basis]
    lawful_basis: str = Field(
        alias="lawfulBasis")

    # Encapsulates the attributes shared by the data source
    personal_data: typing.List[PersonalDataModel] = Field(
        alias="personalData")

    # The code of conduct is followed by the data source.
    # This provides the proper application of privacy regulation
    # taking into account specific features within a sector.
    # The code of conduct shall reference the name of the code of conduct
    # and with a publicly accessible reference.
    code_of_conduct: str = Field(
        alias="codeOfConduct")

    # The data using services that have signed up for consuming data.
    # This get populated after the data disclosure agreement
    # is proposed by the data using service
    data_using_service: DataUsingServiceModel = Field(
        alias="dataUsingService")

    # Encapsulates the event signatures that allows anyone (e.g. an auditor)
    # to verify the authencity and source of the data disclosure agreement.
    # Its uses linked data proofs as per W3C and contains a set of attributes
    # that represent a Linked Data digital proof
    # and the parameters required to verify it.
    proof: typing.Optional[ProofModel]

    proof_chain: typing.Optional[typing.List[ProofModel]] = Field(
        alias="proofChain")
