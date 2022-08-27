from .containers import DataDisclosureAgreementContainer


class DDAVersionLeaf:
    """
    Data Disclosure Agreement Version Leaf

    Represents a leaf in DDA Versions Merkle Tree
    """

    def __init__(self,
                 *,
                 dda_container: DataDisclosureAgreementContainer,
                 next_version_did: str = None,
                 previous_version_did: str = None) -> None:
        """Initialise DDA Version Leaf class"""
        # Set the class attributes
        self._dda_container = dda_container
        self._next_version_did = next_version_did
        self._previous_version_did = previous_version_did

    @property
    def dda_container(self) -> DataDisclosureAgreementContainer:
        """Returns data disclosure agreement container"""
        return self._dda_container

    @property
    def next_version_did(self) -> str:
        """Returns next version did:mydata identifier"""
        return self._next_version_did

    @property
    def previous_version_did(self) -> str:
        """Returns previous version did:mydata identifier"""
        return self._previous_version_did

    @property
    def current_version_did(self) -> str:
        """Returns current version did:mydata identifier"""
        return self._dda_container.mydata_did
