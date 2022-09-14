import typing

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.messaging.valid import UUIDFour
from dexa_sdk.agreements.da.v1_0.models.da_models import (
    DataAgreementPersonalDataModel,
    DataAgreementPersonalDataRestrictionModel,
)
from dexa_sdk.utils import bump_major_for_semver_string
from marshmallow import EXCLUDE, fields


class PersonalDataRecord(BaseRecord):
    """Personal data record to be persisted in the storage"""

    class Meta:
        # Schema class
        schema_class = "PersonalDataRecordSchema"

    # Record type
    RECORD_TYPE = "personal_data"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = None

    # Record tags
    TAG_NAMES = {"~data_agreement_template_id", "~data_agreement_template_version"}

    def __init__(
        self,
        *,
        id: str = None,
        data_agreement_template_id: str = None,
        data_agreement_template_version: str = None,
        attribute_name: str = None,
        attribute_sensitive: str = None,
        attribute_category: dict = None,
        attribute_description: str = "false",
        restrictions: typing.List[dict] = None,
        **kwargs
    ):
        """Initialise personal data record

        Args:
            id (str, optional): Personal data identifier. Defaults to None.
            data_agreement_template_id (str, optional): Data agreement template identifier.
                Defaults to None.
            data_agreement_template_version (str, optional): Data agreement template version.
                Defaults to None.
            attribute_name (str, optional): Attribute name. Defaults to None.
            attribute_sensitive (str, optional): Attribute sensitive. Defaults to None.
            attribute_category (dict, optional): Attribute category. Defaults to None.
            attribute_description (str, optional): Attribute description. Defaults to "false".
            restrictions (typing.List[dict], optional): Attribute restrictions. Defaults to None.
        """

        # Pass identifier to parent class
        super().__init__(id, **kwargs)

        if not data_agreement_template_id:
            raise TypeError("Data agreement template identifier is not provided")

        # Set the record attributes
        self.data_agreement_template_id = data_agreement_template_id
        self.data_agreement_template_version = data_agreement_template_version
        self.attribute_name = attribute_name
        self.attribute_sensitive = attribute_sensitive
        self.attribute_category = attribute_category
        self.attribute_description = attribute_description
        self.restrictions = restrictions

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "data_agreement_template_id",
                "data_agreement_template_version",
                "attribute_name",
                "attribute_sensitive",
                "attribute_category",
                "attribute_description",
                "restrictions",
            )
        }

    @property
    def attribute_id(self):
        """Attribute identifier"""
        return self._id

    @classmethod
    async def list_by_template_id(
        cls, context: InjectionContext, template_id: str, template_version: str
    ) -> typing.List["PersonalDataRecord"]:
        """List by template id and template version

        Returns:
            records (typing.List[PersonalDataRecord]): personal datas
        """
        tag_filter = {
            "data_agreement_template_id": template_id,
            "data_agreement_template_version": template_version,
        }

        records: typing.List[PersonalDataRecord] = await cls.query(context, tag_filter)

        return records

    @classmethod
    async def batch_update_by_da_template_id(
        cls,
        context: InjectionContext,
        template_id: str,
        template_version: str,
        pds: typing.List[dict],
    ) -> typing.List["PersonalDataRecord"]:
        """Batch update by DA template id

        Args:
            template_id (str): template id
            pds (typing.List[PersonalDataRecord]): personal datas
        """

        template_version = bump_major_for_semver_string(template_version)

        # Then no update is performed.
        if len(pds) == 0:
            return []

        records = []
        for pd in pds:

            # Create new entry with updated version.
            record = PersonalDataRecord(
                data_agreement_template_id=template_id,
                data_agreement_template_version=template_version,
                attribute_name=pd.get("attributeName"),
                attribute_sensitive=pd.get("attributeSensitive"),
                attribute_category=pd.get("attributeCategory"),
                attribute_description=pd.get("attributeDescription"),
                restrictions=pd.get("restrictions"),
            )

            await record.save(context)

            records.append(record)

        return records

    def convert_record_to_pd_model(self) -> DataAgreementPersonalDataModel:
        """Convert record to personal data model

        Returns:
            DataAgreementPersonalDataModel: Data agreement personal data model
        """

        pd_model = DataAgreementPersonalDataModel(
            attribute_id=self.attribute_id,
            attribute_name=self.attribute_name,
            attribute_sensitive=self.attribute_sensitive,
            attribute_category=self.attribute_category,
            attribute_description=self.attribute_description,
        )

        restriction_models = []

        if self.restrictions:
            for restriction in self.restrictions:

                restriction_model = DataAgreementPersonalDataRestrictionModel(
                    schema_id=restriction.get("schemaId"),
                    cred_def_id=restriction.get("credDefId"),
                )

                restriction_models.append(restriction_model)

        pd_model.restrictions = restriction_models

        return pd_model

    @classmethod
    async def build_and_save_record_from_pd_model(
        cls,
        context: InjectionContext,
        template_id: str,
        template_version: str,
        pd_model: DataAgreementPersonalDataModel,
    ) -> "PersonalDataRecord":
        """Build personal data record from personal data model

        Args:
            pd_model (DataAgreementPersonalDataModel): Personal data model

        Returns:
            PersonalDataRecord: Personal data record
        """

        pd_record = PersonalDataRecord(
            id=pd_model.attribute_id,
            data_agreement_template_id=template_id,
            data_agreement_template_version=template_version,
            attribute_name=pd_model.attribute_name,
            attribute_sensitive=pd_model.attribute_sensitive,
            attribute_category=pd_model.attribute_category,
            attribute_description=pd_model.attribute_description,
        )

        restrictions = []

        if pd_model.restrictions:
            for restriction in pd_model.restrictions:
                restrictions.append(restriction.serialize())

        pd_record.restrictions = restrictions

        await pd_record.save(context)

        return pd_record


class PersonalDataRecordSchema(BaseRecordSchema):
    """Personal data record schema"""

    class Meta:
        # Model class
        model_class = PersonalDataRecord

        # Unknown fields are excluded
        unknown = EXCLUDE

    # Attribute identifier
    attribute_id = fields.Str(required=True, example=UUIDFour.EXAMPLE)

    # Data agreement template identifier
    data_agreement_template_id = fields.Str(required=True, example=UUIDFour.EXAMPLE)

    # Data agreement template version
    data_agreement_template_version = fields.Str(
        required=True,
    )

    # Attribute name
    attribute_name = fields.Str(required=True)

    # Attribute sensitive
    attribute_sensitive = fields.Bool(required=False)

    # Attribute category
    attribute_category = fields.Str(required=False)

    # Attribute description
    attribute_description = fields.Str(required=False)

    # Restrictions
    restrictions = fields.List(
        fields.Dict(keys=fields.Str, values=fields.Str), required=False
    )
