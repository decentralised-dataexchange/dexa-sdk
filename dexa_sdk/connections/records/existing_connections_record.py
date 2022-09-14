from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from marshmallow import fields


class ExistingConnectionRecord(BaseRecord):
    """Existing connection record."""

    class Meta:
        schema_class = "ExistingConnectionRecordSchema"

    # Record type
    RECORD_TYPE = "existing_connection_record"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Record tags
    TAG_NAMES = {
        "~existing_connection_id",
        "~my_did",
        "~connection_status",
        "~connection_id",
    }

    def __init__(
        self,
        id: str = None,
        existing_connection_id: str = None,
        my_did: str = None,
        connection_status: dict = None,
        connection_id: str = None,
        state: str = None,
        **kwargs
    ):
        # Pass the identifier and state to parent class
        super().__init__(id, state, **kwargs)

        self.existing_connection_id = existing_connection_id
        self.my_did = my_did
        self.connection_status = connection_status
        self.connection_id = connection_id

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "existing_connection_id",
                "state",
                "my_did",
                "connection_status",
                "connection_id",
            )
        }


class ExistingConnectionRecordSchema(BaseRecordSchema):
    """Existing connection record schema"""

    class Meta:
        model_class = ExistingConnectionRecord

    existing_connection_id = fields.Str()
    my_did = fields.Str()
    state = fields.Str()
    connection_status = fields.Dict()
    connection_id = fields.Str()
