import typing
import uuid
import semver
from asynctest import TestCase as AsyncTestCase
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.storage.basic import BasicStorage
from ..da_template_record import DataAgreementTemplateRecord


class TestDATemplateRecord(AsyncTestCase):
    """Test data agreement template record"""

    def setUp(self):
        self.storage = BasicStorage()
        self.context = InjectionContext()
        self.context.injector.bind_instance(BaseStorage, self.storage)
        self.test_record = DataAgreementTemplateRecord(
            third_party_data_sharing="false",
            state=DataAgreementTemplateRecord.STATE_DEFINITION,
            method_of_use=DataAgreementTemplateRecord.METHOD_OF_USE_DATA_SOURCE,
            data_agreement={
                "@context": [
                    "https://raw.githubusercontent.com/decentralised-dataexchange/data-exchange-agreements/main/interface-specs/jsonld/contexts/dexa-context.jsonld",
                    "https://w3id.org/security/v2"
                ],
                "@id": "ea046a85-d460-44ab-9369-ed71f8abf3ba",
                "@type": [
                    "DataAgreement"
                ],
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
                    "thirdPartyDataSharing": False
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
                        "attributeDescription": "Name of the individual"
                    }
                ],
                "dpia": {
                    "dpiaDate": "2011-10-05T14:48:00.000Z",
                    "dpiaSummaryUrl": "https://org.com/dpia_results.html"
                }
            },
            template_id=str(uuid.uuid4())
        )

    async def test_save_retrieve_compare(self):
        """Test save retrieve compare"""
        record = self.test_record
        record_id = await record.save(self.context)
        fetched = await DataAgreementTemplateRecord.retrieve_by_id(self.context, record_id)
        assert fetched and fetched == record

        bad_record = DataAgreementTemplateRecord(
            state=DataAgreementTemplateRecord.STATE_PREPARATION,
            template_id=str(uuid.uuid4())
        )
        assert bad_record != record

    async def test_deleted_record(self):
        """Test deleted record"""
        record = self.test_record

        # Assert record is not deleted before saving to storage
        assert not record.is_deleted

        record_id = await record.save(self.context)
        fetched: DataAgreementTemplateRecord = \
            await DataAgreementTemplateRecord.retrieve_by_id(self.context, record_id)

        # Assert record is not deleted, after fetching from storage
        assert not fetched.is_deleted

        fetched._delete_flag = True

        # Assert record is deleted before saving to storage
        assert fetched.is_deleted

        # Save to storage
        update_record_id = await fetched.save(self.context)

        # Assert record id doesn't change on save.
        assert record_id == update_record_id

        fetched: DataAgreementTemplateRecord = \
            await DataAgreementTemplateRecord.retrieve_by_id(self.context, record_id)

        # Assert record is deleted after saving to storage
        assert fetched.is_deleted

    async def test_draft_record(self):
        """Test draft record"""
        record = self.test_record

        assert record.is_draft

        record._publish_flag = True

        assert not record.is_draft

        record_id = await record.save(self.context)
        fetched: DataAgreementTemplateRecord = \
            await DataAgreementTemplateRecord.retrieve_by_id(self.context, record_id)

        assert not fetched.is_draft

    async def test_record_upgrade(self):
        """Test record upgrade"""

        record = self.test_record
        record_id = await record.save(self.context)

        fetched: typing.List[DataAgreementTemplateRecord] = \
            await DataAgreementTemplateRecord.non_deleted_templates_by_id(
                self.context,
                record.template_id
        )

        assert fetched[0].is_latest_version

        fetched[0]._publish_flag = True
        fetched_id = await fetched[0].upgrade(self.context)

        assert record_id != fetched_id

        fetched_records: typing.List[DataAgreementTemplateRecord] = \
            await DataAgreementTemplateRecord.non_deleted_templates(self.context)

        assert len(fetched_records) == 2

        latest_version: DataAgreementTemplateRecord = \
            await DataAgreementTemplateRecord.latest_template_by_id(
                self.context,
                fetched[0].template_id
            )

        assert latest_version._id == fetched_id

        # Assert to check the version in data agreement has upgraded
        assert semver.compare(
            record.data_agreement.get("version"),
            latest_version.data_agreement.get("version")
        ) == -1

    async def test_publish(self) -> None:
        """Test publish"""
        record = self.test_record

        await record.publish_template(self.context)

        published_records: typing.List[DataAgreementTemplateRecord] = \
            await DataAgreementTemplateRecord.published_templates(self.context)

        assert published_records[0].is_published

    async def test_delete(self) -> None:
        """Test delete"""
        record = self.test_record

        await record.delete_template(self.context)

        deleted_records: typing.List[DataAgreementTemplateRecord] = \
            await DataAgreementTemplateRecord.query(
                self.context,
                {
                    "delete_flag": "true"
                }
        )

        assert deleted_records[0].is_deleted
