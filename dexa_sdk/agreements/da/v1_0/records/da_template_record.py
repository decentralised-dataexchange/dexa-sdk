import typing

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.messaging.valid import UUIDFour
from dexa_sdk.agreements.da.v1_0.models.da_models import DataAgreementModel
from dexa_sdk.agreements.da.v1_0.records.personal_data_record import PersonalDataRecord
from dexa_sdk.utils import bump_major_for_semver_string
from loguru import logger
from marshmallow import EXCLUDE, fields, validate
from mydata_did.v1_0.utils.util import bool_to_str, str_to_bool


class DataAgreementTemplateRecord(BaseRecord):
    """Data agreement template record to be persisted in the storage"""

    class Meta:
        # Schema class
        schema_class = "DataAgreementTemplateRecordSchema"

    # Record type
    RECORD_TYPE = "data_agreement_template"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = None

    # Record tags
    TAG_NAMES = {
        "~template_id",
        "~template_version",
        "~method_of_use",
        "~publish_flag",
        "~delete_flag",
        "~schema_id",
        "~cred_def_id",
        "~existing_schema_flag",
        "~latest_version_flag",
        "~third_party_data_sharing",
    }

    # States of the data agreement.
    STATE_DEFINITION = "DEFINITION"
    STATE_PREPARATION = "PREPARATION"
    STATE_CAPTURE = "CAPTURE"
    STATE_PROOF = "PROOF"

    METHOD_OF_USE_DATA_SOURCE = "data-source"
    METHOD_OF_USE_DATA_USING_SERVICE = "data-using-service"

    def __init__(
        self,
        *,
        id: str = None,
        template_id: str = None,
        template_version: str = None,
        state: str = None,
        method_of_use: str = None,
        data_agreement: dict = None,
        publish_flag: str = "false",
        delete_flag: str = "false",
        schema_id: str = None,
        cred_def_id: str = None,
        presentation_request: dict = None,
        existing_schema_flag: str = "false",
        latest_version_flag: str = "true",
        third_party_data_sharing: str = "false",
        **kwargs,
    ):
        """Initialise data agreement template record

        Args:
            id (str, optional): Identifier of record. Defaults to None.
            template_id (str, optional): Identifier for the template. Default to None.
            template_version (str, optional): Version for the template. Default to None.
            state (str, optional): State of the data agreeement template. Defaults to None.
            method_of_use (str, optional): Method of use. Defaults to None.
            data_agreement (dict, optional): Data agreement template. Defaults to None.
            publish_flag (str, optional): Published or not. Defaults to "false".
            delete_flag (str, optional): Deleted or not. Defaults to "false".
            schema_id (str, optional): Schema identifier. Defaults to None.
            cred_def_id (str, optional): Credential definition identifier. Defaults to None.
            presentation_request (dict, optional): Presentation request. Defaults to None.
            existing_schema_flag (str, optional): Is existing schema or not. Defaults to "false".
            latest_version_flag (str, optional): Latest version of record or not.
                Defaults to "false".
        """

        # Pass identifier and state to parent class
        super().__init__(id, state, **kwargs)

        if not template_id:
            raise TypeError("Template identifier is not specified.")

        # Set the record attributes
        self.template_id = template_id
        self.template_version = template_version
        self.method_of_use = method_of_use
        self.state = state
        self.data_agreement = data_agreement
        self.publish_flag = publish_flag
        self.delete_flag = delete_flag
        self.schema_id = schema_id
        self.cred_def_id = cred_def_id
        self.presentation_request = presentation_request
        self.existing_schema_flag = existing_schema_flag
        self.latest_version_flag = latest_version_flag
        self.third_party_data_sharing = third_party_data_sharing

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "template_id",
                "template_version",
                "method_of_use",
                "state",
                "data_agreement",
                "publish_flag",
                "delete_flag",
                "schema_id",
                "cred_def_id",
                "presentation_request",
                "existing_schema_flag",
                "latest_version_flag",
                "third_party_data_sharing",
            )
        }

    @property
    def _publish_flag(self) -> bool:
        """Accessor for publish_flag."""
        return str_to_bool(self.publish_flag)

    @_publish_flag.setter
    def _publish_flag(self, value: bool) -> None:
        """Setter for publish_flag."""
        self.publish_flag = bool_to_str(value)

    @property
    def _delete_flag(self) -> bool:
        """Accessor for delete_flag."""
        return str_to_bool(self.delete_flag)

    @_delete_flag.setter
    def _delete_flag(self, value: bool) -> None:
        """Setter for delete_flag."""
        self.delete_flag = bool_to_str(value)

    @property
    def _existing_schema_flag(self) -> bool:
        """Accessor for existing_schema_flag."""
        return str_to_bool(self.existing_schema_flag)

    @_existing_schema_flag.setter
    def _existing_schema_flag(self, value: bool) -> None:
        """Setter for existing_schema_flag."""
        self.existing_schema_flag = bool_to_str(value)

    @property
    def _latest_version_flag(self) -> bool:
        """Accessor for latest_version_flag."""
        return str_to_bool(self.latest_version_flag)

    @_latest_version_flag.setter
    def _latest_version_flag(self, value: bool) -> None:
        """Setter for latest_version_flag."""
        self.latest_version_flag = bool_to_str(value)

    @property
    def is_published(self) -> bool:
        """Check if data agreement record is published."""
        return self._publish_flag

    @property
    def is_deleted(self) -> bool:
        """Check if data agreemnent is deleted."""
        return self._delete_flag

    @property
    def is_draft(self) -> bool:
        """Check if data agreement is a draft."""
        return True if not self._publish_flag else False

    @property
    def is_existing_schema(self) -> bool:
        """Check if the schema provided was existing or not."""
        return self._existing_schema_flag

    @property
    def is_latest_version(self) -> bool:
        """Check if the current record is latest version."""
        return self._latest_version_flag

    @classmethod
    async def latest_published_template_by_id(
        cls,
        context: InjectionContext,
        template_id: str,
    ) -> "DataAgreementTemplateRecord":
        """Fetch latest published template by id.

        Args:
            context (InjectionContext): Injection context to use.
            template_id (str): Data agreement template id.

        Returns:
            DataAgreementTemplateRecord: Data agreement template record.
        """

        tag_filter: dict = {
            "delete_flag": bool_to_str(False),
            "template_id": template_id,
            "latest_version_flag": bool_to_str(True),
            "publish_flag": bool_to_str(True),
        }

        fetched = await cls.query(context, tag_filter=tag_filter)

        return None if len(fetched) == 0 else fetched[0]

    @classmethod
    async def latest_template_by_id(
        cls,
        context: InjectionContext,
        template_id: str,
    ) -> "DataAgreementTemplateRecord":
        """Fetch latest template by id.

        Args:
            context (InjectionContext): Injection context to use.
            template_id (str): Data agreement template id.

        Returns:
            DataAgreementTemplateRecord: Data agreement template record.
        """

        tag_filter: dict = {
            "delete_flag": bool_to_str(False),
            "template_id": template_id,
            "latest_version_flag": bool_to_str(True),
        }

        fetched = await cls.query(context, tag_filter=tag_filter)

        return None if len(fetched) == 0 else fetched[0]

    @classmethod
    async def non_deleted_templates_by_id(
        cls,
        context: InjectionContext,
        template_id: str,
    ) -> typing.List["DataAgreementTemplateRecord"]:
        """Fetch a non-deleted templates by id.

        Args:
            context (InjectionContext): Injection context to use.
            template_id (str): Data agreement template id.

        Returns:
            DataAgreementTemplateRecord: Data agreement template record.
        """

        tag_filter: dict = {
            "delete_flag": bool_to_str(False),
            "template_id": template_id,
        }

        fetched = await cls.query(context, tag_filter=tag_filter)

        return fetched

    @classmethod
    async def non_deleted_template_by_id(
        cls, context: InjectionContext, template_id: str
    ) -> typing.List["DataAgreementTemplateRecord"]:
        """Fetch non deleted template by id.

        Returns:
            DataAgreementTemplateRecord: Template record
        """

        tag_filter: dict = {
            "latest_version_flag": bool_to_str(True),
            "delete_flag": bool_to_str(False),
            "template_id": template_id,
        }

        return await cls.query(
            context,
            tag_filter=tag_filter,
        )

    @classmethod
    async def non_deleted_templates(
        cls, context: InjectionContext
    ) -> typing.List["DataAgreementTemplateRecord"]:
        """Fetch all non-deleted agreements.

        Returns:
            DataAgreementTemplateRecord: List of template records
        """

        tag_filter: dict = {"delete_flag": bool_to_str(False)}

        return await cls.query(
            context,
            tag_filter=tag_filter,
        )

    async def upgrade(self, context: InjectionContext, **kwargs) -> str:
        """Upgrade the data agreement template to next version.

        Args:
            context (InjectionContext): Injection context to be used.

        Returns:
            str: Returns the record identifier of the upgraded record.
        """

        # Fetch the previous record
        previous_record: DataAgreementTemplateRecord = (
            await DataAgreementTemplateRecord.latest_template_by_id(
                context, self.template_id
            )
        )

        assert previous_record, "Atleast 1 previous record must be present"

        # Mark the previous record as not the latest
        previous_record._latest_version_flag = False
        await previous_record.save(context)

        # Bump the version of data agreement.
        previous_data_agreement = previous_record.data_agreement
        previous_version = previous_data_agreement["version"]
        template_version = bump_major_for_semver_string(previous_version)
        logger.info(
            (
                f"Data agreement template version is bumped from"
                f" {previous_version} to {template_version}"
            )
        )
        self.data_agreement.update({"version": template_version})

        # Save as new record to the storage
        self._id = None
        self.template_version = template_version
        await self.save(context=context, **kwargs)

        return self

    @classmethod
    async def published_templates(
        cls, context: InjectionContext
    ) -> typing.List["DataAgreementTemplateRecord"]:
        """Fetch all published templates (not-deleted)

        Returns:
            DataAgreementTemplateRecord: List of template records
        """

        tag_filter: dict = {
            "delete_flag": bool_to_str(False),
            "publish_flag": bool_to_str(True),
        }

        return await cls.query(context, tag_filter=tag_filter)

    async def publish_template(self, context: InjectionContext, **kwargs) -> str:
        """Publish the data agreement template

        Args:
            context (InjectionContext): Injection context to be used.

        Returns:
            str: Returns the record identifier for the published record.
        """
        self._publish_flag = True
        return await self.save(context=context, **kwargs)

    async def delete_template(self, context: InjectionContext, **kwargs) -> str:
        """Delete the data agreement template

        Args:
            context (InjectionContext): Injection context to be used.

        Returns:
            str: Returns the record identifier for deleted record.
        """
        self._delete_flag = True
        return await self.save(context=context, **kwargs)

    async def fetch_personal_data_records(
        self, context: InjectionContext
    ) -> typing.List[PersonalDataRecord]:
        """Fetch personal data records

        Args:
            context (InjectionContext): Injection context to be used.

        Returns:
            typing.List[PersonalDataRecord]: Personal data records
        """

        logger.info(
            (
                f"Fetching personal data records for DA template with "
                f"id:{self.template_id} and version:{self.template_version}"
            )
        )

        return await PersonalDataRecord.list_by_template_id(
            context, self.template_id, self.template_version
        )

    @property
    def data_agreement_model(self) -> DataAgreementModel:
        """Accessor for data agreement as model."""
        return DataAgreementModel.deserialize(self.data_agreement)


