import typing
from merklelib import MerkleTree
from ..instances import DataDisclosureAgreementInstance


class DuplicateDDAError(Exception):
    """Raised when existing DDA is added to the merkle tree"""
    pass


class DDAVersionLeaf:
    """
    Data Disclosure Agreement Version Leaf

    Represents a leaf in DDA Versions Merkle Tree
    """

    def __init__(self,
                 *,
                 dda_container: DataDisclosureAgreementInstance,
                 next_version_did: str = None,
                 previous_version_did: str = None) -> None:
        """Initialise DDA Version Leaf class"""
        # Set the class attributes
        self._dda_container = dda_container
        self._next_version_did = next_version_did
        self._previous_version_did = previous_version_did

    @property
    def dda_container(self) -> DataDisclosureAgreementInstance:
        """Returns data disclosure agreement container"""
        return self._dda_container

    @property
    def next_version_did(self) -> str:
        """Returns next version did:mydata identifier"""
        return self._next_version_did

    @next_version_did.setter
    def next_version_did(self, did: str) -> None:
        """Update the next version did:mydata identifier"""
        self._next_version_did = did

    @property
    def previous_version_did(self) -> str:
        """Returns previous version did:mydata identifier"""
        return self._previous_version_did

    @property
    def mydata_did(self) -> str:
        """Returns did:mydata identifier"""
        return self.dda_container.mydata_did

    @property
    def merkle_tree(self) -> MerkleTree:
        """Returns merkle tree"""
        return self.dda_container.merkle_tree

    @property
    def merkle_root(self) -> str:
        """Returns merkle root"""
        return self.dda_container.merkle_root

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"current version did: {self.mydata_did}, "
            f"next version did: {self.next_version_did}, "
            f"previous version did: {self.previous_version_did} >"
        )


class DDAVersionsMerkleTree:
    """
    DDA Versions as Merkle Tree

    Represent different versions of DDA as leaves
    in a Merkle Tree.
    """

    def __init__(self) -> None:

        # Dictionary to map did:mydata identifier
        # of a DDA to DDAVersionLeaf
        self._merkle_leaves: typing.Dict[str, DDAVersionLeaf] = {}

        # Merkle tree constructed from sequence of DDAVersionLeaf
        self._merkle_tree = None

    def add_multiple(
        self,
        dda_containers: typing.List[DataDisclosureAgreementInstance]
    ) -> None:
        """Append multiple DDA to the merkle tree"""
        for dda_container in dda_containers:
            self.add(dda_container)

    def add(
        self,
        dda_container: DataDisclosureAgreementInstance
    ) -> None:
        """Append DDA to the merkle tree"""

        # previous version
        previous_version: DDAVersionLeaf = None
        try:
            previous_version = self._merkle_leaves[
                next(
                    iter(
                        reversed(self._merkle_leaves)
                    )
                )
            ]
        except StopIteration:
            pass

        previous_version_did = None
        if previous_version:
            previous_version_did = previous_version.mydata_did

            # Update next_version_did for previous leaf
            # with did:mydata identifier for current leaf
            previous_version.next_version_did = dda_container.mydata_did

        # next version is not available
        # since the DDA is added to the end of the merkle tree
        next_version_did = None

        mydata_did = dda_container.mydata_did

        # Check if a DDA with same did:mydata exists in the versions tree
        if self._merkle_leaves.get(mydata_did):
            raise DuplicateDDAError(
                (
                    f"DDA with {mydata_did}"
                    f" exists in the merkle tree"
                )
            )

        # Create DDA version leaf and add to merkle leaves dictionary
        leaf = DDAVersionLeaf(
            dda_container=dda_container,
            next_version_did=next_version_did,
            previous_version_did=previous_version_did
        )

        # Update versions mapping with the new version
        self._merkle_leaves.update({mydata_did: leaf})

    @property
    def merkle_leaves_map(self) -> typing.Dict[str, DDAVersionLeaf]:
        """Return mapping of did:mydata to leaf"""
        return self._merkle_leaves

    def get(self, did: str) -> DDAVersionLeaf:
        """Retrieve DDA version by did:mydata"""
        return self._merkle_leaves.get(did)

    @property
    def genesis(self) -> DDAVersionLeaf:
        """Retrieve the genesis DDA version in merkle tree"""
        try:
            return self._merkle_leaves[next(iter(self._merkle_leaves))]
        except StopIteration:
            return None

    @property
    def current(self) -> DDAVersionLeaf:
        """Retrieve the current/latest DDA version in merkle tree"""
        try:
            return self._merkle_leaves[
                next(
                    iter(
                        reversed(self._merkle_leaves)
                    )
                )
            ]
        except StopIteration:
            return None

    def __len__(self) -> int:
        """Return the length merkle tree leaves"""
        return len(self._merkle_leaves)
