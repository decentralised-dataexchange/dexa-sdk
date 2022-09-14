from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from marshmallow import fields
from mydata_did.v1_0.utils.util import bool_to_str


class DataAgreementQRCodeRecord(BaseRecord):
    """Data agreement QR code record"""

    class Meta:
        schema_class = "DataAgreementQRCodeRecordSchema"

    # Record type
    RECORD_TYPE = "da_qr"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = None

    # Record tags
    TAG_NAMES = {
        "~template_id",
        "~multi_use_flag",
        "~scanned_flag",
        "~connection_id",
        "~data_ex_id",
    }

    def __init__(
        self,
        id: str = None,
        template_id: str = None,
        multi_use_flag: str = None,
        scanned_flag: str = None,
        connection_id: str = None,
        state: str = None,
        dynamic_link: str = None,
        data_ex_id: str = None,
        **kwargs
    ):
        # Pass the identifier and state to parent class
        super().__init__(id, state, **kwargs)

        self.connection_id = connection_id
        self.template_id = template_id
        self.multi_use_flag = multi_use_flag
        self.scanned_flag = scanned_flag
        self.dynamic_link = dynamic_link
        self.data_ex_id = data_ex_id

    @property
    def qr_id(self) -> str:
        return self._id

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "connection_id",
                "template_id",
                "multi_use_flag",
                "scanned_flag",
                "dynamic_link",
                "data_ex_id",
            )
        }

    @property
    def _multi_use_flag(self) -> bool:
        return self.multi_use_flag

    @_multi_use_flag.setter
    def _multi_use_flag(self, val: bool):
        self.mult_use_flag = bool_to_str(val)

    @property
    def _scanned_flag(self) -> bool:
        return self.scanned_flag

    @_scanned_flag.setter
    def _scanned_flag(self, val: bool) -> bool:
        self.scanned_flag = bool_to_str(val)

    async def connection_record(self, context: InjectionContext) -> ConnectionRecord:
        """Retreive connection record.

        Returns:
            ConnectionRecord: Connection record.
        """
        return await ConnectionRecord.retrieve_by_id(context, self.connection_id)


class DataAgreementQRCodeRecordSchema(BaseRecordSchema):
    """Data agreement QR code record schema"""

    class Meta:
        model_class = DataAgreementQRCodeRecord

    qr_id = fields.Str()
    connection_id = fields.Str()
    template_id = fields.Str()
    multi_use_flag = fields.Str()
    scanned_flag = fields.Str()
    dynamic_link = fields.Str()
    data_ex_id = fields.Str()
