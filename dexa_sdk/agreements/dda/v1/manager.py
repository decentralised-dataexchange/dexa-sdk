from .models import (
    DataDisclosureAgreementModel,
    DDAVersionsModel
)


class DDAVersionsManager:
    """
    Manager for Data Disclosure Agreements(DDA)

    To manage merkle tree for different version of
    Data Disclosure Agreements. It will provide functions
    to create, read, update, delete DDA and update the
    versions merkle tree.
    """

    def __init__(self) -> None:

        # Dictionary to map merkle root (version)
        # to data disclosure agreements
        self._versions = DDAVersionsModel()

        # Merkle tree to store DDA versions
        self._versions_merkle_tree = None

    def add(self, dda: DataDisclosureAgreementModel) -> None:
        """Add a DDA to the versions mapping"""

        # Merkle root of the DDA
        merkle_root = dda.merkle_tree.merkle_root

        # Update agreement versions with new DDA
        self._versions.add(merkle_root, dda)

    def list(self) -> DDAVersionsModel:
        """Return all the agreements"""
        return self._versions.list()

    def get(self, merkle_root: str) -> DDAVersionsModel:
        """Retrieve DDA by merkle root (version)"""
        return self._versions.get(merkle_root)
