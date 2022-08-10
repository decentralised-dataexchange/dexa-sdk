from marshmallow import fields, ValidationError


class ContextField(fields.Field):
    """Field that serialises a JSONLD context,
    it can be a list of strings or a string"""

    def _serialize(self, value, attr, obj, **kwargs):
        if not (isinstance(value, list) or isinstance(value, str)):
            raise ValidationError(
                "Context must be an instance of List[str] or str")
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        if not (isinstance(value, list) or isinstance(value, str)):
            raise ValidationError(
                "Context must be an instance of List[str] or str")
        return value
