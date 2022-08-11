from pydantic import BaseModel
from merklelib import MerkleTree
from .....storage.merkletree import build_merkle_tree_from_pydantic_base_model


class DataDisclosureAgreementBase(BaseModel):
    """
    Base class for Data Disclosure Agreement models
    """

    def to_merkle_tree(self) -> MerkleTree:
        """Get <MerkleTree> representation"""

        # Build <MerkleTree>
        mt = build_merkle_tree_from_pydantic_base_model(self)
        return mt