class DataAgreementTemplateRecordSchema(BaseRecordSchema):
    """Data agreement template record schema"""

    class Meta:
        # Model class
        model_class = DataAgreementTemplateRecord

        # Unknown fields are excluded
        unknown = EXCLUDE

    # Data agreement template identifier
    template_id = fields.Str(required=True, example=UUIDFour.EXAMPLE)

    # Data agreement template version
    template_version = fields.Str(required=False)

    # State of the data agreement.
    state = fields.Str(
        required=True,
        example=DataAgreementTemplateRecord.STATE_PREPARATION,
        validate=validate.OneOf(
            [
                DataAgreementTemplateRecord.STATE_DEFINITION,
                DataAgreementTemplateRecord.STATE_PREPARATION,
            ]
        ),
    )

    # Method of use for the data agreement.
    method_of_use = fields.Str(
        required=True,
        example="data-source",
        validate=validate.OneOf(
            [
                DataAgreementTemplateRecord.METHOD_OF_USE_DATA_SOURCE,
                DataAgreementTemplateRecord.METHOD_OF_USE_DATA_USING_SERVICE,
            ]
        ),
    )

    # Data agreement
    data_agreement = fields.Dict(required=True)

    # Schema identifier
    schema_id = fields.Str(
        required=True, example="WgWxqztrNooG92RXvxSTWv:2:schema_name:1.0"
    )

    # Credential definition identifier
    cred_def_id = fields.Str(
        required=True, example="WgWxqztrNooG92RXvxSTWv:3:CL:20:tag"
    )

    # Presentation request
    presentation_request = fields.Dict(
        required=True,
    )

    # Is published or not
    publish_flag = fields.Str(
        required=True,
        example="false",
        validate=validate.OneOf(
            [
                "true",
                "false",
            ]
        ),
    )

    # Is deleted or not
    delete_flag = fields.Str(
        required=True,
        example="false",
        validate=validate.OneOf(
            [
                "true",
                "false",
            ]
        ),
    )

    # Is existing schema or not
    existing_schema_flag = fields.Str(
        required=True,
        example="false",
        validate=validate.OneOf(
            [
                "true",
                "false",
            ]
        ),
    )

    # Latest version of the record or not.
    latest_version_flag = fields.Str(
        required=True,
        example="false",
        validate=validate.OneOf(
            [
                "true",
                "false",
            ]
        ),
    )

    # Third party data sharing
    third_party_data_sharing = fields.Str(
        required=True,
        example="false",
        validate=validate.OneOf(
            [
                "true",
                "false",
            ]
        ),
    )
