import typing
import base64
from pyld import jsonld
from pydantic import BaseModel, PrivateAttr
from merklelib import MerkleTree
from .....did_mydata.core import DidMyData
from .....jsonld.core import jsonld_context_fingerprint
from .....storage.utils.json import jcs_rfc8785


class DataDisclosureAgreementBaseModel(BaseModel):
    """
    Base class for Data Disclosure Agreement models
    """
    class Config:
        allow_population_by_field_name = True

    # Store the merkle tree
    _merkle_tree: MerkleTree = PrivateAttr()

    # Store the did:mydata identifier
    _mydata_did: str = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)

        # Initialise with default values.
        self._merkle_tree = None
        self._mydata_did = None

    def to_json(self) -> str:
        """Generate a JSON representation of the document model."""
        return super().json(by_alias=True, exclude_none=True)

    def to_dict(self) -> dict:
        """Generate a dictionary representation of the document model."""
        return super().dict(by_alias=True, exclude_none=True)

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
        doc = self.to_dict()

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
        return jcs_rfc8785(self.to_dict())

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
            self.generate_did()
        return self._mydata_did

    @property
    def merkle_tree(self) -> MerkleTree:
        """Returns merkle tree"""
        if not self._merkle_tree:
            self.build_merkle_tree()
        return self._merkle_tree
