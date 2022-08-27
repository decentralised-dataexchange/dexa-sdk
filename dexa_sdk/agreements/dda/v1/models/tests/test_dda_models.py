from asynctest import TestCase as AsyncTestCase
from ..dda_models import (
    DataControllerModel,
    DataDisclosureAgreementModel,
    DataSharingRestrictionsModel,
    PersonalDataModel,
    DataUsingServiceModel,
    ProofModel
)


class TestACAPyDDAModels(AsyncTestCase):
    """Test DDA Models (ACA-Py compatible)"""

    async def test_data_controller_model_serialisation(self) -> None:
        """Test data controller model serialisation"""
        data_controller = DataControllerModel(
            did="did:key:z6mk",
            name="Happy Shopping AB",
            legal_id="lei:happy",
            url="https://happyshopping.se",
            industry_sector="Retail"
        )

        dc = data_controller.serialize()

        assert dc["legalId"] == data_controller.legal_id

    async def test_data_controller_model_deserialisation(self) -> None:
        """Test data controller model deserialisation"""
        dc = {
            "did": "did:key:z6mk",
            "name": "Happy Shopping AB",
            "legalId": "lei:happy",
            "url": "https://happyshopping.se",
            "industrySector": "Retail"
        }

        data_controller = DataControllerModel.deserialize(dc)

        assert data_controller.legal_id == dc["legalId"]

    async def test_data_disclosure_agreement_model_serialisation(self) -> None:
        """Test data disclosure agreement model serialisation"""
        data_disclosure_agreement = DataDisclosureAgreementModel(
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

        dda = data_disclosure_agreement.serialize()

        assert dda["dataController"]["legalId"] == \
            data_disclosure_agreement.data_controller.legal_id

    async def test_data_disclosure_agreement_deserialistion(self) -> None:
        """Test data disclosure agreement deserialisation"""

        dda = {
            "@context": [
                "https://schema.org",
                "https://w3c/security/v1"
            ],
            "@id": "urn:uuid:abc123",
            "@type": [
                "DataDisclosureAgreement"
            ],
            "version": "1.0.0",
            "templateId": "urn:uuid:template123",
            "templateVersion": "1.0.0",
            "language": "en",
            "dataController": {
                "did": "did:key:z6mk",
                "name": "XYZ company",
                "legalId": "lei:xyz",
                "url": "https://company.xyz",
                "industrySector": "Retail"
            },
            "agreementPeriod": 365,
            "dataSharingRestrictions": {
                "policyUrl": "https://company.xyz/policy",
                "jurisdiction": "EU",
                "industrySector": "Retail",
                "dataRetentionPeriod": "365",
                "geographicRestriction": "EU",
                "storageLocation": "EU"
            },
            "purpose": "Health data sharing",
            "purpose_description": "Transfering patient data",
            "lawfulBasis": "consent",
            "personalData": [
                {
                    "attributeId": "urn:uuid:attribute123",
                    "attributeName": "Name",
                    "attributeSensitive": "true",
                    "attributeCategory": "personalData"
                }
            ],
            "codeOfConduct": "https://company.xyz/code_of_conduct",
            "dataUsingService": {
                "did": "did:key:z6mk",
                "name": "ABC company",
                "legalId": "lei:abc",
                "url": "https://company.abc",
                "industrySector": "Retail",
                "usagePurposes": "Insights driven healthcare",
                "jurisdiction": "EU",
                "withdrawal": "https://company.abc/withdrawal",
                "privacyRights": "https://company.abc/privacy_rights",
                "signatureContact": "did:key:z6mk"
            },
            "proof": {
                "id": "urn:uuid:proof123",
                "type": "ED25519Signature2018",
                "created": "2022",
                "verificationMethod": "did:key:z6mk",
                "proofPurpose": "Authentication",
                "proofValue": "x.y.z"
            }
        }

        data_disclosure_agreement = DataDisclosureAgreementModel.deserialize(
            dda)

        assert data_disclosure_agreement.proof.verification_method == dda[
            "proof"]["verificationMethod"]
