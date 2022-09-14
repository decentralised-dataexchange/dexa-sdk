import json
import typing
from datetime import datetime

from aries_cloudagent.messaging.models.base import BaseModel
from aries_cloudagent.messaging.util import datetime_to_str
from aries_cloudagent.storage.record import StorageRecord


class BaseRecord:
    """Represent a storage record"""

    # Record field representing the identifier
    RECORD_ID_NAME = "id"

    # Record type
    RECORD_TYPE = None

    # Record tags
    TAG_NAMES = {}

    def __init__(
        self,
        *,
        id: str = None,
        record_model: BaseModel,
        record_type: str,
        record_tags: typing.Dict[str, str] = {},
        encrypted_tags: typing.List[str] = [],
        created_at: typing.Union[str, datetime] = None,
        updated_at: typing.Union[str, datetime] = None,
    ) -> None:
        """Intiallise a storage record

        Args:
            record_model (BaseModel): Model instance for the data.
            record_tags (typing.Dict[str, str], optional): Tags for the record. Defaults to {}.
            encrypted_tags (typing.List[str], optional): List of tags to be encrypted on storage.
                Defaults to [].
            created_at (typing.Union[str, datetime], optional): Record creation time.
                Defaults to None.
            updated_at (typing.Union[str, datetime], optional): Record updation time.
                Defaults to None.
        """

        # Identifier for the record.
        # If empty, the record would be treated as a new one.
        self._id = id

        # Type for this record, when persisted to storage
        self.RECORD_TYPE = record_type

        # Model instance for the data
        self._record_model = record_model

        # Tag pairs for the record. It is a key:value pair.
        self._record_tags = record_tags

        # List of tag names
        self.TAG_NAMES = record_tags.keys()
        #
        # List of tags to be encrypted on storage.
        self._encrypted_tags = encrypted_tags

        # Record creation time
        self.created_at = datetime_to_str(created_at)

        # Record updation time.
        self.updated_at = datetime_to_str(updated_at)

    @property
    def encrypted_tags(self) -> typing.List[str]:
        """Accessor for encrypted tags for the record.

        Returns:
            typing.List[str]: List of tags to be encrypted on storage
        """
        return self._encrypted_tags

    @property
    def tag_names(self) -> typing.List[str]:
        """Accessor for tag names available for this record.

        Returns:
            typing.List[str]: Tags names
        """
        return [f"~{k}" if k not in self.encrypted_tags else k for k in self.TAG_NAMES]

    @property
    def record_model(self) -> BaseModel:
        """Accessor for record model

        Returns:
            BaseModel: Model instance for the record data
        """
        return self._record_model

    @property
    def record_tags(self) -> dict:
        """Accessor to record tags pairs.

        Returns:
            dict: Record tag pairs.
        """
        return {
            tag: self._record_tags.get(prop)
            for (prop, tag) in self.get_tag_map().items()
            if self._record_tags.get(prop) is not None
        }

    @property
    def record_value(self) -> dict:
        """Accessor to JSON representation of record model.

        Returns:
            dict: JSON data for the record model
        """
        return self.record_model.serialize()

    @property
    def value(self) -> dict:
        """Accessor for the JSON record value generated for this record.

        Returns:
            dict: JSON record value
        """
        # Remove ~ prefix from non encrypted tags.
        ret = self.strip_tag_prefix(self.tags)

        # Add creation and updation date time to dictionary
        ret.update({"created_at": self.created_at, "updated_at": self.updated_at})

        # Add JSON data for record model to dictionary
        ret.update(self.record_value)

        return ret

    @property
    def tags(self) -> dict:
        """Accessor for the record tags generated for this record.

        Returns:
            dict: Record tags
        """
        tags = self.record_tags
        return tags

    def strip_tag_prefix(self, tags: dict) -> dict:
        """Strip tilde from unencrypted tag names.

        Args:
            tags (dict): Record tags

        Returns:
            dict: Record tags with ~ removed from keys
        """
        return (
            {(k[1:] if "~" in k else k): v for (k, v) in tags.items()} if tags else {}
        )

    def get_tag_map(self) -> typing.Mapping[str, str]:
        """Accessor for the set of defined tags.

        Returns:
            typing.Mapping[str, str]: Map tag keys with ~ to without
        """
        return {tag.lstrip("~"): tag for tag in self.tag_names or ()}

    def prefix_tag_filter(self, tag_filter: dict) -> dict:
        """Prefix unencrypted tags used in the tag filter.

        Args:
            tag_filter (dict): Tag filter for querying records

        Returns:
            dict: Returns tags with prefix
        """
        ret = None
        if tag_filter:
            tag_map = self.get_tag_map()
            ret = {}
            for k, v in tag_filter.items():
                if k in ("$or", "$and") and isinstance(v, list):
                    ret[k] = [self.prefix_tag_filter(clause) for clause in v]
                elif k == "$not" and isinstance(v, dict):
                    ret[k] = self.prefix_tag_filter(v)
                else:
                    ret[tag_map.get(k, k)] = v
        return ret

    @property
    def storage_record(self) -> StorageRecord:
        """Accessor for a `StorageRecord` representing this record.

        Returns:
            StorageRecord: Storage record
        """
        return StorageRecord(
            self.RECORD_TYPE, json.dumps(self.value), self.tags, self._id
        )
