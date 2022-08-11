import typing
from pydantic import Field
from merklelib import MerkleTree
from .base import DataDisclosureAgreementBase
from .....storage.merkletree import build_merkle_tree_from_pydantic_base_model


class DataController(DataDisclosureAgreementBase):
    # This is the DID of the data source preparing the agreement
    did: str

    # The name of the data source exposing the data
    name: str

    # This is the legal ID to the data source.
    # E.g. Swedish Organisation Number
    legal_id: str

    # This is the data source organisation URL
    url: str

    # Industry sector that the DS belongs to
    industry_sector: str

    class Config:
        __dda_field_jsonpath__ = "$.data_controller."


class DataSharingRestrictions(DataDisclosureAgreementBase):

    # URL to the privacy policy document of the data source organisation
    policy_url: str

    # The jurisdiction associated with the data source exposing
    # the personal data that the privacy regulation is followed.
    # These can be country, economic union, law, location or region.
    # [value based on W3C Location and Jurisdiction]
    jurisdiction: str

    # The sector to which the data source restricts the use of data
    # by any data using services. If no restriction, leave blank
    industry_sector: str

    # The amount of time that the data source holds onto
    # any personal data, in seconds.
    data_retention_period: int

    # The country or economic union is restricted from
    # processing personal data.[value based on W3C
    # Location and Jurisdiction] for the data source
    geographic_restriction: str

    # The geographic location where the personal
    # data is stored by the data source
    storage_location: str

    class Config:
        __dda_field_jsonpath__ = "$.data_sharing_restrictions."


class PersonalData(DataDisclosureAgreementBase):

    # Identifier of the attribute
    attribute_id: str

    # Name of the attributes that is being shared
    attribute_name: str

    # Defines the sensitivity of the data as per PII
    attribute_sensitive: str

    # An explicit list of personal data categories to be shared.
    # The categories shall be defined using language meaningful to
    # the users and consistent with the purposes of the processing.
    # [values based on W3C DPV-DP]
    attribute_category: str

    class Config:
        __dda_field_jsonpath__ = "$.personal_data."


class DataUsingService(DataDisclosureAgreementBase):

    # This is the DID of the data using service signing the agreement
    did: str

    # Name of the DUS signing the agreement
    name: str

    # The legal ID of the data using service
    legal_id: str

    # This is the data using service organisation URL
    url: str

    # Industry sector that the DUS belongs to
    industry_sector: str

    # The purpose for which the data is being used by the DUS
    usage_purposes: str

    # The jurisdiction associated with the data using service
    # consuming personal data that the privacy regulation is followed.
    # These can be country, economic union, law, location or region.
    # [value based on W3C Location and Jurisdiction]
    jurisdiction: str

    # Reference to how data subject may withdraw.
    withdrawal: str

    # Reference to information on how to exercise
    # privacy rights (ex. erasure, objection, withdrawal, copy)
    privacy_rights: str

    # The responsible entity or person in the organisation
    # signing the data disclosure agreement
    signature_contact: str

    class Config:
        __dda_field_jsonpath__ = "$.data_using_service."


class Event(DataDisclosureAgreementBase):

    # Event identifier
    id: str

    # Event timestamp (ISO 8601 UTC)
    timestamp: str

    # Should match the data_using_service did
    did: str

    # The various available states are:
    # offer/accept/reject/terminate/fetch-data
    state: str

    class Config:
        __dda_field_jsonpath__ = "$.event."


class Proof(DataDisclosureAgreementBase):
    # Proof identifier
    id: str

    # Signature schema type (For e.g. ed25519, es256 e.t.c.)
    type: str

    # Proof creation time (ISO 8601 UTC)
    created: str

    # Should match the data_using_service did
    verification_method: str

    # Contract agreement (Type inferred from JSON-LD spec)
    proof_purpose: str

    # Proof value
    proof_value: str

    class Config:
        __dda_field_jsonpath__ = "$.proof."


class DataDisclosureAgreement(DataDisclosureAgreementBase):

    # Defines the context of this document. E.g. the link the JSON-LD
    context: typing.List[str] = Field(alias="@context")

    # Identifier to the data disclosure agreement instance
    # addressed to a specific DUS
    id: str

    # Version number of the data disclosure agreement
    version: str

    # Identifier to the template of the data disclosure agreement
    template_id: str

    # Version number of the data disclosure agreement template
    template_version: str

    # language used. If not present default language is English
    language: str

    # Encapsulates the data controller data
    data_controller: DataController

    # Duration of the agreement after which the
    # data disclosure agreement expires
    agreement_period: int

    # Used by the DS to configure any data sharing restrictions
    # towards the DUS. This could reuse the
    # data agreement policy parameters as is.
    data_sharing_restrictions: DataSharingRestrictions

    # Describes the purpose for which the data source shares
    # personal data as described in the
    # data agreement [values based on W3C DPV Purposes]
    purpose: str

    # Additional description of the purpose
    # for which the data source shares personal data
    purpose_description: str

    # Indicate the lawful basis for sharing personal data.
    # These can be consent, legal obligation, contract, vital interest,
    # public task or legitimate_interest. [values based on W3C DPV legal basis]
    lawful_basis: str

    # Encapsulates the attributes shared by the data source
    personal_data: typing.List[PersonalData]

    # The code of conduct is followed by the data source.
    # This provides the proper application of privacy regulation
    # taking into account specific features within a sector.
    # The code of conduct shall reference the name of the code of conduct
    # and with a publicly accessible reference.
    code_of_conduct: str

    # The data using services that have signed up for consuming data.
    # This get populated after the data disclosure agreement
    # is proposed by the data using service
    data_using_service: DataUsingService

    # Encapsulates the data disclosure agreement lifecycle event data.
    # For e.g. data disclosure agreement Offer, Accept, Reject, Terminate etc.
    event: typing.List[Event]

    # Encapsulates the event signatures that allows anyone (e.g. an auditor)
    # to verify the authencity and source of the data disclosure agreement.
    # Its uses linked data proofs as per W3C and contains a set of attributes
    # that represent a Linked Data digital proof
    # and the parameters required to verify it.
    proof: typing.List[Proof]

    class Config:
        allow_population_by_field_name = True
        __dda_field_jsonpath__ = "$."

    def to_merkle_tree(self) -> MerkleTree:
        """Get <MerkleTree> representation"""

        # Build <MerkleTree>
        mt = build_merkle_tree_from_pydantic_base_model(
            self,
            dict_fields=[
                "data_controller",
                "data_sharing_restrictions",
                "data_using_service"
            ],
            list_fields=[
                "context",
                "personal_data",
                "event",
                "proof"
            ]
        )
        return mt
