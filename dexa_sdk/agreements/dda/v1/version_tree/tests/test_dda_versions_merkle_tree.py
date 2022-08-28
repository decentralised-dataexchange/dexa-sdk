from asynctest import TestCase as AsyncTestCase
from asynctest import mock as async_mock
from ..version_tree import DDAVersionsMerkleTree
from ...instances import DataDisclosureAgreementInstance
from ...models.dda_models import (
    DataControllerModel,
    DataDisclosureAgreementModel,
    DataSharingRestrictionsModel,
    PersonalDataModel,
    DataUsingServiceModel,
    ProofModel
)


class TestDDAVersionsMerkleTree(AsyncTestCase):
    """Test DDA Versions Merkle Tree Class"""

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
            dda=self.data_disclosure_agreement
        )

    @async_mock.patch(("dexa_sdk.agreements.dda.v1"
                       ".instances.DataDisclosureAgreementInstance.nquads"))
    @async_mock.patch(("dexa_sdk.agreements.dda.v1"
                       ".instances.dda_instance.jsonld_context_fingerprint"))
    async def test_add_single_dda_to_versions_merkle_tree(
        self,
        mock_jsonld_context_fingerprint,
        mock_nquads
    ) -> None:
        """Test add a single DDA to the versions merkle tree"""

        mock_nquads.side_effect = [
            [
                'nquad-statement-1'
            ]
        ]

        mock_jsonld_context_fingerprint.side_effect = [
            "ff2629dbdfd4157d051c7c60a3ec095864b2327f87b77b273a1772c1913445f0"
        ]

        versions_tree = DDAVersionsMerkleTree()
        versions_tree.add(self.dda_container)

        assert len(versions_tree) == 1

    @async_mock.patch(("dexa_sdk.agreements.dda.v1"
                       ".instances.DataDisclosureAgreementInstance.nquads"))
    @async_mock.patch(("dexa_sdk.agreements.dda.v1"
                       ".instances.dda_instance.jsonld_context_fingerprint"))
    async def test_add_two_dda_to_versions_merkle_tree(
        self,
        mock_jsonld_context_fingerprint,
        mock_nquads
    ) -> None:
        """Test add two DDA to the versions merkle tree"""

        mock_nquads.side_effect = [
            'nquad-statement-1',
            'nquad-statement-2'
        ]

        mock_jsonld_context_fingerprint.side_effect = [
            "ff2629dbdfd4157d051c7c60a3ec095864b2327f87b77b273a1772c1913445f0",
            "ff2629dbdfd4157d051c7c60a3ec095864b2327f87b77b273a1772c1913445f1"
        ]
        versions_tree = DDAVersionsMerkleTree()

        dda_container1 = DataDisclosureAgreementInstance(
            dda=self.data_disclosure_agreement
        )

        versions_tree.add(dda_container1)

        dda_container2 = DataDisclosureAgreementInstance(
            dda=self.data_disclosure_agreement
        )

        versions_tree.add(dda_container2)

        assert len(versions_tree) == 2
        assert versions_tree.genesis.next_version_did \
            == versions_tree.current.mydata_did
        assert versions_tree.current.next_version_did is None

    @async_mock.patch(("dexa_sdk.agreements.dda.v1"
                       ".instances.DataDisclosureAgreementInstance.nquads"))
    @async_mock.patch(("dexa_sdk.agreements.dda.v1"
                       ".instances.dda_instance.jsonld_context_fingerprint"))
    async def test_query_a_dda_version_by_merkle_root(
        self,
        mock_jsonld_context_fingerprint,
        mock_nquads
    ) -> None:
        """Test query a dda by version"""

        mock_nquads.side_effect = [
            [
                'nquad-statement-1'
            ],
            [
                'nquad-statement-2'
            ]
        ]

        mock_jsonld_context_fingerprint.side_effect = [
            "ff2629dbdfd4157d051c7c60a3ec095864b2327f87b77b273a1772c1913445f0",
            "ff2629dbdfd4157d051c7c60a3ec095864b2327f87b77b273a1772c1913445f1"
        ]

        versions_tree = DDAVersionsMerkleTree()

        dda_container1 = DataDisclosureAgreementInstance(
            dda=self.data_disclosure_agreement
        )

        versions_tree.add(dda_container1)

        dda_container2 = DataDisclosureAgreementInstance(
            dda=self.data_disclosure_agreement
        )

        versions_tree.add(dda_container2)

        genesis_leaf = versions_tree.genesis
        queried_leaf = versions_tree.get(genesis_leaf.mydata_did)

        assert queried_leaf == genesis_leaf
