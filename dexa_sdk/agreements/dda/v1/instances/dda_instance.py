import typing
import base64
from pyld import jsonld
from merklelib import MerkleTree
from ..models.dda_models import DataDisclosureAgreementModel
from .....did_mydata.core import DidMyData
from .....jsonld.core import jsonld_context_fingerprint
from .....storage.utils.json import jcs_rfc8785


class DataDisclosureAgreementInstance:
    """
    Class for managing a data disclosure agreement instance
    """

    def __init__(self, dda: DataDisclosureAgreementModel, did: str = None):

        # Set class attributes
        self._dda = dda
        self._merkle_tree = None
        self._mydata_did = did

    def nquads(self) -> typing.List[str]:
        """
        JSON-LD normalise document using URDNA2015.
        For reference: https://json-ld.github.io/normalization/spec/

        Returns:
            List of n-quad statements
        """

        # Config for JSONLD normalisation
        config = {'algorithm': 'URDNA2015', 'format': 'application/n-quads'}

        # Obtains the dictionary representation of the document
        doc = self._dda.serialize()

        # Convert the doc to nquads statements
        normalized = jsonld.normalize(doc, config)

        # Split normalised string into multiple statements
        normalized = normalized.split("\n")

        # Return the statements
        return normalized[:-1]

    def build_merkle_tree(self) -> MerkleTree:
        """
        Build merkle tree from nquads statements about the agreement

        Returns:
            mt (MerkleTree):
                Merkle tree from nquads statements

        """
        # Normalise document to n-quads
        data = self.nquads()

        # Build merkle tree
        mt = MerkleTree(data)

        # Store the merkle tree in the instance
        self._merkle_tree = mt

        return mt

    def jcs(self) -> bytes:
        """Canonicalise the agreement using JCS IETF RFC8785"""
        return jcs_rfc8785(self._dda.serialize())

    def base64(self) -> str:
        """
        Returns output string after performing base64 encoding
        on JSON Canonicalisation Schema (JCS) on the document.
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
        """Returns did:mydata identifier"""
        if not self._mydata_did:
            return self.generate_did()
        return self._mydata_did

    @mydata_did.setter
    def mydata_did(self, did: str) -> None:
        """Set did:mydata identifier"""
        self._mydata_did = did

    @property
    def merkle_tree(self) -> MerkleTree:
        """Returns merkle tree"""
        if not self._merkle_tree:
            return self.build_merkle_tree()
        return self._merkle_tree

    @property
    def merkle_root(self) -> str:
        """Returns merkle root"""
        return self.merkle_tree.merkle_root
