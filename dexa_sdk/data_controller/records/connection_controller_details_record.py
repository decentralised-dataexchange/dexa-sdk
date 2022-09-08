from aries_cloudagent.messaging.models.base_record import (
    BaseRecord,
    BaseRecordSchema
)
from aries_cloudagent.config.injection_context import InjectionContext
from marshmallow import fields
from ...marketplace.models.controller_details import ControllerDetailModel


class ConnectionControllerDetailsRecord(BaseRecord):
    """Connection controller details record model"""
    class Meta:
        schema_class = "ConnectionControllerDetailsRecordSchema"

    # Record type
    RECORD_TYPE = "connection_controller_details"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = None

    # Record tags
    TAG_NAMES = {
        "~connection_id"
    }

    def __init__(
        self,
        id: str = None,
        connection_id: str = None,
        controller_details: dict = None,
        state: str = None,
        **kwargs
    ):
        # Pass the identifier and state to parent class
        super().__init__(id, state, **kwargs)

        self.connection_id = connection_id
        self.controller_details = controller_details

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "connection_id",
                "state",
                "controller_details"
            )
        }

    @property
    def controller_details_model(self) -> ControllerDetailModel:
        """Retreive controller details model.

        Returns:
            ControllerDetailModel: Controller details model
        """
        return ControllerDetailModel.deserialize(self.controller_details)

    @classmethod
    async def set_controller_details_for_connection(
            cls,
            context: InjectionContext,
            connection_id: str,
            controller_details: dict
    ) -> "ConnectionControllerDetailsRecord":
        """Set controller details for connection.

        Args:
            context (InjectionContext): Injection context to be used.
            connection_id (str): Connection identifier
            controller_details (dict): Controller details

        Returns:
            ConnectionControllerDetailsRecord: Connection controller details record.
        """

        tag_filter = {
            "connection_id": connection_id
        }
        records = await cls.query(context, tag_filter)

        if records:
            record: ConnectionControllerDetailsRecord = records[0]
            record.controller_details = controller_details
        else:
            # Create marketplace connection record.
            record = cls(
                connection_id=connection_id,
                controller_details=controller_details
            )

        await record.save(context)

        return record


class ConnectionControllerDetailsRecordSchema(BaseRecordSchema):
    """Connection controller details record schema"""

    class Meta:
        model_class = ConnectionControllerDetailsRecord

    connection_id = fields.Str()
    controller_details = fields.Dict()
