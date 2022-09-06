import uuid
import datetime
from aries_cloudagent.wallet.base import BaseWallet
from aries_cloudagent.messaging.jsonld.credential import (
    sign_credential,
    verify_credential,
)
from ..base import BaseDataDisclosureAgreementTemplate
from ..models import DataDisclosureAgreementModel
from .....utils import replace_jws, replace_proof_value, replace_proof_chain


class ProofNotAvailableException(Exception):
    """Raised when proof or proof chain is not present in the agreement"""

    pass


class DataDisclosureAgreementInstance(BaseDataDisclosureAgreementTemplate):
    """
    Class for managing a data disclosure agreement instance
    """

    async def sign_proof(self, *, proof, verkey: str, wallet: BaseWallet) -> dict:
        """Sign embedded proof in agreement to generated counter signatures chain

        Create proof algorithm is defined at w3c vc data integrity 1.0 spec.

        Args:
            verkey (str): public key
            wallet (BaseWallet): wallet instance

        Returns:
            dict: proof of proof (counter signed proof)
        """
        # Signature options.
        # verification method should be did:key identifier
        signature_options = {
            "id": f"urn:uuid:{str(uuid.uuid4())}",
            "verificationMethod": verkey,
            "proofPurpose": "authentication",
            "created": datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }

        # Add security context to the proof.
        proof_with_context = {
            **proof,
            "@context": "https://w3id.org/security/v2",
        }

        # Sign the proof document
        proof_with_proof = await sign_credential(
            proof_with_context, signature_options, verkey, wallet
        )

        # Replace 'jws' field with 'proofValue' field
        proof = replace_jws(proof_with_proof["proof"].copy())

        return proof

    async def sign_agreement(self, *, verkey: str, wallet: BaseWallet) -> None:
        """Sign agreement.

        Create proof algorithm is defined at w3c vc data integrity 1.0 spec.

        Args:
            verkey (str): public key
            wallet (BaseWallet): wallet instance
        """

        # To be signed agreement
        agreement = self.serialize()

        # Check if proof chain
        if "proof" in agreement:
            proof = [agreement["proof"]]
        elif "proofChain" in agreement:
            proof = agreement["proofChain"]
        else:
            proof = None

        if proof:
            # To be signed
            tbs = proof[-1].copy()

            # Replace 'proofValue' field with 'jws' field
            tbs = replace_proof_value(tbs)

            signed_proof = await self.sign_proof(
                proof=tbs, verkey=verkey, wallet=wallet
            )
            proof.append(signed_proof)

            # del 'proof' in agreement
            if "proof" in agreement:
                del agreement["proof"]

            # Replace 'proofChain' with new proofs
            agreement["proofChain"] = proof
        else:
            # Signature options.
            # verification method should be did:key identifier
            signature_options = {
                "id": f"urn:uuid:{str(uuid.uuid4())}",
                "verificationMethod": verkey,
                "proofPurpose": "authentication",
                "created": datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }

            # Sign the agreement
            agreement = await sign_credential(
                agreement, signature_options, verkey, wallet
            )

            # Replace 'jws' field with 'proofValue' field
            agreement["proof"] = replace_jws(agreement["proof"].copy())

        # Build a new DDA from the doc with proofs
        dda = DataDisclosureAgreementModel.deserialize(agreement)

        # Update the dda
        self._dda = dda

    async def verify_agreement(self, *, verkey: str, wallet: BaseWallet) -> bool:
        """Verify agreement

        Args:
            verkey (str): public key
            wallet (BaseWallet): wallet instance

        Returns:
            bool: Validity of the agreement
        """

        # To be verified agreement
        tbv = self.serialize()

        # Check if proof chain
        proofs = None
        if "proof" in tbv:
            proofs = [tbv["proof"]]
        elif "proofChain" in tbv:
            proofs = tbv["proofChain"]
            # Replace 'proofChain' field with 'proof' field
            tbv = replace_proof_chain(tbv.copy())
        else:
            raise ProofNotAvailableException("Proof or proof chain is not present")

        valid = []
        # Iterate through the proofs
        for index, proof in enumerate(proofs):
            if index == 0:
                # First proof in the chain
                # Replace 'proofValue' field with 'jws' field
                tbv["proof"] = replace_proof_value(proofs[0].copy())
                valid.append(await verify_credential(tbv, verkey, wallet))
            else:
                # From second proof onwards, tbv would be the proof before it.
                tbv = {**proofs[index - 1], "@context": "https://w3id.org/security/v2"}
                tbv = replace_proof_value(tbv.copy())
                tbv["proof"] = replace_proof_value(proof.copy())
                valid.append(await verify_credential(tbv, verkey, wallet))

        return all(valid)
