import datetime
import hashlib
import uuid

import requests
from aries_cloudagent.messaging.jsonld.credential import (
    sign_credential,
    verify_credential,
)
from aries_cloudagent.wallet.base import BaseWallet
from dexa_sdk.jsonld.exceptions import ProofNotAvailableException
from dexa_sdk.utils import (
    jcs_rfc8785,
    replace_jws,
    replace_proof_chain,
    replace_proof_value,
)
from merklelib import utils

DEXA_JSONLD_CONTEXT_URL = (
    "https://raw.githubusercontent.com"
    "/decentralised-dataexchange"
    "/data-exchange-agreements/main/interface-specs"
    "/jsonld/contexts/dexa-context.jsonld"
)


def fetch_jsonld_context_from_remote(
    context_type: str = None, remote_context_url: str = DEXA_JSONLD_CONTEXT_URL
) -> dict:
    """
    Fetch JSONLD context from remote

    Args:
        context_type (str): Specific JSONLD context type
        remote_context_url (str): Remote JSONLD context URL

    Returns:
        jresp (dict): JSONLD context
    """
    # Perform HTTP GET against remote context URL
    req = requests.get(remote_context_url)
    assert req.status_code == 200, "Failed to fetch JSONLD context from remote."
    # JSON response
    jresp = req.json()
    # Return context
    return jresp if not context_type else jresp.get("@context", {}).get(context_type)


def jsonld_context_fingerprint(
    context_type: str = None, remote_context_url: str = DEXA_JSONLD_CONTEXT_URL
) -> str:
    """Returns the fingerprint (SHA2-256) of JSON-LD context

    Args:
        context_type (str, optional): JSONLD context type. Defaults to None.
        remote_context_url (str, optional): Remote context URL. Defaults to DEXA_JSONLD_CONTEXT_URL.

    Returns:
        str: SHA2-256 finger for the jsonld document
    """
    # Fetch context from remote
    jsonld_context = fetch_jsonld_context_from_remote(context_type, remote_context_url)
    # Canonicalise the context document
    jcs = jcs_rfc8785(jsonld_context)
    # Convert bytes to string
    value = utils.to_string(jcs)
    # Return the SHA2-256 hexdigest
    return hashlib.sha256(value).hexdigest()


async def sign_proof(
    *, proof, verkey: str, wallet: BaseWallet, signature_options: dict = None
) -> dict:
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
    if not signature_options:
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


async def sign_agreement(
    *, agreement: dict, verkey: str, wallet: BaseWallet, signature_options: dict = None
) -> None:
    """Sign agreement.

    Create proof algorithm is defined at w3c vc data integrity 1.0 spec.

    Args:
        verkey (str): public key
        wallet (BaseWallet): wallet instance
    """

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

        signed_proof = await sign_proof(
            proof=tbs, verkey=verkey, wallet=wallet, signature_options=signature_options
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
        if not signature_options:
            signature_options = {
                "id": f"urn:uuid:{str(uuid.uuid4())}",
                "verificationMethod": verkey,
                "proofPurpose": "authentication",
                "created": datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }

        # Sign the agreement
        agreement = await sign_credential(agreement, signature_options, verkey, wallet)

        # Replace 'jws' field with 'proofValue' field
        agreement["proof"] = replace_jws(agreement["proof"].copy())

    # Return agreement with proofs
    return agreement


async def verify_agreement(*, agreement: dict, wallet: BaseWallet) -> bool:
    """Verify agreement

    Args:
        verkey (str): public key
        wallet (BaseWallet): wallet instance

    Returns:
        bool: Validity of the agreement
    """

    # To be verified agreement
    tbv = agreement

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
            valid.append(
                await verify_credential(tbv, tbv["proof"]["verificationMethod"], wallet)
            )
        else:
            # From second proof onwards, tbv would be the proof before it.
            tbv = {**proofs[index - 1], "@context": "https://w3id.org/security/v2"}
            tbv = replace_proof_value(tbv.copy())
            tbv["proof"] = replace_proof_value(proof.copy())
            valid.append(
                await verify_credential(tbv, tbv["proof"]["verificationMethod"], wallet)
            )

    return all(valid)
