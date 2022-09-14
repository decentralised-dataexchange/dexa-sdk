from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from marshmallow import fields


class PublishDDARecord(BaseRecord):
    """Publish DDA record."""

    class Meta:
        schema_class = "PublishDDARecordSchema"

    # Record type
    RECORD_TYPE = "publish_dda_record"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Record tags
    TAG_NAMES = {"~connection_id", "~template_id", "~state"}

    # States
    STATE_REQUEST = "request"
    STATE_ACCEPT = "accept"

    def __init__(
        self,
        id: str = None,
        connection_id: str = None,
        template_id: str = None,
        dda: dict = None,
        state: str = None,
        **kwargs
    ):
        # Pass the identifier and state to parent class
        super().__init__(id, state, **kwargs)

        self.connection_id = connection_id
        self.dda = dda
        self.template_id = template_id

    @property
    def request_id(self) -> str:
        """Accessor for record identifier"""
        return self._id

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in ("connection_id", "state", "dda", "template_id")
        }

    @classmethod
    async def store_publish_dda_record(
        cls, context: InjectionContext, connection_id: str, template_id: str, dda: dict
    ) -> "PublishDDARecord":
        """Store publish dda record.

        Args:
            context (InjectionContext): Injection context to be used.
            connection_id (str): Connection id
            template_id (str): Template id.
            dda (dict): Data disclosure agreement

        Returns:
            PublishDDARecord: Publish dda record.
        """
        #  Check if an existing publish dda record exists.
        tag_filter = {"connection_id": connection_id, "template_id": template_id}
        records = await cls.query(context, tag_filter)
        assert len(records) == 0, "DDA cannot be published twice."

        record = PublishDDARecord(
            connection_id=connection_id,
            template_id=template_id,
            dda=dda,
            state=PublishDDARecord.STATE_REQUEST,
        )

        await record.save(context)
        return record


class PublishDDARecordSchema(BaseRecordSchema):
    """Publish DDA record schema"""

    class Meta:
        model_class = PublishDDARecord

    request_id = fields.Str()
    connection_id = fields.Str()
    state = fields.Str()
    dda = fields.Dict()
    template_id = fields.Str()
