import binascii
from multibase import encode


class DidMyData:
    def __init__(self,
                 *,
                 agreement_type: str,
                 agreement_merkle_root: str) -> None:
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
        agreement_merkle_root_bytes = binascii.unhexlify(
            self._agreement_merkle_root)

        # 16 + 38 bytes = 48 byte method specific identifier
        identifier = agreement_type_bytes[:16] + agreement_merkle_root_bytes

        # Multibase encode
        identifier = encode('base58btc', identifier).decode()
        return f"did:mydata:{identifier}"

    @property
    def did(self) -> str:
        return self._did
