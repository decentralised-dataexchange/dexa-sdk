from asynctest import TestCase as AsyncTestCase
from rich.console import Console
from ..dexa_model import (
    DataController,
    DataControllerSchema,
    DataSharingRestrictions,
    DataSharingRestrictionsSchema,
    DataUsingService,
    DataUsingServiceSchema,
    PersonalData,
    PersonalDataSchema,
    Event,
    EventSchema,
    Proof,
    ProofSchema,
    DataExchangeAgreement,
    DataExchangeAgreementSchema
)


class TestDexaModel(AsyncTestCase):
    """Tests for DEXA Model"""

    async def setUp(self) -> None:
        self.console = Console()

    async def test_data_controller(self) -> None:
        """Test data controller model and schema"""

        data_controller = DataController(
            did="did:abc",
            name="alice",
            legal_id="lei:abc",
            url="alice.com",
            industry_sector="retail"
        )

        dc_schema = DataControllerSchema()

        result = dc_schema.dump(data_controller)

        assert result["did"] == data_controller.did
        assert result["name"] == data_controller.name
        assert result["legal_id"] == data_controller.legal_id
        assert result["url"] == data_controller.url
        assert result["industry_sector"] == data_controller.industry_sector

        result_json = dc_schema.dumps(data_controller)

        assert len(result_json) == 107

    async def test_data_sharing_restrictions(self) -> None:
        """Test data sharing restrictions model and schema"""

        data_sharing_restrictions = DataSharingRestrictions(
            policy_url="alice.com/policy.html",
            jurisdiction="EU",
            industry_sector="Retail",
            data_retention_period="365",
            geographic_restriction="EU",
            storage_location="EU"
        )

        dsr_schema = DataSharingRestrictionsSchema()

        result = dsr_schema.dump(data_sharing_restrictions)

        assert result["policy_url"] == data_sharing_restrictions.policy_url
        assert result["jurisdiction"] == data_sharing_restrictions.jurisdiction
        assert result["industry_sector"] == data_sharing_restrictions.industry_sector
        assert result["data_retention_period"] == data_sharing_restrictions.data_retention_period
        assert result["geographic_restriction"] == data_sharing_restrictions.geographic_restriction
        assert result["storage_location"] == data_sharing_restrictions.storage_location

        result_json = dsr_schema.dumps(data_sharing_restrictions)

        assert len(result_json) == 180

    async def test_personal_data(self) -> None:
        """Test personal data model and schema"""

        personal_data = PersonalData(
            attribute_id="abc123",
            attribute_name="abc",
            attribute_sensitive="true",
            attribute_category="personal_data"
        )

        pd_schema = PersonalDataSchema()

        result = pd_schema.dump(personal_data)

        assert result["attribute_id"] == personal_data.attribute_id
        assert result["attribute_name"] == personal_data.attribute_name
        assert result["attribute_sensitive"] == personal_data.attribute_sensitive
        assert result["attribute_category"] == personal_data.attribute_category

        result_json = pd_schema.dumps(personal_data)

        assert len(result_json) == 121

    async def test_data_using_service(self) -> None:
        """Test data using service model and schema"""

        data_using_service = DataUsingService(
            did="did:abc:alice",
            name="abc",
            legal_id="lei:abc",
            url="abc.com",
            industry_sector="retail",
            usage_purposes="abc",
            jurisdiction="EU",
            withdrawal="abc.com/withdrawal.html",
            privacy_rights="abc.com/privacy_rights.html",
            signature_contact="alice"
        )

        dus_schema = DataUsingServiceSchema()

        result = dus_schema.dump(data_using_service)

        assert result["did"] == data_using_service.did
        assert result["name"] == data_using_service.name
        assert result["legal_id"] == data_using_service.legal_id
        assert result["url"] == data_using_service.url
        assert result["industry_sector"] == data_using_service.industry_sector
        assert result["usage_purposes"] == data_using_service.usage_purposes
        assert result["jurisdiction"] == data_using_service.jurisdiction
        assert result["withdrawal"] == data_using_service.withdrawal
        assert result["privacy_rights"] == data_using_service.privacy_rights
        assert result["signature_contact"] == data_using_service.signature_contact

        result_json = dus_schema.dumps(data_using_service)

        assert len(result_json) == 276

    async def test_event(self) -> None:
        """Test event model and schema"""

        event = Event(
            id="abc123",
            timestamp="1234",
            did="did:abc:alice",
            state="accept"
        )

        event_schema = EventSchema()

        result = event_schema.dump(event)

        assert result["id"] == event.id
        assert result["timestamp"] == event.timestamp
        assert result["did"] == event.did
        assert result["state"] == event.state

        result_json = event_schema.dumps(event)

        assert len(result_json) == 80

    async def test_proof(self) -> None:
        """Test proof model and schema"""

        proof = Proof(
            id="abc1234",
            type="Assertion",
            created="1234",
            verification_method="Assertion",
            proof_purpose="Assertion",
            proof_value="x.y.z"
        )

        proof_schema = ProofSchema()

        result = proof_schema.dump(proof)

        assert result["id"] == proof.id
        assert result["type"] == proof.type
        assert result["created"] == proof.created
        assert result["verification_method"] == proof.verification_method
        assert result["proof_purpose"] == proof.proof_purpose
        assert result["proof_value"] == proof.proof_value

        result_json = proof_schema.dumps(proof)

        assert len(result_json) == 147

    async def test_data_exchange_agreement(self) -> None:
        """Test data exchange agreement model and schema"""

        data_controller = DataController(
            did="did:abc",
            name="alice",
            legal_id="lei:abc",
            url="alice.com",
            industry_sector="retail"
        )

        data_sharing_restrictions = DataSharingRestrictions(
            policy_url="alice.com/policy.html",
            jurisdiction="EU",
            industry_sector="Retail",
            data_retention_period="365",
            geographic_restriction="EU",
            storage_location="EU"
        )

        personal_data = PersonalData(
            attribute_id="abc123",
            attribute_name="abc",
            attribute_sensitive="true",
            attribute_category="personal_data"
        )

        data_using_service = DataUsingService(
            did="did:abc:alice",
            name="abc",
            legal_id="lei:abc",
            url="abc.com",
            industry_sector="retail",
            usage_purposes="abc",
            jurisdiction="EU",
            withdrawal="abc.com/withdrawal.html",
            privacy_rights="abc.com/privacy_rights.html",
            signature_contact="alice"
        )

        event = Event(
            id="abc123",
            timestamp="1234",
            did="did:abc:alice",
            state="accept"
        )

        proof = Proof(
            id="abc1234",
            type="Assertion",
            created="1234",
            verification_method="Assertion",
            proof_purpose="Assertion",
            proof_value="x.y.z"
        )

        data_exchange_agreement = DataExchangeAgreement(
            context="schema.org",
            id="abc123",
            version="0.0.1",
            template_id="abc123",
            template_version="0.0.1",
            language="en",
            data_controller=data_controller,
            agreement_period="365",
            data_sharing_restrictions=data_sharing_restrictions,
            purpose="some purpose",
            purpose_description="description of the purpose",
            lawful_basis="consent",
            personal_data=[personal_data],
            code_of_conduct="abc.com/code_of_conduct.html",
            data_using_service=data_using_service,
            event=[event],
            proof=[proof]
        )

        dexa_schema = DataExchangeAgreementSchema()

        result = dexa_schema.dump(data_exchange_agreement)

        assert result["context"] == data_exchange_agreement.context
        assert result["id"] == data_exchange_agreement.id
        assert result["version"] == data_exchange_agreement.version
        assert result["template_id"] == data_exchange_agreement.template_id
        assert result["template_version"] == data_exchange_agreement.template_version
        assert result["language"] == data_exchange_agreement.language
        assert result["data_controller"]["did"] == data_exchange_agreement.data_controller.did
        assert result["agreement_period"] == data_exchange_agreement.agreement_period
        assert result["data_sharing_restrictions"]["data_retention_period"] == data_exchange_agreement.data_sharing_restrictions.data_retention_period
        assert result["purpose"] == data_exchange_agreement.purpose
        assert result["purpose_description"] == data_exchange_agreement.purpose_description
        assert result["lawful_basis"] == data_exchange_agreement.lawful_basis
        assert result["personal_data"][0]["attribute_id"] == data_exchange_agreement.personal_data[0].attribute_id
        assert result["code_of_conduct"] == data_exchange_agreement.code_of_conduct
        assert result["data_using_service"]["did"] == data_exchange_agreement.data_using_service.did
        assert result["event"][0]["id"] == data_exchange_agreement.event[0].id
        assert result["proof"][0]["id"] == data_exchange_agreement.proof[0].id

        result_json = dexa_schema.dumps(data_exchange_agreement)

        assert len(result_json) == 1352
