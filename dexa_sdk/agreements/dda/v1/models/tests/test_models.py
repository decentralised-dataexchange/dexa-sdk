from asynctest import TestCase as AsyncTestCase
from asynctest import mock as async_mock
from merklelib import MerkleTree
from ..models import (
    DataControllerModel,
    DataSharingRestrictionsModel,
    DataUsingServiceModel,
    PersonalDataModel,
    ProofModel,
    DataDisclosureAgreementModel,
)


class TestDDAModel(AsyncTestCase):
    """Tests for DDA Model"""

    async def setUp(self) -> None:
        self.data_controller = DataControllerModel(
            did="did:abc",
            name="alice",
            legal_id="lei:abc",
            url="alice.com",
            industry_sector="retail"
        )

        self.data_sharing_restrictions = DataSharingRestrictionsModel(
            policy_url="alice.com/policy.html",
            jurisdiction="EU",
            industry_sector="Retail",
            data_retention_period=365,
            geographic_restriction="EU",
            storage_location="EU"
        )

        self.personal_data = PersonalDataModel(
            attribute_id="abc123",
            attribute_name="abc",
            attribute_sensitive="true",
            attribute_category="personal_data"
        )

        self.data_using_service = DataUsingServiceModel(
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

        self.proof = ProofModel(
            id="urn:uuid:proof",
            type="Ed25519Signature2018",
            created="2017-06-18T21:19:10Z",
            verification_method="did:key:abc",
            proof_purpose="authentication",
            proof_value="x.y.z"
        )

        self.data_disclosure_agreement = DataDisclosureAgreementModel(
            context=[
                ("https://raw.githubusercontent.com/decentralised-dataexchange"
                 "/data-exchange-agreements/main/interface-specs"
                 "/jsonld/contexts"
                 "/dexa-context.jsonld"),
                "https://w3id.org/security/v2"
            ],
            id="urn:uuid:xyz",
            type=["DataDisclosureAgreement"],
            version="0.0.1",
            template_id="urn:uuid:abc",
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
            proof_chain=[self.proof]
        )

    async def test_data_controller(self) -> None:
        """Test data controller model and schema"""

        result = self.data_controller.to_dict()

        assert result["did"] == self.data_controller.did
        assert result["name"] == self.data_controller.name
        assert result["legalId"] == self.data_controller.legal_id
        assert result["url"] == self.data_controller.url
        assert result["industrySector"] == \
            self.data_controller.industry_sector

    async def test_data_sharing_restrictions(self) -> None:
        """Test data sharing restrictions model and schema"""

        result = self.data_sharing_restrictions.to_dict()

        assert result["policyUrl"] == \
            self.data_sharing_restrictions.policy_url
        assert result["jurisdiction"] == \
            self.data_sharing_restrictions.jurisdiction
        assert result["industrySector"] == \
            self.data_sharing_restrictions.industry_sector
        assert result["dataRetentionPeriod"] == \
            self.data_sharing_restrictions.data_retention_period
        assert result["geographicRestriction"] == \
            self.data_sharing_restrictions.geographic_restriction
        assert result["storageLocation"] == \
            self.data_sharing_restrictions.storage_location

    async def test_personal_data(self) -> None:
        """Test personal data model and schema"""

        result = self.personal_data.to_dict()

        assert result["attributeId"] == self.personal_data.attribute_id
        assert result["attributeName"] == self.personal_data.attribute_name
        assert result["attributeSensitive"] == \
            self.personal_data.attribute_sensitive
        assert result["attributeCategory"] == \
            self.personal_data.attribute_category

    async def test_data_using_service(self) -> None:
        """Test data using service model and schema"""

        result = self.data_using_service.to_dict()

        assert result["did"] == self.data_using_service.did
        assert result["name"] == self.data_using_service.name
        assert result["legalId"] == self.data_using_service.legal_id
        assert result["url"] == self.data_using_service.url
        assert result["industrySector"] == \
            self.data_using_service.industry_sector
        assert result["usagePurposes"] == \
            self.data_using_service.usage_purposes
        assert result["jurisdiction"] == self.data_using_service.jurisdiction
        assert result["withdrawal"] == \
            self.data_using_service.withdrawal
        assert result["privacyRights"] == \
            self.data_using_service.privacy_rights
        assert result["signatureContact"] == \
            self.data_using_service.signature_contact

    async def test_proof(self) -> None:
        """Test proof model and schema"""

        result = self.proof.to_dict()

        assert result["id"] == self.proof.id
        assert result["type"] == self.proof.type
        assert result["created"] == self.proof.created
        assert result["verificationMethod"] == self.proof.verification_method
        assert result["proofPurpose"] == self.proof.proof_purpose
        assert result["proofValue"] == self.proof.proof_value

    async def test_data_disclosure_agreement(self) -> None:
        """Test data disclosure agreement model and schema"""

        result = self.data_disclosure_agreement.to_dict()

        assert result["@context"] == self.data_disclosure_agreement.context
        assert result["@id"] == self.data_disclosure_agreement.id
        assert result["version"] == self.data_disclosure_agreement.version
        assert result["templateId"] == \
            self.data_disclosure_agreement.template_id
        assert result["templateVersion"] == \
            self.data_disclosure_agreement.template_version
        assert result["language"] == self.data_disclosure_agreement.language
        assert result["dataController"]["did"] == \
            self.data_disclosure_agreement.data_controller.did
        assert result["agreementPeriod"] == \
            self.data_disclosure_agreement.agreement_period
        assert result["dataSharingRestrictions"]["dataRetentionPeriod"] \
            == self.data_disclosure_agreement\
            .data_sharing_restrictions\
            .data_retention_period
        assert result["purpose"] == \
            self.data_disclosure_agreement.purpose
        assert result["purposeDescription"] == \
            self.data_disclosure_agreement.purpose_description
        assert result["lawfulBasis"] == \
            self.data_disclosure_agreement.lawful_basis
        assert result["personalData"][0]["attributeId"] == \
            self.data_disclosure_agreement.personal_data[0].attribute_id
        assert result["codeOfConduct"] == \
            self.data_disclosure_agreement.code_of_conduct
        assert result["dataUsingService"]["did"] == \
            self.data_disclosure_agreement.data_using_service.did
        assert result["proofChain"][0]["id"] == \
            self.data_disclosure_agreement.proof_chain[0].id

    @async_mock.patch(("dexa_sdk.agreements.dda.v1.models"
                       ".DataDisclosureAgreementBaseModel.nquads"))
    async def test_data_disclosure_agreement_merkletree(self,
                                                        mock_nquads) -> None:
        """Test data disclosure agreement merkle tree"""
        mock_nquads.return_value = [
            ('<urn:uuid:proof> <http://purl.org/dc/terms/created> '
             '"2017-06-18T21:19:10Z"^^'
             '<http://www.w3.org/2001/XMLSchema#dateTime> .')
        ]

        mt = self.data_disclosure_agreement.merkle_tree

        assert isinstance(mt, MerkleTree)
        assert len(mt.leaves) == 1

    @async_mock.patch(("pyld.jsonld.normalize"))
    async def test_data_disclosure_agreement_nquads(self,
                                                    mock_normalize) -> None:
        """Test data disclosure agreement nquads"""
        mock_normalize.return_value = (
            '<urn:uuid:proof> '
            '<http://purl.org/dc/terms/created> '
            '"2017-06-18T21:19:10Z"^^'
            '<http://www.w3.org/2001/XMLSchema#dateTime> .\n')

        nquads = self.data_disclosure_agreement.nquads()

        assert isinstance(nquads, list)
        assert len(nquads) == 1

    @async_mock.patch(("dexa_sdk.agreements.dda.v1.models"
                       ".DataDisclosureAgreementBaseModel.nquads"))
    @async_mock.patch(("dexa_sdk.jsonld.core"
                       ".jsonld_context_fingerprint"))
    async def test_data_disclosure_agreement_did_mydata(
            self,
            mock_jsonld_context_fingerprint,
            mock_nquads
    ) -> None:
        """Test data disclosure agreement did:mydata identifier"""
        mock_nquads.return_value = [
            ('<urn:uuid:proof> <http://purl.org/dc/terms/created> '
             '"2017-06-18T21:19:10Z"^^'
             '<http://www.w3.org/2001/XMLSchema#dateTime> .')
        ]

        mock_jsonld_context_fingerprint.return_value = \
            "ff2629dbdfd4157d051c7c60a3ec095864b2327f87b77b273a1772c1913445f0"
        did = self.data_disclosure_agreement.mydata_did

        assert did.startswith("did:mydata:zAMr")
