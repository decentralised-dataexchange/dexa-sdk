import typing

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from dexa_sdk.agreements.da.v1_0.records.da_instance_record import (
    DataAgreementInstanceRecord,
)
from marshmallow import EXCLUDE, fields
from mydata_did.v1_0.utils.util import bool_to_str, str_to_bool


class DAInstancePermissionRecord(BaseRecord):
    class Meta:
        schema_class = "DAInstancePermissionRecordSchema"

    RECORD_TYPE = "da_instance_permission_record"
    RECORD_ID_NAME = "id"
    WEBHOOK_TOPIC = "da_instance_permission_record"
    TAG_NAMES = {"~instance_id", "~latest_flag"}

    STATE_ALLOW = "allow"
    STATE_DISALLOW = "disallow"

    def __init__(
        self,
        *,
        id: str = None,
        instance_id: str = None,
        latest_flag: str = "false",
        state: str = None,
        **kwargs
    ):
        super().__init__(id, state, **kwargs)

        if not instance_id:
            raise TypeError("Instance identifier is not specified.")

        self.instance_id = instance_id
        self.state = state
        self.latest_flag = latest_flag

    @property
    def record_value(self) -> dict:
        return {
            prop: getattr(self, prop)
            for prop in ("instance_id", "state", "latest_flag")
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
    async def get_latest(
        cls, context: InjectionContext, instance_id: str
    ) -> "DAInstancePermissionRecord":

        # Fetch DA instance.
        tag_filter = {"instance_id": instance_id}
        da_instance_record: DataAgreementInstanceRecord = (
            await DataAgreementInstanceRecord.retrieve_by_tag_filter(
                context, tag_filter
            )
        )

        # Fetch the latest permission.
        tag_filter = {
            "instance_id": da_instance_record.instance_id,
            "latest_flag": bool_to_str(True),
        }
        records = await DAInstancePermissionRecord.query(context, tag_filter)

        return None if not records else records[0]

    @classmethod
    async def add_permission(
        cls, context: InjectionContext, instance_id: str, state: str
    ) -> typing.Tuple[DataAgreementInstanceRecord, "DAInstancePermissionRecord"]:

        # Fetch DA instance.
        tag_filter = {"instance_id": instance_id}
        da_instance_record: DataAgreementInstanceRecord = (
            await DataAgreementInstanceRecord.retrieve_by_tag_filter(
                context, tag_filter
            )
        )

        # Fetch the latest permission.
        tag_filter = {
            "instance_id": da_instance_record.instance_id,
            "latest_flag": bool_to_str(True),
        }
        records = await DAInstancePermissionRecord.query(context, tag_filter)

        if not records:
            # There are no existing records.
            # Create a new record.
            record = cls(
                instance_id=da_instance_record.instance_id,
                state=state,
                latest_flag=bool_to_str(True),
            )
            await record.save(context)
        else:
            # Update the existing record
            # Mark as not the latest.
            record: DAInstancePermissionRecord = records[0]
            record.latest_flag = bool_to_str(False)
            await record.save(context)

            # Create a new record.
            new_record = cls(
                instance_id=da_instance_record.instance_id,
                state=state,
                latest_flag=bool_to_str(True),
            )
            await new_record.save(context)

        return da_instance_record, record


class DAInstancePermissionRecordSchema(BaseRecordSchema):
    class Meta:
        model_class = DAInstancePermissionRecord
        unknown = EXCLUDE

    instance_id = fields.Str()
    state = fields.Str()
    latest_flag = fields.Str()
