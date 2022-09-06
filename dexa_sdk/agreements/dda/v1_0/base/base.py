import typing
import base64
from pyld import jsonld
from merklelib import MerkleTree
from abc import ABC
from .....did_mydata.core import DidMyData
from .....jsonld.core import jsonld_context_fingerprint
from .....utils import jcs_rfc8785
from ..models.dda_models import DataDisclosureAgreementModel


class BaseDataDisclosureAgreementTemplate(ABC):
    """Base data disclosure agreement template"""

    def __init__(
        self,
        *,
        dda: DataDisclosureAgreementModel,
        did: str = None,
    ) -> None:
        """Initialise a new BaseDataDisclosureAgreementTemplate

        Args:
            dda (DataDisclosureAgreementModel): data disclosure agreement model
            did (str, optional): did:mydata identifier. Defaults to None.
        """

        self._dda = dda
        self._mydata_did = did
        self._merkle_tree = None

    def nquads(self) -> typing.List[str]:
        """JSON-LD normalise document using URDNA2015.
        For reference: https://json-ld.github.io/normalization/spec/

        Returns:
            typing.List[str]: n-quads statements
        """

        # Config for JSONLD normalisation
        config = {"algorithm": "URDNA2015", "format": "application/n-quads"}

        # Obtains the dictionary representation of the document
        doc = self._dda.serialize()

        # Convert the doc to nquads statements
        normalized = jsonld.normalize(doc, config)

        # Split normalised string into multiple statements
        normalized = normalized.split("\n")

        # Return the statements
        return normalized[:-1]

    def build_merkle_tree(self) -> MerkleTree:
        """Build merkle tree from nquads statements about the agreement

        Returns:
            MerkleTree: merkle tree
        """
        # Normalise document to n-quads
        data = self.nquads()

        # Build merkle tree
        mt = MerkleTree(data)

        # Store the merkle tree in the instance
        self._merkle_tree = mt

        return mt

    def jcs(self) -> bytes:
        """Canonicalise the agreement using JCS IETF RFC8785

        Returns:
            bytes: jcs bytes
        """
        return jcs_rfc8785(self._dda.serialize())

    def base64(self) -> str:
        """Returns output string after performing base64 encoding
        on JSON Canonicalisation Schema (JCS) on the document.

        Returns:
            str: base64 encoded string
        """
        return base64.urlsafe_b64encode(self.jcs()).decode()

    def generate_did(self) -> str:
        """
        Generate the did:mydata identifier for the agreement

        Returns:
            did (str): did:mydata identifier
        """

        # Merkle tree
        mt = self.build_merkle_tree()

        # Merkle root (sha256 fingerprint)
        mr = mt.merkle_root

        # Obtain SHA2-256 fingerprint for agreement JSONLD context
        at = jsonld_context_fingerprint(context_type="DataDisclosureAgreement")

        # Create did:mydata v2 identifier
        mydata_did = DidMyData(agreement_type=at, agreement_merkle_root=mr)
        did = mydata_did.did

        # Store the did:mydata identifier in the instance
        self._mydata_did = did

        return did

    @property
    def mydata_did(self) -> str:
        """Returns did:mydata identifier

        Returns:
            str: did:mydata identifier
        """
        # If did:mydata identifier not generated.
        if not self._mydata_did:
            # Generate did:mydata identifier
            return self.generate_did()
        return self._mydata_did

    @mydata_did.setter
    def mydata_did(self, did: str) -> None:
        """Set did:mydata identifier

        Args:
            did (str): did:mydata identifier
        """
        self._mydata_did = did

    @property
    def merkle_tree(self) -> MerkleTree:
        """Returns merkle tree

        Returns:
            MerkleTree: merkle tree
        """
        # If merkle tree not available
        if not self._merkle_tree:
            # Build merkle tree and return it.
            return self.build_merkle_tree()
        return self._merkle_tree

    @property
    def merkle_root(self) -> str:
        """Returns merkle root

        Returns:
            str: merkle root
        """
        return self.merkle_tree.merkle_root

    @property
    def dda(self) -> DataDisclosureAgreementModel:
        """Returns data disclosure agreement

        Returns:
            DataDisclosureAgreementModel: data disclosure agreement
        """
        return self._dda
