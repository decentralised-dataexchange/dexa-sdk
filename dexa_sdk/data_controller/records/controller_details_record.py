from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from marshmallow import fields


class ControllerDetailsRecord(BaseRecord):
    """Data controller details record."""

    class Meta:
        schema_class = "ControllerDetailsRecordSchema"

    # Record type
    RECORD_TYPE = "controller_details_record"

    # Record identifier
    RECORD_ID_NAME = "id"

    # Webhook topic name for this record type
    WEBHOOK_TOPIC = None

    def __init__(
        self,
        id: str = None,
        organisation_did: str = None,
        organisation_name: str = None,
        cover_image_url: str = None,
        logo_image_url: str = None,
        location: str = None,
        organisation_type: str = None,
        description: str = None,
        policy_url: str = None,
        eula_url: str = None,
        state: str = None,
        **kwargs
    ):
        # Pass the identifier and state to parent class
        super().__init__(id, state, **kwargs)

        self.organisation_did = organisation_did
        self.organisation_name = organisation_name
        self.cover_image_url = cover_image_url
        self.logo_image_url = logo_image_url
        self.location = location
        self.organisation_type = organisation_type
        self.description = description
        self.policy_url = policy_url
        self.eula_url = eula_url

    @property
    def record_value(self) -> dict:
        """Accessor for JSON record value generated for this transaction record."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "organisation_did",
                "state",
                "organisation_name",
                "cover_image_url",
                "logo_image_url",
                "location",
                "organisation_type",
                "description",
                "policy_url",
                "eula_url",
            )
        }


class ControllerDetailsRecordSchema(BaseRecordSchema):
    """Data controller details record schema"""

    class Meta:
        model_class = ControllerDetailsRecord

    organisation_did = fields.Str(required=False)
    organisation_name = fields.Str(required=False)
    cover_image_url = fields.Str(required=False)
    logo_image_url = fields.Str(required=False)
    location = fields.Str(required=False)
    organisation_type = fields.Str(required=False)
    description = fields.Str(required=False)
    policy_url = fields.Str(required=False)
    eula_url = fields.Str(required=False)
