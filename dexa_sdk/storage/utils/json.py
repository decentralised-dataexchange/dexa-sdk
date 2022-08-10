import typing
import jcs
import ast
from collections import OrderedDict


def jcs_rfc8785(data: dict) -> bytes:
    """JSON canonicalisation schema as per IETF RFC 8785"""
    return jcs.canonicalize(data)


def jcs_bytes_to_ordered_dict(data: bytes) -> typing.OrderedDict:
    """Convert JCS bytes to OrderedDict"""
    return OrderedDict(ast.literal_eval(data.decode()))
