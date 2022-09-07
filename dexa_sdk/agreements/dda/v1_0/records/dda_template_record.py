import typing
from marshmallow import fields, validate, EXCLUDE
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.messaging.valid import UUIDFour
from aries_cloudagent.config.injection_context import InjectionContext
from mydata_did.v1_0.utils.util import bool_to_str, str_to_bool
from ..models.dda_models import (
    DataDisclosureAgreementModel,
    DDA_DEFAULT_CONTEXT,
    DDA_TYPE
)
from .....utils import bump_major_for_semver_string


class DataDisclosureAgreementTemplateRecord(BaseRecord):
    """Data disclosure agreement template record to be persisted in the storage"""

    class Meta:
        # Schema class
        schema_class = "DataDisclosureAgreementTemplateRecordSchema"

    # Record type
    RECORD_TYPE = "data_disclosure_agreement_template"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = None

    # Record tags
    TAG_NAMES = {
        "~template_id",
        "~template_version",
        "~industry_sector",
        "~delete_flag",
        "~publish_flag",
        "~latest_version_flag"
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
        data_disclosure_agreement: dict = None,
        industry_sector: str = None,
        publish_flag: str = "false",
        delete_flag: str = "false",
        latest_version_flag: str = "false",
        **kwargs
    ):
        """Instantiate data disclosure agreement template record.

        Args:
            id (str, optional): Record identifier. Defaults to None.
            template_id (str, optional): Template identifier. Defaults to None.
            template_version (str, optional): Template version. Defaults to None.
            state (str, optional): State. Defaults to None.
            data_disclosure_agreement (dict, optional): Data disclosure agreement. Defaults to None.
            industry_sector (str, optional): Industry sector. Defaults to None.
        """

        # Pass identifier and state to parent class
        super().__init__(id, state, **kwargs)

        if not template_id:
            raise TypeError(
                "Template identifier is not specified."
            )

        if not template_version:
            raise TypeError(
                "Template version is not specified."
            )

        # Set the record attributes
        self.template_id = template_id
        self.template_version = template_version
        self.state = state
        self.data_disclosure_agreement = data_disclosure_agreement
        self.industry_sector = industry_sector
        self.publish_flag = publish_flag
        self.latest_version_flag = latest_version_flag
        self.delete_flag = delete_flag

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "template_id",
                "template_version",
                "state",
                "data_disclosure_agreement",
                "industry_sector",
                "publish_flag",
                "latest_version_flag",
                "delete_flag"
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
    def is_latest_version(self) -> bool:
        """Check if the current record is latest version."""
        return self._latest_version_flag

    @property
    def is_draft(self) -> bool:
        """Check if data agreement is a draft."""
        return True if not self._publish_flag else False

    @property
    def dda_model(self) -> DataDisclosureAgreementModel:
        """Returns the Data Disclosure Agreement model.

        Returns:
            DataDisclosureAgreementModel: Data disclosure agreement model.
        """

        return DataDisclosureAgreementModel.deserialize(
            self.data_disclosure_agreement
        )

    @staticmethod
    def to_dda_model(dda: dict) -> DataDisclosureAgreementModel:
        """Returns the Data Disclosure Agreement model.

        Returns:
            DataDisclosureAgreementModel: Data disclosure agreement model.
        """

        return DataDisclosureAgreementModel.deserialize(dda)

    @classmethod
    async def latest_published_template_by_id(
        cls,
        context: InjectionContext,
        template_id: str,
    ) -> "DataDisclosureAgreementTemplateRecord":
        """Fetch latest published template by id.

        Args:
            context (InjectionContext): Injection context to use.
            template_id (str): DDA template id.

        Returns:
            DataDisclosureAgreementTemplateRecord: DDA template record.
        """

        tag_filter: dict = {
            "delete_flag": bool_to_str(False),
            "template_id": template_id,
            "latest_version_flag": bool_to_str(True),
            "publish_flag": bool_to_str(True)
        }

        fetched = await cls.query(
            context,
            tag_filter=tag_filter
        )

        return None if len(fetched) == 0 else fetched[0]

    @classmethod
    async def latest_template_by_id(
        cls,
        context: InjectionContext,
        template_id: str,
    ) -> "DataDisclosureAgreementTemplateRecord":
        """Fetch latest template by id.

        Args:
            context (InjectionContext): Injection context to use.
            template_id (str): DDA template id.

        Returns:
            DataDisclosureAgreementTemplateRecord: DDA template record.
        """

        tag_filter: dict = {
            "delete_flag": bool_to_str(False),
            "template_id": template_id,
            "latest_version_flag": bool_to_str(True)
        }

        fetched = await cls.query(
            context,
            tag_filter=tag_filter
        )

        return None if len(fetched) == 0 else fetched[0]

    @classmethod
    async def non_deleted_templates_by_id(
        cls,
        context: InjectionContext,
        template_id: str,
    ) -> typing.List["DataDisclosureAgreementTemplateRecord"]:
        """Fetch a non-deleted templates by id.

        Args:
            context (InjectionContext): Injection context to use.
            template_id (str): DDA template id.

        Returns:
            DataDisclosureAgreementTemplateRecord: DDA template records.
        """

        tag_filter: dict = {
            "delete_flag": bool_to_str(False),
            "template_id": template_id
        }

        fetched = await cls.query(
            context,
            tag_filter=tag_filter
        )

        return fetched

    @classmethod
    async def non_deleted_template_by_id(
        cls,
        context: InjectionContext,
        template_id: str
    ) -> typing.List["DataDisclosureAgreementTemplateRecord"]:
        """Fetch non deleted template by id.

        Returns:
            DataDisclosureAgreementTemplateRecord: Template record
        """

        tag_filter: dict = {
            "latest_version_flag": bool_to_str(True),
            "delete_flag": bool_to_str(False),
            "template_id": template_id
        }

        return await cls.query(
            context,
            tag_filter=tag_filter,
        )

    @classmethod
    async def non_deleted_templates(
        cls,
        context: InjectionContext
    ) -> typing.List["DataDisclosureAgreementTemplateRecord"]:
        """Fetch all non-deleted agreements.

        Returns:
            DataDisclosureAgreementTemplateRecord: List of template records
        """

        tag_filter: dict = {
            "delete_flag": bool_to_str(False)
        }

        return await cls.query(
            context,
            tag_filter=tag_filter,
        )

    async def upgrade(
        self,
        context: InjectionContext,
        dda: dict,
        publish_flag: str
    ) -> "DataDisclosureAgreementTemplateRecord":
        """Upgrade DDA to next version.

        Args:
            context (InjectionContext): Injection context to be used.
            dda (dict): DDA
            publish_flag (str): Publish flag.

        Returns:
            DataDisclosureAgreementTemplateRecord: DDA template record.
        """

        # DDA model from existing template.
        existing_dda_model = self.dda_model

        # Adding the necessary fields to updated dda.
        # This is necessary for deserialisation.
        # Bump up the version
        template_version = bump_major_for_semver_string(self.template_version)
        # Provide defaults in the to be updated template.
        dda.update({"@context": DDA_DEFAULT_CONTEXT})
        dda.update({"@type": DDA_TYPE})
        dda.update({"@id": self.template_id})
        dda.update({"version": template_version})
        # Update the controller did.
        dda["dataController"].update({"did": existing_dda_model.data_controller.did})

        # DDA model from update.
        dda_model = DataDisclosureAgreementTemplateRecord.to_dda_model(dda)

        # Checking restrictions
        assert dda_model.data_sharing_restrictions.industry_sector == \
            existing_dda_model.data_sharing_restrictions.industry_sector, \
            "Industry cannot be updated."

        # Updating old version template
        self._latest_version_flag = False
        await self.save(context)

        # Create the upgraded DDA template
        dda_template = DataDisclosureAgreementTemplateRecord(
            template_id=self.template_id,
            template_version=template_version,
            state=self.state,
            data_disclosure_agreement=dda,
            industry_sector=dda_model.data_sharing_restrictions.industry_sector.lower(),
            publish_flag=publish_flag,
            delete_flag=bool_to_str(False),
            latest_version_flag=bool_to_str(True)
        )

        await dda_template.save(context)

        return dda_template

    async def delete_template(self, context: InjectionContext):
        """Delete template record."""
        self._delete_flag = True
        await self.save(context)

    async def publish_template(self, context: InjectionContext):
        """Publish template record"""
        self._publish_flag = True
        await self.save(context)


class DataDisclosureAgreementTemplateRecordSchema(BaseRecordSchema):
    """Data agreement instance record schema"""

    class Meta:
        # Model class
        model_class = DataDisclosureAgreementTemplateRecord

        # Unknown fields are excluded
        unknown = EXCLUDE

    # Data disclosure agreement template identifier
    template_id = fields.Str(
        required=True,
        example=UUIDFour.EXAMPLE
    )

    # Data disclosure agreement template version
    template_version = fields.Str(
        required=False
    )

    # State of the data agreement.
    state = fields.Str(
        required=True,
        example=DataDisclosureAgreementTemplateRecord.STATE_PREPARATION,
        validate=validate.OneOf(
            [
                DataDisclosureAgreementTemplateRecord.STATE_DEFINITION,
                DataDisclosureAgreementTemplateRecord.STATE_PREPARATION,
            ]
        )
    )

    # Data disclosure agreement
    data_disclosure_agreement = fields.Dict(required=True)

    # Industry sector
    industry_sector = fields.Str(required=False)

    # Is published or not
    publish_flag = fields.Str(
        required=True,
        example="false",
        validate=validate.OneOf(
            [
                "true",
                "false",
            ]
        )
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
        )
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
        )
    )
