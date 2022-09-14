from asynctest import TestCase as AsyncTestCase
from dexa_sdk.agreements.da.v1_0.models.da_instance_models import (
    DataAgreementDataPolicyModel,
    DataAgreementDPIAModel,
    DataAgreementInstanceModel,
    DataAgreementPersonalDataModel,
    DataAgreementProofModel,
)


class TestDAInstanceModels(AsyncTestCase):
    """Test DA instance models"""

    async def test_data_agreement_instance_serialisation(self):
        """Test data agreement instance serialisation"""

        data_agreement_instance_model = DataAgreementInstanceModel(
            template_id="06b86978-b6b7-4495-994d-6384fa0e0289",
            template_version="1.0.0",
            version="1.0.0",
            language="en",
            data_controller_name="XYZ Company",
            data_controller_url="https://company.xyz",
            data_policy=DataAgreementDataPolicyModel(
                data_retention_period=365,
                policy_url="https://clarifyhealth.com/privacy-policy/",
                jurisdiction="EU",
                industry_sector="Healthcare",
                geographic_restriction="EU",
                storage_location="EU",
                third_party_data_sharing=False,
            ),
            purpose="Fetch diabetic records and recommend foods",
            purpose_description="To perform ML on diabetic records and recommend foods",
            lawful_basis="consent",
            method_of_use="data-using-service",
            personal_data=[
                DataAgreementPersonalDataModel(
                    attribute_name="Name",
                    attribute_sensitive=True,
                    attribute_description="Name of the individual",
                )
            ],
            dpia=DataAgreementDPIAModel(
                dpia_date="2011-10-05T14:48:00.000Z",
                dpia_summary_url="https://org.com/dpia_results.html",
            ),
            proof=DataAgreementProofModel(
                proof_id="did:key:z6MkiTBz1ymuepAQ4HEHYSF1H8quG5GLVVQR3djdX3mDooWp#1",
                proof_type="Ed25519Signature2018",
                created="2021-05-08T08:41:59+0000",
                verification_method="did:key:z6MkiTBz1ymuepAQ4HEHYSF1H8quG5GLVVQR3djdX3mDooWp",
                proof_purpose="authentication",
                proof_value="z6MkwW6aqMnjgrhJXFUko3NnZPGzVpkNzhYK7yEhnsibm",
            ),
            data_subject_did="did:key:z6Mk",
        )

        data_agreement_instance_dict = data_agreement_instance_model.serialize()

        assert (
            data_agreement_instance_model.proof.proof_id
            == data_agreement_instance_dict["proof"]["id"]
        )
        assert (
            data_agreement_instance_model.proof.verification_method
            == data_agreement_instance_dict["proof"]["verificationMethod"]
        )
        assert (
            data_agreement_instance_model.data_subject_did
            == data_agreement_instance_dict["dataSubjectDid"]
        )

        data_agreement_instance_model.proof = None
        data_agreement_instance_model.proof_chain = [
            DataAgreementProofModel(
                proof_id="did:key:z6MkiTBz1ymuepAQ4HEHYSF1H8quG5GLVVQR3djdX3mDooWp#1",
                proof_type="Ed25519Signature2018",
                created="2021-05-08T08:41:59+0000",
                verification_method="did:key:z6MkiTBz1ymuepAQ4HEHYSF1H8quG5GLVVQR3djdX3mDooWp",
                proof_purpose="authentication",
                proof_value="z6MkwW6aqMnjgrhJXFUko3NnZPGzVpkNzhYK7yEhnsibm",
            )
        ]

        data_agreement_instance_dict = data_agreement_instance_model.serialize()

        assert len(data_agreement_instance_model.proof_chain) == 1

    async def test_data_agreement_instance_deserialisation(self):
        """Test data agreement instance deserialisation"""

        data_agreement_instance_dict = {
            "@context": [
                "https://raw.githubusercontent.com/decentralised-dataexchange/data-exchange-agreements/main/interface-specs/jsonld/contexts/dexa-context.jsonld",
                "https://w3id.org/security/v2",
            ],
            "@id": "5d2ecbb8-29d7-442f-8304-1384df96f522",
            "@type": ["DataAgreement"],
            "version": "1.0.0",
            "templateId": "06b86978-b6b7-4495-994d-6384fa0e0289",
            "templateVersion": "1.0.0",
            "language": "en",
            "dataControllerName": "XYZ Company",
            "dataControllerUrl": "https://company.xyz",
            "dataPolicy": {
                "policyUrl": "https://clarifyhealth.com/privacy-policy/",
                "jurisdiction": "EU",
                "industrySector": "Healthcare",
                "dataRetentionPeriod": 365,
                "geographicRestriction": "EU",
                "storageLocation": "EU",
                "thirdPartyDataSharing": False,
            },
            "purpose": "Fetch diabetic records and recommend foods",
            "purposeDescription": "To perform ML on diabetic records and recommend foods",
            "lawfulBasis": "consent",
            "methodOfUse": "data-using-service",
            "personalData": [
                {
                    "attributeId": "a56e0361-3814-426d-be92-e6efa291db7a",
                    "attributeName": "Name",
                    "attributeSensitive": False,
                    "attributeDescription": "Name of the individual",
                }
            ],
            "dpia": {
                "dpiaDate": "2011-10-05T14:48:00.000Z",
                "dpiaSummaryUrl": "https://org.com/dpia_results.html",
            },
            "dataSubjectDid": "did:key:z6Mk",
            "proofChain": [
                {
                    "id": "did:key:z6MkiTBz1ymuepAQ4HEHYSF1H8quG5GLVVQR3djdX3mDooWp#1",
                    "type": "Ed25519Signature2018",
                    "created": "2021-05-08T08:41:59+0000",
                    "verificationMethod": "did:key:z6MkiTBz1ymuepAQ4HEHYSLVVQR3djdX3mDooWp",
                    "proofPurpose": "authentication",
                    "proofValue": "z6MkwW6aqMnjgrhJXFUko3NnZPGzVpkNzhYK7yEhnsibm",
                }
            ],
        }

        data_agreement_instance_model = DataAgreementInstanceModel.deserialize(
            data_agreement_instance_dict
        )

        assert len(data_agreement_instance_model.proof_chain) == 1
