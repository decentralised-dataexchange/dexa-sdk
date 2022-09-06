from asynctest import TestCase as AsyncTestCase
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.storage.basic import BasicStorage
from ..personal_data_record import PersonalDataRecord
from ...models.da_models import DataAgreementPersonalDataModel


class TestPersonalDataRecord(AsyncTestCase):
    """Test personal data record"""

    def setUp(self):
        self.storage = BasicStorage()
        self.context = InjectionContext()
        self.context.injector.bind_instance(BaseStorage, self.storage)
        self.test_record = PersonalDataRecord(
            data_agreement_template_id="urn:uuid:",
            data_agreement_template_version="1.0.0",
            attribute_name="Name",
            attribute_description="Name of the individual",
            restrictions=[
                {
                    "schemaId": "schema:id",
                    "credDefId": "cred:id"
                }
            ]
        )

    async def test_save_retrieve_compare(self):
        """Test save retrieve compare"""
        record = self.test_record
        record_id = await record.save(self.context)
        fetched = await PersonalDataRecord.retrieve_by_id(self.context, record_id)

        assert fetched and fetched == record

        bad_record = PersonalDataRecord(
            data_agreement_template_id="urn:uuid:",
            attribute_name="Age",
        )
        assert bad_record != record

    async def test_batch_update_by_da_template_id(self):
        """Test batch update by da template id"""

        pd1 = PersonalDataRecord(
            data_agreement_template_id="1",
            data_agreement_template_version="1.0.0",
            attribute_name="Name",
            attribute_description="Name of the individual",
            restrictions=[
                {
                    "schemaId": "schema:id",
                    "credDefId": "cred:id"
                }
            ]
        )

        pd1_id = await pd1.save(self.context)

        pd2 = PersonalDataRecord(
            data_agreement_template_id="1",
            data_agreement_template_version="1.0.0",
            attribute_name="Organisation name",
            attribute_description="Name of the organisation",
            restrictions=[
                {
                    "schemaId": "schema:id",
                    "credDefId": "cred:id"
                }
            ]
        )

        pd2_id = await pd2.save(self.context)

        pds = await PersonalDataRecord.list_by_template_id(self.context, template_id="1", template_version="1.0.0")
        assert len(pds) == 2

        to_be_updated_pds = [
            {
                "attributeId": pd1_id,
                "attributeName": "Age",
                "attributeDescription": "Age of the individual"
            },
            {
                "attributeName": "Designation",
                "attributeDescription": "Designation of the individual"
            }
        ]

        updated_pds = await PersonalDataRecord.batch_update_by_da_template_id(
            context=self.context,
            template_id="1",
            template_version="1.0.0",
            pds=to_be_updated_pds
        )

        assert len(updated_pds) == 2

        pds = await PersonalDataRecord.list_by_template_id(self.context, template_id="1", template_version="1.0.0")
        assert len(pds) == 2

    async def test_convert_record_to_pd_model(self) -> None:
        """Test convert record to personal data model"""

        pd1 = PersonalDataRecord(
            data_agreement_template_id="1",
            attribute_name="Name",
            attribute_description="Name of the individual"
        )

        await pd1.save(self.context)

        pd_model = pd1.convert_record_to_pd_model()

        assert pd_model.attribute_id == pd1.attribute_id
        assert pd_model.attribute_description == pd1.attribute_description

    async def test_build_and_save_record_from_pd_model(self):
        """Build and save record from personal data model
        """

        pd_model = DataAgreementPersonalDataModel(
            attribute_id=None,
            attribute_name="Name"
        )

        pd_record = await PersonalDataRecord.build_and_save_record_from_pd_model(
            context=self.context,
            template_id="1",
            template_version="1.0.0",
            pd_model=pd_model
        )

        assert pd_record.attribute_id is not None
