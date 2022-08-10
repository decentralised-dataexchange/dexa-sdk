# TODO: Store dda as <MerkleTree>
# TODO: Get proofs
# TODO: Get Audit proofs

from typing import OrderedDict
import typing
from merklelib import MerkleTree
from loguru import logger


def list_to_merkle_tree(data: typing.List) -> MerkleTree:
    """
    Convert list to <MerkleTree>

    List is iterated to prepare the items to be loaded
    into a <MerkleTree>.
    """
    return None


def ordered_dict_to_merkle_tree(data: OrderedDict) -> MerkleTree:
    """
    Convert ordered dict to <MerkleTree>

    Note: OrderedDict shall only contain JSON compatible values.

    OrderedDict will be flattened into a list of values.
    The flattened list of value is then used to instantiate
    the <MerkleTree> instance.

    Dict key are iterated and value with string, boolean, int,
    float types are added to the flattened list.

    If the value is a dict, then a <MerkleTree> is created
    from a flattened list iterated from the content of the dict.
    The root hash of the new <MerkleTree> is then added to the parent
    flattened list.

    If the value is a list, then list is iterated to create a list of data
    (to be converted to merkle hashes) to form a new <MerkleTree>. The root
    hash of this new <MerkleTree> is then added to the parent flattened list.
    """

    okeys = data.keys()
    ovalues = data.values()

    for index, key in enumerate(okeys):
        logger.info(f"okeys[{index}] = {key}")

    for index, value in enumerate(ovalues):
        logger.info(f"ovalues[{index}] = {value}")

    return None
