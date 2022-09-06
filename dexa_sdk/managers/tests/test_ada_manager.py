from asynctest import TestCase as AsyncTestCase
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.storage.basic import BasicStorage
from ..ada_manager import V2ADAManager


class TestPersonalDataRecord(AsyncTestCase):
    """Test personal data record"""

    def setUp(self):
        self.storage = BasicStorage()
        self.context = InjectionContext()
        self.context.injector.bind_instance(BaseStorage, self.storage)
        self.manager = V2ADAManager(self.context)

    async def test_create_and_store_data_agreement_template_in_wallet(self):
        """Test create and store data agreement template in wallet
        """

        da = {
            "language": "en",
            "dataControllerName": "Happy Shopping AB",
            "dataControllerUrl": "https://www.happyshopping.com",
            "dataPolicy": {
                "policyUrl": "https://happyshoping.com/privacy-policy/",
                "jurisdiction": "Sweden",
                "industrySector": "Retail",
                "dataRetentionPeriod": 30,
                "geographicRestriction": "Europe",
                "storageLocation": "Europe",
                "thirdPartyDataSharing": False
            },
            "purpose": "Customized shopping experience",
            "purposeDescription": "Collecting user data.",
            "lawfulBasis": "consent",
            "methodOfUse": "data-using-service",
            "personalData": [
                {
                    "attributeName": "Name",
                    "attributeSensitive": True,
                    "attributeCategory": "Name",
                    "attributeDescription": "Name of the individual",
                    "restrictions": [
                        {
                            "schemaId": "schema:1",
                            "credDefId": "cred:1"
                        }
                    ]
                }
            ],
            "dpia": {
                "dpiaDate": "2021-05-08T08:41:59+0000",
                "dpiaSummaryUrl": "https://org.com/dpia_results.html"
            }
        }

        record = await self.manager.create_and_store_da_template_in_wallet(
            data_agreement=da,
            publish_flag=True
        )

        assert record.method_of_use == record.data_agreement.get("methodOfUse")

        pd_records = await record.fetch_personal_data_records(self.context)

        assert len(pd_records) == 1
