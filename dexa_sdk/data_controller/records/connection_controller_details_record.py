from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from marshmallow import fields
from mydata_did.v1_0.models.data_controller_model import DataController


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
    TAG_NAMES = {"~connection_id", "~organisation_did"}

    def __init__(
        self,
        id: str = None,
        connection_id: str = None,
        organisation_did: str = None,
        controller_details: dict = None,
        state: str = None,
        **kwargs
    ):
        # Pass the identifier and state to parent class
        super().__init__(id, state, **kwargs)

        self.connection_id = connection_id
        self.controller_details = controller_details
        self.organisation_did = organisation_did

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "connection_id",
                "state",
                "controller_details",
                "organisation_did",
            )
        }

    @property
    def controller_details_model(self) -> DataController:
        """Retreive controller details model.

        Returns:
            DataController: Controller details model
        """
        return DataController.deserialize(self.controller_details)

    async def fetch_connection_record(
        self, context: InjectionContext
    ) -> ConnectionRecord:
        """Retreive connection record.

        Returns:
            ConnectionRecord: Connection record.
        """
        return await ConnectionRecord.retrieve_by_id(context, self.connection_id)

    @classmethod
    async def set_controller_details_for_connection(
        cls,
        context: InjectionContext,
        connection_record: ConnectionRecord,
        controller_details: DataController,
    ) -> "ConnectionControllerDetailsRecord":
        """Set controller details for connection.

        Args:
            context (InjectionContext): Injection context to be used.
            connection_id (ConnectionRecord): Connection identifier
            controller_details (dict): Controller details

        Returns:
            ConnectionControllerDetailsRecord: Connection controller details record.
        """

        tag_filter = {"organisation_did": controller_details.organisation_did}
        records = await cls.query(context, tag_filter)

        if records:
            # Existing connection found.

            # Delete the new connection.
            await connection_record.delete_record(context)
        else:
            # Create marketplace connection record.
            record = cls(
                connection_id=connection_record.connection_id,
                controller_details=controller_details.serialize(),
                organisation_did=controller_details.organisation_did,
            )

        await record.save(context)

        return record


class ConnectionControllerDetailsRecordSchema(BaseRecordSchema):
    """Connection controller details record schema"""

    class Meta:
        model_class = ConnectionControllerDetailsRecord

    connection_id = fields.Str()
    controller_details = fields.Dict()
    organisation_did = fields.Str()
