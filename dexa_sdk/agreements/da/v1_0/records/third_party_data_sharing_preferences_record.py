import typing

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from marshmallow import EXCLUDE, fields
from mydata_did.v1_0.utils.util import bool_to_str, str_to_bool


class ThirdParyDAPreferenceRecord(BaseRecord):
    class Meta:
        schema_class = "ThirdParyDAPreferenceRecordSchema"

    RECORD_TYPE = "third_party_da_preference_record"
    RECORD_ID_NAME = "id"
    WEBHOOK_TOPIC = "third_party_da_preference_record"
    TAG_NAMES = {"~dda_instance_id", "~da_instance_id", "~state", "~latest_flag"}

    STATE_ALLOW = "allow"
    STATE_DISALLOW = "disallow"

    def __init__(
        self,
        *,
        id: str = None,
        dda_instance_id: str = None,
        da_instance_id: str = None,
        latest_flag: str = "false",
        state: str = None,
        **kwargs
    ):
        super().__init__(id, state, **kwargs)

        self.dda_instance_id = dda_instance_id
        self.state = state
        self.latest_flag = latest_flag
        self.da_instance_id = da_instance_id

    @property
    def record_value(self) -> dict:
        return {
            prop: getattr(self, prop)
            for prop in ("dda_instance_id", "state", "latest_flag", "da_instance_id")
        }

    @property
    def _latest_flag(self) -> bool:
        """Accessor for latest flag

        Returns:
            bool: Latest flag
        """
        return str_to_bool(self.latest_flag)

    @_latest_flag.setter
    def _latest_flag(self, val: bool):
        """Setter for latest flag

        Args:
            val (bool): Latest flag
        """
        self.latest_flag = bool_to_str(val)

    @classmethod
    async def get_preference(
        cls,
        context: InjectionContext,
        dda_instance_id: str,
        da_instance_id: str,
    ) -> typing.Union["ThirdParyDAPreferenceRecord", None]:
        """Get preference.

        Args:
            context (InjectionContext): Injection context to be used.
            dda_instance_id (str): DDA instance ID.
            da_instance_id (str): DA instance ID.

        Returns:
            ThirdParyDAPreferenceRecord: Thirdparty DA preference record.
        """

        preference_records: typing.List[
            ThirdParyDAPreferenceRecord
        ] = await ThirdParyDAPreferenceRecord.query(
            context,
            {
                "dda_instance_id": dda_instance_id,
                "da_instance_id": da_instance_id,
                "latest_flag": bool_to_str(True),
            },
        )

        return preference_records[0] if preference_records else None

    @classmethod
    async def add_preference(
        cls,
        context: InjectionContext,
        dda_instance_id: str,
        da_instance_id: str,
        state: str,
    ) -> "ThirdParyDAPreferenceRecord":
        """Add preference.

        Args:
            context (InjectionContext): Injection context to be used.
            dda_instance_id (str): DDA instance ID.
            da_instance_id (str): DA instance ID.
            state (str): State.

        Returns:
            ThirdParyDAPreferenceRecord: Thirdparty DA preference record.
        """

        preference_records: typing.List[
            ThirdParyDAPreferenceRecord
        ] = await ThirdParyDAPreferenceRecord.query(
            context,
            {
                "dda_instance_id": dda_instance_id,
                "da_instance_id": da_instance_id,
                "latest_flag": bool_to_str(True),
            },
        )

        # Create preference record.
        new_preference_record = ThirdParyDAPreferenceRecord(
            dda_instance_id=dda_instance_id,
            da_instance_id=da_instance_id,
            latest_flag=bool_to_str(True),
            state=state,
        )

        if preference_records:
            # Update existing preference record.
            # and mark as not the latest.
            preference_record = preference_records[0]
            preference_record.latest_flag = bool_to_str(False)
            await preference_record.save(context)

        await new_preference_record.save(context)

        return new_preference_record


class ThirdParyDAPreferenceRecordSchema(BaseRecordSchema):
    class Meta:
        model_class = ThirdParyDAPreferenceRecord
        unknown = EXCLUDE

    dda_instance_id = fields.Str()
    state = fields.Str()
    latest_flag = fields.Str()
    da_instance_id = fields.Str()
