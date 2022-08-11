import typing
from merklelib import MerkleTree
from pydantic import BaseModel

from .utils.json import jcs_bytes_to_pyobject, jcs_rfc8785


def build_merkle_tree(data: typing.List) -> MerkleTree:
    """Build <MerkleTree> from list"""

    # Build <MerkleTree>
    mt = MerkleTree(data)

    return mt


def build_merkle_tree_from_pydantic_base_model(
    base_model: BaseModel,
    dict_fields: typing.List[str] = [],
    list_fields: typing.List[str] = []
) -> MerkleTree:
    """
    Build <MerkleTree> from pydantic <BaseModel>

    Each data is recorded as - <jsonpath>:<value>
    This would avoid collision while generating merkle proofs
    For e.g. for the following json,
    {
        "name" : "Alice"
    }

    Data in merkle tree for field "name" would be - $.name:Alice
    """

    # Canonicalise the fields
    canon = jcs_rfc8785(list(base_model.__fields__.keys()))

    # Convert bytes to python list
    canon = jcs_bytes_to_pyobject(canon)

    # Data prefix to avoid collision
    jsonpath = base_model.__class__.Config.__dda_field_jsonpath__

    flattened = []

    # Prepare data for <MerkleTree>
    # Each data is recorded as - <jsonpath>:<value>
    # This would avoid collision while generating merkle proofs
    for key in canon:
        value = getattr(base_model, key)

        if key in dict_fields:

            # Build the <MerkleTree>
            dict_mt: MerkleTree = value.to_merkle_tree()

            flattened.append(
                f"$.{key}:{dict_mt.merkle_root}"
            )

        elif key in list_fields:

            nested_flattened = []

            # Iterate through each list<BaseModel>
            for index, item in enumerate(value):

                # To accomodate @context field,
                # which can be either str or list<str>
                if isinstance(item, str):
                    nested_flattened.append(
                        f"{jsonpath}{key}.{index}:{item}"
                    )
                else:
                    # Build the <MerkleTree>
                    item_mt = item.to_merkle_tree()

                    # Append the merkle root to a nested flattened list
                    nested_flattened.append(
                        f"{jsonpath}{key}.{index}:{item_mt.merkle_root}"
                    )

            # Build the <MerkleTree> from the nested flattened list
            nested_mt = build_merkle_tree(nested_flattened)

            # Append the merkle root to the flattened (parent) list
            flattened.append(
                f"{jsonpath}{key}:{nested_mt.merkle_root}"
            )

        else:
            flattened.append(
                f"{jsonpath}{key}:{value}"
            )

    # Build <MerkleTree>
    mt = build_merkle_tree(flattened)

    return mt
