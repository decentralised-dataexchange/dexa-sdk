from aries_cloudagent.messaging.models.base import BaseModel, BaseModelSchema
from aries_cloudagent.storage.record import StorageRecord
from asynctest import TestCase as AsyncTestCase
from dexa_sdk.storage.records.base_record import BaseRecord
from marshmallow import EXCLUDE, fields


class MockModel(BaseModel):
    """Mock model for testing."""

    class Meta:
        # Schema class
        schema_class = "MockSchema"

    def __init__(self, *, mock_field: str, **kwargs):
        """Initialise the mock model

        Args:
            mock_field (str): mock field description
        """
        # Call the parent constructor
        super().__init__(**kwargs)

        # Set model attributes
        self.mock_field = mock_field


class MockSchema(BaseModelSchema):
    class Meta:
        # Model class
        model_class = "MockModel"

        # Exclude unknown fields
        unknown = EXCLUDE

    # Mock field
    mock_field = fields.Str()


class TestBaseRecord(AsyncTestCase):
    """Test base record"""

    def setUp(self) -> None:

        self.mock_model = MockModel(mock_field="mock field value")

    def test_base_record_value(self) -> None:
        """Test base record value to be persisted in storage"""

        base_record = BaseRecord(
            record_model=self.mock_model,
            record_type="mock",
            record_tags={"mock tag": "mock tag value"},
        )

        assert base_record.value.get("mock_field") is not None
        assert base_record.get_tag_map().get("mock tag") is not None
        assert base_record.get_tag_map().get("mock tag") == "~mock tag"
        assert (
            base_record.prefix_tag_filter({"mock tag": "some value"}).get("~mock tag")
            is not None
        )
        assert isinstance(base_record.storage_record, StorageRecord)
