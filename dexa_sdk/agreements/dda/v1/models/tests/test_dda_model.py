from asynctest import TestCase as AsyncTestCase
from ..dda_model import (
    DataController,
    DataSharingRestrictions,
    DataUsingService,
    PersonalData,
    Event,
    Proof,
    DataDisclosureAgreement,
)


class TestDDAModel(AsyncTestCase):
    """Tests for DDA Model"""

    async def setUp(self) -> None:
        self.data_controller = DataController(
            did="did:abc",
            name="alice",
            legal_id="lei:abc",
            url="alice.com",
            industry_sector="retail"
        )

        self.data_sharing_restrictions = DataSharingRestrictions(
            policy_url="alice.com/policy.html",
            jurisdiction="EU",
            industry_sector="Retail",
            data_retention_period=365,
            geographic_restriction="EU",
            storage_location="EU"
        )

        self.personal_data = PersonalData(
            attribute_id="abc123",
            attribute_name="abc",
            attribute_sensitive="true",
            attribute_category="personal_data"
        )

        self.data_using_service = DataUsingService(
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

        self.event = Event(
            id="abc123",
            timestamp="1234",
            did="did:abc:alice",
            state="accept"
        )

        self.proof = Proof(
            id="abc1234",
            type="Assertion",
            created="1234",
            verification_method="Assertion",
            proof_purpose="Assertion",
            proof_value="x.y.z"
        )

        self.data_disclosure_agreement = DataDisclosureAgreement(
            context=["schema.org", "abc.org"],
            id="abc123",
            version="0.0.1",
            template_id="abc123",
            template_version="0.0.1",
            language="en",
            data_controller=self.data_controller,
            agreement_period=365,
            data_sharing_restrictions=self.data_sharing_restrictions,
            purpose="some purpose",
            purpose_description="description of the purpose",
            lawful_basis="consent",
            personal_data=[self.personal_data],
            code_of_conduct="abc.com/code_of_conduct.html",
            data_using_service=self.data_using_service,
            event=[self.event],
            proof=[self.proof]
        )

    async def test_data_controller(self) -> None:
        """Test data controller model and schema"""

        result = self.data_controller.dict()

        assert result["did"] == self.data_controller.did
        assert result["name"] == self.data_controller.name
        assert result["legal_id"] == self.data_controller.legal_id
        assert result["url"] == self.data_controller.url
        assert result["industry_sector"] == \
            self.data_controller.industry_sector

    async def test_data_controller_merkle_tree(self) -> None:
        """Test data controller merkle tree"""

        mt = self.data_controller.to_merkle_tree()

        assert len(mt.leaves) == 5

    async def test_data_sharing_restrictions(self) -> None:
        """Test data sharing restrictions model and schema"""

        result = self.data_sharing_restrictions.dict()

        assert result["policy_url"] == \
            self.data_sharing_restrictions.policy_url
        assert result["jurisdiction"] == \
            self.data_sharing_restrictions.jurisdiction
        assert result["industry_sector"] == \
            self.data_sharing_restrictions.industry_sector
        assert result["data_retention_period"] == \
            self.data_sharing_restrictions.data_retention_period
        assert result["geographic_restriction"] == \
            self.data_sharing_restrictions.geographic_restriction
        assert result["storage_location"] == \
            self.data_sharing_restrictions.storage_location

    async def test_data_sharing_restrictions_merkle_tree(self) -> None:
        """Test data sharing restrictions merkle tree"""

        mt = self.data_sharing_restrictions.to_merkle_tree()

        assert len(mt.leaves) == 6

    async def test_personal_data(self) -> None:
        """Test personal data model and schema"""

        result = self.personal_data.dict()

        assert result["attribute_id"] == self.personal_data.attribute_id
        assert result["attribute_name"] == self.personal_data.attribute_name
        assert result["attribute_sensitive"] == \
            self.personal_data.attribute_sensitive
        assert result["attribute_category"] == \
            self.personal_data.attribute_category

    async def test_personal_data_merkle_tree(self) -> None:
        """Test personal data merkle tree"""

        mt = self.personal_data.to_merkle_tree()

        assert len(mt.leaves) == 4

    async def test_data_using_service(self) -> None:
        """Test data using service model and schema"""

        result = self.data_using_service.dict()

        assert result["did"] == self.data_using_service.did
        assert result["name"] == self.data_using_service.name
        assert result["legal_id"] == self.data_using_service.legal_id
        assert result["url"] == self.data_using_service.url
        assert result["industry_sector"] == \
            self.data_using_service.industry_sector
        assert result["usage_purposes"] == \
            self.data_using_service.usage_purposes
        assert result["jurisdiction"] == self.data_using_service.jurisdiction
        assert result["withdrawal"] == \
            self.data_using_service.withdrawal
        assert result["privacy_rights"] == \
            self.data_using_service.privacy_rights
        assert result["signature_contact"] == \
            self.data_using_service.signature_contact

    async def test_data_using_service_merkle_tree(self) -> None:
        """Test data using service merkle tree"""

        mt = self.data_using_service.to_merkle_tree()

        assert len(mt.leaves) == 10

    async def test_event(self) -> None:
        """Test event model and schema"""

        result = self.event.dict()

        assert result["id"] == self.event.id
        assert result["timestamp"] == self.event.timestamp
        assert result["did"] == self.event.did
        assert result["state"] == self.event.state

    async def test_event_merkle_tree(self) -> None:
        """Test event merkle tree"""

        mt = self.event.to_merkle_tree()

        assert len(mt.leaves) == 4

    async def test_proof(self) -> None:
        """Test proof model and schema"""

        result = self.proof.dict()

        assert result["id"] == self.proof.id
        assert result["type"] == self.proof.type
        assert result["created"] == self.proof.created
        assert result["verification_method"] == self.proof.verification_method
        assert result["proof_purpose"] == self.proof.proof_purpose
        assert result["proof_value"] == self.proof.proof_value

    async def test_proof_merkle_tree(self) -> None:
        """Test proof merkle tree"""

        mt = self.proof.to_merkle_tree()

        assert len(mt.leaves) == 6

    async def test_data_disclosure_agreement(self) -> None:
        """Test data disclosure agreement model and schema"""

        result = self.data_disclosure_agreement.dict(by_alias=True)

        assert result["@context"] == self.data_disclosure_agreement.context
        assert result["id"] == self.data_disclosure_agreement.id
        assert result["version"] == self.data_disclosure_agreement.version
        assert result["template_id"] == \
            self.data_disclosure_agreement.template_id
        assert result["template_version"] == \
            self.data_disclosure_agreement.template_version
        assert result["language"] == self.data_disclosure_agreement.language
        assert result["data_controller"]["did"] == \
            self.data_disclosure_agreement.data_controller.did
        assert result["agreement_period"] == \
            self.data_disclosure_agreement.agreement_period
        assert result["data_sharing_restrictions"]["data_retention_period"] \
            == self.data_disclosure_agreement\
            .data_sharing_restrictions\
            .data_retention_period
        assert result["purpose"] == \
            self.data_disclosure_agreement.purpose
        assert result["purpose_description"] == \
            self.data_disclosure_agreement.purpose_description
        assert result["lawful_basis"] == \
            self.data_disclosure_agreement.lawful_basis
        assert result["personal_data"][0]["attribute_id"] == \
            self.data_disclosure_agreement.personal_data[0].attribute_id
        assert result["code_of_conduct"] == \
            self.data_disclosure_agreement.code_of_conduct
        assert result["data_using_service"]["did"] == \
            self.data_disclosure_agreement.data_using_service.did
        assert result["event"][0]["id"] == \
            self.data_disclosure_agreement.event[0].id
        assert result["proof"][0]["id"] == \
            self.data_disclosure_agreement.proof[0].id

    async def test_data_disclosure_agreement_merkle_tree(self) -> None:
        """Test data disclosure agreement merkle tree"""

        mt = self.data_disclosure_agreement.to_merkle_tree()

        assert len(mt.leaves) == 17
