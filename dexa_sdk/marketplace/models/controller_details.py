from aries_cloudagent.messaging.models.base import BaseModel, BaseModelSchema
from marshmallow import fields


class ControllerDetailModel(BaseModel):
    class Meta:
        schema_class = "ControllerDetailSchema"

    def __init__(
        self,
        *,
        organisation_id: str = None,
        organisation_name: str = None,
        cover_image_url: str = None,
        logo_image_url: str = None,
        location: str = None,
        organisation_type: str = None,
        description: str = None,
        policy_url: str = None,
        eula_url: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.organisation_id = organisation_id
        self.organisation_name = organisation_name
        self.cover_image_url = cover_image_url
        self.logo_image_url = logo_image_url
        self.location = location
        self.organisation_type = organisation_type
        self.description = description
        self.policy_url = policy_url
        self.eula_url = eula_url


class ControllerDetailSchema(BaseModelSchema):
    class Meta:
        model_class = ControllerDetailModel

    organisation_id = fields.Str(required=False)
    organisation_name = fields.Str(required=False)
    cover_image_url = fields.Str(required=False)
    logo_image_url = fields.Str(required=False)
    location = fields.Str(required=False)
    organisation_type = fields.Str(required=False)
    description = fields.Str(required=False)
    policy_url = fields.Str(required=False)
    eula_url = fields.Str(required=False)
