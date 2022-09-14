from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from dexa_sdk.agreements.dda.v1_0.models.dda_models import DataDisclosureAgreementModel
from marshmallow import fields


class PublishedDDATemplateRecord(BaseRecord):
    """Published DDA template record."""

    class Meta:
        schema_class = "PublishedDDATemplateRecordSchema"

    # Record type
    RECORD_TYPE = "published_dda_template_record"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Record tags
    TAG_NAMES = {"~connection_id", "~template_id", "~industry_sector", "~state"}

    def __init__(
        self,
        id: str = None,
        connection_id: str = None,
        template_id: str = None,
        industry_sector: str = None,
        dda: dict = None,
        connection_url: str = None,
        state: str = None,
        **kwargs
    ):
        # Pass the identifier and state to parent class
        super().__init__(id, state, **kwargs)

        self.connection_id = connection_id
        self.dda = dda
        self.template_id = template_id
        self.industry_sector = industry_sector
        self.connection_url = connection_url

    @property
    def request_id(self) -> str:
        """Accessor for record identifier"""
        return self._id

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "connection_id",
                "dda",
                "template_id",
                "industry_sector",
                "connection_url",
            )
        }

    @classmethod
    async def store_publish_dda_record(
        cls,
        context: InjectionContext,
        connection_id: str,
        dda: DataDisclosureAgreementModel,
        connection_url: str,
    ) -> "PublishedDDATemplateRecord":
        """Store a dda and create/update publish dda record.

        Args:
            context (InjectionContext): Injection context to be used.
            connection_id (str): Connection id
            dda (DataDisclosureAgreementModel): Data disclosure agreement.
            connection_url (str): Connection URL.

        Returns:
            PublishedDDATemplateRecord: Published DDA template record.
        """

        # Query for existing record for connection and template id.
        tag_filter = {"connection_id": connection_id, "template_id": dda.id}
        records = await cls.query(context, tag_filter)

        if not records:
            # Not an existing entry.
            # Create a new record.
            record = PublishedDDATemplateRecord(
                connection_id=connection_id,
                template_id=dda.id,
                industry_sector=dda.data_sharing_restrictions.industry_sector,
                dda=dda.serialize(),
                connection_url=connection_url,
            )
        else:
            # Existing entry.
            # Update the record.
            record: PublishedDDATemplateRecord = records[0]
            # Industry sector
            record.industry_sector = dda.data_sharing_restrictions.industry_sector
            # DDA
            record.dda = dda.serialize()
            # Connection URL.
            record.connection_url = connection_url

        # Save the record.
        await record.save(context)

        return record

    @classmethod
    async def delete_publish_dda_record(
        cls, context: InjectionContext, connection_id: str, template_id: str
    ):
        """Delete publish DDA record.

        Args:
            context (InjectionContext): Injection context to be used.
            connection_id (str): Connection identifier.
            template_id (str): Template identifier.
        """

        tag_filter = {"connection_id": connection_id, "template_id": template_id}

        records = await cls.query(context, tag_filter)
        assert records, "Publish DDA record not found."

        record: PublishedDDATemplateRecord = records[0]
        await record.delete_record(context)


class PublishedDDATemplateRecordSchema(BaseRecordSchema):
    """Publish DDA template record schema"""

    class Meta:
        model_class = PublishedDDATemplateRecord

    connection_id = fields.Str()
    dda = fields.Dict()
    template_id = fields.Str()
    industry_sector = fields.Str()
    connection_url = fields.Str()
