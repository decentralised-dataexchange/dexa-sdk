from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from dexa_sdk.data_controller.records.connection_controller_details_record import (
    ConnectionControllerDetailsRecord,
)
from dexa_sdk.marketplace.models.controller_details import ControllerDetailModel
from marshmallow import fields


class MarketplaceConnectionRecord(BaseRecord):
    """Marketplace connection record model"""

    class Meta:
        schema_class = "MarketplaceConnectionRecordSchema"

    # Record type
    RECORD_TYPE = "marketplace_connection"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = None

    # Record tags
    TAG_NAMES = {"~connection_id"}

    def __init__(
        self, id: str = None, connection_id: str = None, state: str = None, **kwargs
    ):
        # Pass the identifier and state to parent class
        super().__init__(id, state, **kwargs)

        self.connection_id = connection_id

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {prop: getattr(self, prop) for prop in ("connection_id", "state")}

    async def controller_details_model(
        self, context: InjectionContext
    ) -> ControllerDetailModel:
        """Retreive controller details model.

        Returns:
            ControllerDetailModel: Controller details model
        """
        tag_filter = {"connection_id": self.connection_id}
        record: ConnectionControllerDetailsRecord = (
            await ConnectionControllerDetailsRecord.retrieve_by_tag_filter(
                context, tag_filter
            )
        )
        return record.controller_details_model

    @classmethod
    async def set_connection_as_marketplace(
        cls, context: InjectionContext, connection_id: str
    ) -> "MarketplaceConnectionRecord":
        """Set connection as marketplace.

        Args:
            context (InjectionContext): Injection context to be used.
            connection_id (str): Connection identifier

        Returns:
            MarketplaceConnectionRecord: Marketplace connection record.
        """

        tag_filter = {"connection_id": connection_id}
        records = await cls.query(context, tag_filter)

        if records:
            record: MarketplaceConnectionRecord = records[0]
        else:
            # Create marketplace connection record.
            record = cls(connection_id=connection_id)

        await record.save(context)

        return record

    @classmethod
    async def retrieve_connection_record(
        cls, context: InjectionContext, connection_id: str
    ) -> ConnectionRecord:
        """Retrieve connection record.

        Args:
            context (InjectionContext): Injection context to be used.
            connection_id (str): Connection id.

        Returns:
            ConnectionRecord: Connection record.
        """
        tag_filter = {"connection_id": connection_id}
        records = await cls.query(context, tag_filter)
        assert records, "Marketplace connection not found."

        record = records[0]

        connection_record = await ConnectionRecord.retrieve_by_id(
            context, record.connection_id
        )
        return connection_record


class MarketplaceConnectionRecordSchema(BaseRecordSchema):
    """Marketplace connection record schema"""

    class Meta:
        model_class = MarketplaceConnectionRecord

    connection_id = fields.Str()
