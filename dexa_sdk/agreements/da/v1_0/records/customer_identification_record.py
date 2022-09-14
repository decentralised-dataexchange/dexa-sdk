from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from dexa_sdk.agreements.da.v1_0.records.da_template_record import (
    DataAgreementTemplateRecord,
)
from marshmallow import EXCLUDE, fields


class CustomerIdentificationRecord(BaseRecord):
    """Customer identification record."""

    class Meta:
        # Schema class
        schema_class = "CustomerIdentificationRecordSchema"

    # Record type
    RECORD_TYPE = "customer_identification_record"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = None

    # Record tags
    TAG_NAMES = {"~da_template_id"}

    def __init__(
        self, *, id: str = None, state: str = None, da_template_id: str = None, **kwargs
    ):
        # Pass the identifier and state to the parent class.
        super().__init__(id, state, **kwargs)

        # Set record attributes.
        self.da_template_id = da_template_id

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {prop: getattr(self, prop) for prop in ("state", "da_template_id")}

    @classmethod
    async def create_or_update_record(
        cls, context: InjectionContext, template_id: str
    ) -> "CustomerIdentificationRecord":
        """Create or update record.

        Args:
            context (InjectionContext): Injection context to be used.
            template_id (str): Template ID.
        """
        # Fetch data agreement template by id.
        da_template_record = (
            await DataAgreementTemplateRecord.latest_published_template_by_id(
                context, template_id
            )
        )

        # Validate DA method of use is data-source.
        assert (
            da_template_record.method_of_use
            == DataAgreementTemplateRecord.METHOD_OF_USE_DATA_SOURCE
        ), "Method of use must be data-source."

        # Search for existing customer identification record.
        records = await cls.query(context, {})

        if records:
            # Update existing record.
            record: CustomerIdentificationRecord = records[0]
            record.da_template_id = da_template_record.template_id
        else:
            # Create a new record.
            record = CustomerIdentificationRecord(
                da_template_id=da_template_record.template_id
            )

        await record.save(context)

        return record

    async def data_agreement_template_record(
        self, context: InjectionContext
    ) -> DataAgreementTemplateRecord:
        """Get data agreement template record.

        Args:
            context (InjectionContext): Injection context to be used.

        Returns:
            DataAgreementTemplateRecord: Data agreement template record.
        """
        record = await DataAgreementTemplateRecord.latest_published_template_by_id(
            context, self.da_template_id
        )

        return record


class CustomerIdentificationRecordSchema(BaseRecordSchema):
    """Customer identification record schema"""

    class Meta:
        # Model class
        model_class = CustomerIdentificationRecord

        # Unknown fields are excluded
        unknown = EXCLUDE

    da_template_id = fields.Str()
