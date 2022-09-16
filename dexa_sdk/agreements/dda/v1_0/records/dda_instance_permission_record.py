import typing

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from dexa_sdk.agreements.dda.v1_0.records.dda_instance_record import (
    DataDisclosureAgreementInstanceRecord,
)
from marshmallow import EXCLUDE, fields


class DDAInstancePermissionRecord(BaseRecord):
    class Meta:
        schema_class = "DDAInstancePermissionRecordSchema"

    RECORD_TYPE = "dda_instance_permission_record"
    RECORD_ID_NAME = "id"
    WEBHOOK_TOPIC = "dda_instance_permission_record"
    TAG_NAMES = {"~instance_id"}

    STATE_DEACTIVATE = "deactivate"

    def __init__(
        self, *, id: str = None, instance_id: str = None, state: str = None, **kwargs
    ):
        super().__init__(id, state, **kwargs)

        if not instance_id:
            raise TypeError("Instance identifier is not specified.")

        self.instance_id = instance_id
        self.state = state

    @property
    def record_value(self) -> dict:
        return {
            prop: getattr(self, prop)
            for prop in (
                "instance_id",
                "state",
            )
        }

    @classmethod
    async def deactivate(
        cls, context: InjectionContext, instance_id: str
    ) -> typing.Tuple[
        DataDisclosureAgreementInstanceRecord, "DDAInstancePermissionRecord"
    ]:
        """Deactivate DDA.

        Args:
            context (InjectionContext): Injection context to be used.
            instance_id (str): Instance ID.
        """
        # Fetch DDA instance.
        tag_filter = {"instance_id": instance_id}
        dda_instance_record: DataDisclosureAgreementInstanceRecord = (
            await DataDisclosureAgreementInstanceRecord.retrieve_by_tag_filter(
                context, tag_filter
            )
        )

        # Check for existing records.
        tag_filter = {"instance_id": dda_instance_record.instance_id}
        records = await DDAInstancePermissionRecord.query(context, tag_filter)

        # There are no existing records.
        if not records:
            # Create a new record.
            record = cls(
                instance_id=dda_instance_record.instance_id, state=cls.STATE_DEACTIVATE
            )
            await record.save(context)
        else:
            record = records[0]

        return dda_instance_record, record

    @classmethod
    async def get_permission(
        cls, context: InjectionContext, instance_id: str
    ) -> typing.Union["DDAInstancePermissionRecord", None]:
        """Get permission.

        Args:
            context (InjectionContext): Injection context to be used.

        Returns:
            typing.Union[DDAInstancePermissionRecord, None]: DDA instance permission record.
        """
        # Fetch DDA instance permission record.
        instance_permission_records: typing.List[
            DDAInstancePermissionRecord
        ] = await DDAInstancePermissionRecord.query(
            context, {"instance_id": instance_id}
        )

        return (
            None if not instance_permission_records else instance_permission_records[0]
        )


class DDAInstancePermissionRecordSchema(BaseRecordSchema):
    class Meta:
        model_class = DDAInstancePermissionRecord
        unknown = EXCLUDE

    instance_id = fields.Str()
    state = fields.Str()
