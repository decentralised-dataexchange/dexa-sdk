from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from marshmallow import EXCLUDE, fields


class PullDataRecord(BaseRecord):
    class Meta:
        schema_class = "PullDataRecordSchema"

    RECORD_TYPE = "pulldata_record"
    RECORD_ID_NAME = "id"
    WEBHOOK_TOPIC = "pulldata_record"
    TAG_NAMES = {
        "~state",
        "~dda_instance_id",
        "~dda_template_id",
        "~nonce",
        "~blink",
        "~da_instance_id",
        "~da_template_id",
    }

    STATE_REQUEST = "request"
    STATE_RESPONSE = "response"

    def __init__(
        self,
        *,
        id: str = None,
        dda_instance_id: str = None,
        dda_template_id: str = None,
        da_instance_id: str = None,
        nonce: str = None,
        state: str = None,
        blink: str = None,
        blockchain_receipt: dict = None,
        token: str = None,
        token_packed: dict = None,
        da_template_id: str = None,
        **kwargs
    ):
        super().__init__(id, state, **kwargs)

        self.dda_instance_id = dda_instance_id
        self.dda_template_id = dda_template_id
        self.nonce = nonce
        self.state = state
        self.blink = blink
        self.blockchain_receipt = blockchain_receipt
        self.token = token
        self.token_packed = token_packed
        self.da_instance_id = da_instance_id
        self.da_template_id = da_template_id

    @property
    def record_value(self) -> dict:
        return {
            prop: getattr(self, prop)
            for prop in (
                "dda_instance_id",
                "dda_template_id",
                "nonce",
                "state",
                "blink",
                "blockchain_receipt",
                "token",
                "token_packed",
                "da_instance_id",
                "da_template_id",
            )
        }


class PullDataRecordSchema(BaseRecordSchema):
    class Meta:
        model_class = PullDataRecord
        unknown = EXCLUDE

    dda_instance_id = fields.Str(required=False)
    dda_template_id = fields.Str(required=False)
    nonce = fields.Str(required=False)
    state = fields.Str(required=False)
    blink = fields.Str(required=False)
    blockchain_receipt = fields.Dict(required=False)
    token_packed = fields.Dict(required=False)
    token = fields.Str(required=False)
    da_instance_id = fields.Str(required=False)
    da_template_id = fields.Str(required=False)
