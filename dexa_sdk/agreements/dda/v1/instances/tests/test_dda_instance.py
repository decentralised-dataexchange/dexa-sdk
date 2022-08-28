from asynctest import TestCase as AsyncTestCase
from asynctest import mock as async_mock
from merklelib import MerkleTree
from ..dda_instance import DataDisclosureAgreementInstance
from ...models.dda_models import (
    DataControllerModel,
    DataDisclosureAgreementModel,
    DataSharingRestrictionsModel,
    PersonalDataModel,
    DataUsingServiceModel,
    ProofModel
)


class TestDDAInstance(AsyncTestCase):
    """Test data disclosure agreement instance class"""

    async def setUp(self) -> None:
        self.data_disclosure_agreement = DataDisclosureAgreementModel(
            context=["https://schema.org", "https://w3c/security/v1"],
            id="urn:uuid:abc123",
            type=["DataDisclosureAgreement"],
            language="en",
            version="1.0.0",
            template_id="urn:uuid:template123",
            template_version="1.0.0",
            data_controller=DataControllerModel(
                did="did:key:z6mk",
                name="XYZ company",
                legal_id="lei:xyz",
                url="https://company.xyz",
                industry_sector="Retail"
            ),
            agreement_period=365,
            data_sharing_restrictions=DataSharingRestrictionsModel(
                policy_url="https://company.xyz/policy",
                jurisdiction="EU",
                industry_sector="Retail",
                data_retention_period=365,
                geographic_restriction="EU",
                storage_location="EU"
            ),
            purpose="Health data sharing",
            purpose_description="Transfering patient data",
            lawful_basis="consent",
            personal_data=[
                PersonalDataModel(
                    attribute_id="urn:uuid:attribute123",
                    attribute_name="Name"
                )
            ],
            code_of_conduct="https://company.xyz/code_of_conduct",
            data_using_service=DataUsingServiceModel(
                did="did:key:z6mk",
                name="ABC company",
                legal_id="lei:abc",
                url="https://company.abc",
                industry_sector="Retail",
                usage_purposes="Insights driven healthcare",
                jurisdiction="EU",
                withdrawal="https://company.abc/withdrawal",
                privacy_rights="https://company.abc/privacy_rights",
                signature_contact="did:key:z6mk"
            ),
            proof=ProofModel(
                id="urn:uuid:proof123",
                type="ED25519Signature2018",
                created="2022",
                verification_method="did:key:z6mk",
                proof_purpose="Authentication",
                proof_value="x.y.z"
            )
        )

        self.dda_container = DataDisclosureAgreementInstance(
            self.data_disclosure_agreement)

    @async_mock.patch(("dexa_sdk.agreements.dda.v1"
                       ".instances.DataDisclosureAgreementInstance.nquads"))
    async def test_data_disclosure_agreement_merkletree(self,
                                                        mock_nquads) -> None:
        """Test data disclosure agreement merkle tree"""
        mock_nquads.return_value = [
            ('<urn:uuid:proof> <http://purl.org/dc/terms/created> '
             '"2017-06-18T21:19:10Z"^^'
             '<http://www.w3.org/2001/XMLSchema#dateTime> .')
        ]

        mt = self.dda_container.merkle_tree

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

        nquads = self.dda_container.nquads()

        assert isinstance(nquads, list)
        assert len(nquads) == 1

    @async_mock.patch(("dexa_sdk.agreements.dda.v1"
                       ".instances.DataDisclosureAgreementInstance.nquads"))
    # jsonld_context_fingerprint is originally defined at dexa_sdk.jsonld.core
    # but since the function is imported in to the module and
    # not the global scope, we have to patch at module level.
    # (Pattern B as described in the below article)
    # http://bhfsteve.blogspot.com/2012/06/patching-tip-using-mocks-in-python-unit.html
    @async_mock.patch(("dexa_sdk.agreements.dda.v1"
                       ".instances.dda_instance.jsonld_context_fingerprint"))
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
        did = self.dda_container.mydata_did

        assert did.startswith("did:mydata:zAMr")
