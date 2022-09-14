import base64
import binascii
import typing

from aries_cloudagent.messaging.models.base import BaseModel
from dexa_sdk.jsonld.core import jsonld_context_fingerprint
from dexa_sdk.utils import jcs_rfc8785
from merklelib import MerkleTree
from multibase import encode
from pyld import jsonld


class DIDMyDataBuilder:
    """Builder for did:mydata identifier"""

    def __init__(
        self,
        *,
        artefact: BaseModel,
        did: str = None,
    ) -> None:
        """

        Args:
            artefact (BaseModel): MyData artefact for .e.g. DA, DDA
            did (str, optional): did:mydata identifier. Defaults to None.
        """
        self._artefact = artefact
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
        doc = self._artefact.serialize()

        # Convert the doc to nquads statements
        normalized = jsonld.normalize(doc, config)

        # Split normalised string into multiple statements
        normalized = normalized.split("\n")

        # Return the statements
        return normalized[:-1]

    def build_merkle_tree(self) -> MerkleTree:
        """Build merkle tree from nquads statements about the artefact

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
        return jcs_rfc8785(self._artefact.serialize())

    def base64(self) -> str:
        """Returns output string after performing base64 encoding
        on JSON Canonicalisation Schema (JCS) on the document.

        Returns:
            str: base64 encoded string
        """
        return base64.urlsafe_b64encode(self.jcs()).decode()

    def generate_did(self, context_type="DataAgreement") -> str:
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
        at = jsonld_context_fingerprint(context_type=context_type)

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
    def artefact(self) -> BaseModel:
        """Returns MyData artefact

        Returns:
            BaseModel: MyData artefact
        """
        return self._artefact


class DidMyData:
    def __init__(self, *, agreement_type: str, agreement_merkle_root: str) -> None:
        """
        Initialise the DidMydata class

        Args:
            agreement_type (str):
                SHA2-256 fingerprint of the agreement JSONLD context
            agreement_merkle_root (str):
                SHA2-256 merkle root for the agreement document

        Returns:
            None
        """
        self._agreement_type = agreement_type
        self._agreement_merkle_root = agreement_merkle_root

        # Generate did:mydata v2 identifier
        self._did = self.generate()

    def generate(self) -> str:
        """Create did:mydata v2 identifier"""
        # Agreement type sha256 fingerprint to bytes
        agreement_type_bytes = binascii.unhexlify(self._agreement_type)

        # Agreement merkle root sha256 fingerprint to bytes
        agreement_merkle_root_bytes = binascii.unhexlify(self._agreement_merkle_root)

        # 16 + 38 bytes = 48 byte method specific identifier
        identifier = agreement_type_bytes[:16] + agreement_merkle_root_bytes

        # Multibase encode
        identifier = encode("base58btc", identifier).decode()
        return f"did:mydata:{identifier}"

    @property
    def did(self) -> str:
        return self._did
