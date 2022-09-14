import typing
from asyncio import shield

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.issuer.base import BaseIssuer
from aries_cloudagent.ledger.base import BaseLedger


class IndyLegerConfigError(Exception):
    """Raised when ledger is misconfigured"""


async def create_schema_def_and_anchor_to_ledger(
    context: InjectionContext,
    schema_name: str,
    schema_version: str,
    attributes: typing.List[str],
) -> typing.Tuple[str, dict]:
    """
    Create scheme definition and anchor to ledger.

    Args:
        schema_name: Schema name.
        schema_version: Schema version.
        attributes: List of attributes.

    :return: (schema_id, schema_def)
    """

    # Ledger instance from context
    ledger: BaseLedger = await context.inject(BaseLedger, required=False)
    if not ledger:
        reason = "No ledger available"
        if not context.settings.get_value("wallet.type"):
            reason += ": missing wallet-type?"

        raise IndyLegerConfigError(f"{reason}")

    # Issuer instance from context
    issuer: BaseIssuer = await context.inject(BaseIssuer)

    async with ledger:
        # Create schema
        schema_name = schema_name
        schema_version = schema_version
        attributes = attributes

        schema_id, schema_def = await shield(
            ledger.create_and_send_schema(
                issuer, schema_name, schema_version, attributes
            )
        )

        return schema_id, schema_def


async def create_cred_def_and_anchor_to_ledger(
    context: InjectionContext,
    schema_id: str,
    tag: str = "default",
    support_revocation: bool = False,
) -> typing.Tuple[str, dict, bool]:
    """
    Create credential definition and anchor to ledger.

    Args:
        schema_id: Schema id.
        tag: Tag.
        support_revocation: Support revocation.

    Returns:
        :rtype: tuple: (credential definition id, credential definition json, support revocation)
    """

    # Ledger instance from context
    ledger: BaseLedger = await context.inject(BaseLedger, required=False)
    if not ledger:
        reason = "No ledger available"
        if not context.settings.get_value("wallet.type"):
            reason += ": missing wallet-type?"

        raise IndyLegerConfigError(f"{reason}")

    # Issuer instance from context
    issuer: BaseIssuer = await context.inject(BaseIssuer)

    tag = "default"
    support_revocation = False

    async with ledger:
        # Create credential definition
        (cred_def_id, cred_def, novel) = await shield(
            ledger.create_and_send_credential_definition(
                issuer,
                schema_id,
                signature_type=None,
                tag=tag,
                support_revocation=support_revocation,
            )
        )

        return cred_def_id, cred_def, novel
