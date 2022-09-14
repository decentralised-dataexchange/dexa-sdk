from asynctest import TestCase as AsyncTestCase
from dexa_sdk.agreements.da.v1_0.models.da_models import (
    DataAgreementDataPolicyModel,
    DataAgreementDPIAModel,
    DataAgreementModel,
    DataAgreementPersonalDataModel,
)


class TestDAModels(AsyncTestCase):
    """Test DA models"""

    async def test_dpia_model_serialisation(self) -> None:
        """Test dpia model serialisation"""
        dpia_model = DataAgreementDPIAModel(
            dpia_date="2011-10-05T14:48:00.000Z",
            dpia_summary_url="https://org.com/dpia_results.html",
        )

        dpia_dict = dpia_model.serialize()

        assert dpia_dict["dpiaDate"] == dpia_model.dpia_date

    async def test_dpia_model_deserialisation(self) -> None:
        """Test dpia model deserialisation"""
        dpia_json = {
            "dpiaDate": "2011-10-05T14:48:00.000Z",
            "dpiaSummaryUrl": "https://org.com/dpia_results.html",
        }

        dpia_model: DataAgreementDPIAModel = DataAgreementDPIAModel.deserialize(
            dpia_json
        )

        assert dpia_model.dpia_date == dpia_json["dpiaDate"]

    async def test_personal_data_model_serialisation(self) -> None:
        """Test personal data model serialisation"""
        personal_data_model = DataAgreementPersonalDataModel(
            attribute_id="18038282-0eb8-4796-b0b5-fc57ac27c861",
            attribute_name="Name",
            attribute_sensitive=True,
            attribute_description="Name of the individual",
        )

        personal_data_dict = personal_data_model.serialize()

        assert personal_data_dict["attributeId"] == personal_data_model.attribute_id
        assert personal_data_dict["attributeName"] == personal_data_model.attribute_name

    async def test_personal_data_model_deserialisation(self) -> None:
        """Test personal data model deserialisation"""
        personal_data_json = {
            "attributeId": "18038282-0eb8-4796-b0b5-fc57ac27c861",
            "attributeName": "Name",
            "attributeSensitive": True,
            "attributeDescription": "Name of the individual",
        }

        personal_data_model: DataAgreementPersonalDataModel = (
            DataAgreementPersonalDataModel.deserialize(personal_data_json)
        )

        assert personal_data_model.attribute_id == personal_data_json["attributeId"]
        assert personal_data_model.attribute_name == personal_data_json["attributeName"]
        assert (
            personal_data_model.attribute_sensitive
            == personal_data_json["attributeSensitive"]
        )
        assert (
            personal_data_model.attribute_description
            == personal_data_json["attributeDescription"]
        )

    async def test_data_policy_serialisation(self):
        """Test data policy serialisation"""
        data_policy_model = DataAgreementDataPolicyModel(
            data_retention_period=365,
            policy_url="https://clarifyhealth.com/privacy-policy/",
            jurisdiction="EU",
            industry_sector="Healthcare",
            geographic_restriction="EU",
            storage_location="EU",
            third_party_data_sharing=False,
        )

        data_policy_dict = data_policy_model.serialize()

        assert (
            data_policy_dict["dataRetentionPeriod"]
            == data_policy_model.data_retention_period
        )
        assert data_policy_dict["policyUrl"] == data_policy_model.policy_url
        assert data_policy_dict["jurisdiction"] == data_policy_model.jurisdiction
        assert data_policy_dict["industrySector"] == data_policy_model.industry_sector
        assert (
            data_policy_dict["geographicRestriction"]
            == data_policy_model.geographic_restriction
        )
        assert data_policy_dict["storageLocation"] == data_policy_model.storage_location
        assert (
            data_policy_dict["thirdPartyDataSharing"]
            == data_policy_model.third_party_data_sharing
        )

    async def test_data_policy_deserialisation(self):
        """Test data policy deserialisation"""
        data_policy_dict = {
            "dataRetentionPeriod": 365,
            "policyUrl": "https://clarifyhealth.com/privacy-policy/",
            "jurisdiction": "EU",
            "industrySector": "Healthcare",
            "geographicRestriction": "EU",
            "storageLocation": "EU",
            "thirdPartyDataSharing": False,
        }

        data_policy_model = DataAgreementDataPolicyModel.deserialize(data_policy_dict)

        assert (
            data_policy_dict["dataRetentionPeriod"]
            == data_policy_model.data_retention_period
        )
        assert data_policy_dict["policyUrl"] == data_policy_model.policy_url
        assert data_policy_dict["jurisdiction"] == data_policy_model.jurisdiction
        assert data_policy_dict["industrySector"] == data_policy_model.industry_sector
        assert (
            data_policy_dict["geographicRestriction"]
            == data_policy_model.geographic_restriction
        )
        assert data_policy_dict["storageLocation"] == data_policy_model.storage_location
        assert (
            data_policy_dict["thirdPartyDataSharing"]
            == data_policy_model.third_party_data_sharing
        )

    async def test_data_agreement_serialisation(self):
        """Test data agreement serialisation"""

        data_agreement_model = DataAgreementModel(
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
        )

        data_agreement_dict = data_agreement_model.serialize()

        assert data_agreement_model.version == data_agreement_dict["version"]
        assert (
            data_agreement_model.data_controller_name
            == data_agreement_dict["dataControllerName"]
        )
        assert len(data_agreement_model.personal_data) == 1
        assert (
            data_agreement_model.data_policy.data_retention_period
            == data_agreement_dict["dataPolicy"]["dataRetentionPeriod"]
        )

    async def test_data_agreement_deserialisation(self):
        """Test data agreement deserialisation"""

        data_agreement_dict = {
            "@context": [
                "https://raw.githubusercontent.com/decentralised-dataexchange/data-exchange-agreements/main/interface-specs/jsonld/contexts/dexa-context.jsonld",
                "https://w3id.org/security/v2",
            ],
            "@id": "ea046a85-d460-44ab-9369-ed71f8abf3ba",
            "@type": ["DataAgreement"],
            "version": "1.0.0",
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
                    "attributeId": "fbcd8bd5-7706-4042-8fd8-04b7f78e8adf",
                    "attributeName": "Name",
                    "attributeSensitive": True,
                    "attributeDescription": "Name of the individual",
                }
            ],
            "dpia": {
                "dpiaDate": "2011-10-05T14:48:00.000Z",
                "dpiaSummaryUrl": "https://org.com/dpia_results.html",
            },
        }

        data_agreement_model = DataAgreementModel.deserialize(data_agreement_dict)

        assert data_agreement_model.version == data_agreement_dict["version"]
        assert (
            data_agreement_model.data_controller_name
            == data_agreement_dict["dataControllerName"]
        )
        assert len(data_agreement_model.personal_data) == 1
        assert (
            data_agreement_model.data_policy.data_retention_period
            == data_agreement_dict["dataPolicy"]["dataRetentionPeriod"]
        )
