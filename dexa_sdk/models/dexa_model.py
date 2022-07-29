import typing
from marshmallow import Schema, fields


class DataController:
    """Data controller model"""

    def __init__(self,
                 did: str,
                 name: str,
                 legal_id: str,
                 url: str,
                 industry_sector: str
                 ) -> None:
        self.did = did
        self.name = name
        self.legal_id = legal_id
        self.url = url
        self.industry_sector = industry_sector


class DataControllerSchema(Schema):
    """Data controller schema"""
    did = fields.Str()
    name = fields.Str()
    legal_id = fields.Str()
    url = fields.Str()
    industry_sector = fields.Str()


class DataSharingRestrictions:
    """Data sharing restrictions model"""

    def __init__(self,
                 policy_url: str,
                 jurisdiction: str,
                 industry_sector: str,
                 data_retention_period: str,
                 geographic_restriction: str,
                 storage_location: str) -> None:
        self.policy_url = policy_url
        self.jurisdiction = jurisdiction
        self.industry_sector = industry_sector
        self.data_retention_period = data_retention_period
        self.geographic_restriction = geographic_restriction
        self.storage_location = storage_location


class DataSharingRestrictionsSchema(Schema):
    """Data sharing restrictions schema"""
    policy_url = fields.Str()
    jurisdiction = fields.Str()
    industry_sector = fields.Str()
    data_retention_period = fields.Str()
    geographic_restriction = fields.Str()
    storage_location = fields.Str()


class PersonalData:
    """Personal data model"""

    def __init__(self,
                 attribute_id: str,
                 attribute_name: str,
                 attribute_sensitive: str,
                 attribute_category: str) -> None:
        self.attribute_id = attribute_id
        self.attribute_name = attribute_name
        self.attribute_sensitive = attribute_sensitive
        self.attribute_category = attribute_category


class PersonalDataSchema(Schema):
    """Personal data schema"""
    attribute_id = fields.Str()
    attribute_name = fields.Str()
    attribute_sensitive = fields.Str()
    attribute_category = fields.Str()


class DataUsingService:
    """Data using service model"""

    def __init__(self,
                 did: str,
                 name: str,
                 legal_id: str,
                 url: str,
                 industry_sector: str,
                 usage_purposes: str,
                 jurisdiction: str,
                 withdrawal: str,
                 privacy_rights: str,
                 signature_contact: str) -> None:
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


class DataUsingServiceSchema(Schema):
    """Data using service schema"""
    did = fields.Str()
    name = fields.Str()
    legal_id = fields.Str()
    url = fields.Str()
    industry_sector = fields.Str()
    usage_purposes = fields.Str()
    jurisdiction = fields.Str()
    withdrawal = fields.Str()
    privacy_rights = fields.Str()
    signature_contact = fields.Str()


class Event:
    """Event model"""

    def __init__(self,
                 id: str,
                 timestamp: str,
                 did: str,
                 state: str) -> None:
        self.id = id
        self.timestamp = timestamp
        self.did = did
        self.state = state


class EventSchema(Schema):
    """Event schema"""
    id = fields.Str()
    timestamp = fields.Str()
    did = fields.Str()
    state = fields.Str()


class Proof:
    """Proof model"""

    def __init__(self,
                 id: str,
                 type: str,
                 created: str,
                 verification_method: str,
                 proof_purpose: str,
                 proof_value: str) -> None:
        self.id = id
        self.type = type
        self.created = created
        self.verification_method = verification_method
        self.proof_purpose = proof_purpose
        self.proof_value = proof_value


class ProofSchema(Schema):
    """Proof schema"""
    id = fields.Str()
    type = fields.Str()
    created = fields.Str()
    verification_method = fields.Str()
    proof_purpose = fields.Str()
    proof_value = fields.Str()


class DataExchangeAgreement:
    """Data exchange agreement model"""

    def __init__(self,
                 context: str,
                 id: str,
                 version: str,
                 template_id: str,
                 template_version: str,
                 language: str,
                 data_controller: DataController,
                 agreement_period: str,
                 data_sharing_restrictions: DataSharingRestrictions,
                 purpose: str,
                 purpose_description: str,
                 lawful_basis: str,
                 personal_data: typing.List[PersonalData],
                 code_of_conduct: str,
                 data_using_service: DataUsingService,
                 event: typing.List[Event],
                 proof: typing.List[Proof]
                 ):
        self.context = context
        self.id = id
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
        self.event = event
        self.proof = proof


class DataExchangeAgreementSchema(Schema):
    """Data exchange agreement schema"""
    context = fields.Str()
    id = fields.Str()
    version = fields.Str()
    template_id = fields.Str()
    template_version = fields.Str()
    language = fields.Str()
    data_controller = fields.Nested(DataControllerSchema)
    agreement_period = fields.Str()
    data_sharing_restrictions = fields.Nested(DataSharingRestrictionsSchema)
    purpose = fields.Str()
    purpose_description = fields.Str()
    lawful_basis = fields.Str()
    personal_data = fields.List(fields.Nested(PersonalDataSchema))
    code_of_conduct = fields.Str()
    data_using_service = fields.Nested(DataUsingServiceSchema)
    event = fields.List(fields.Nested(EventSchema))
    proof = fields.List(fields.Nested(ProofSchema))
