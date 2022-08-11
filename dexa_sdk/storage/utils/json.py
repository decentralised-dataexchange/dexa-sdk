import jcs
import ast
import typing


def jcs_rfc8785(data: typing.Union[list, dict]) -> bytes:
    """JSON canonicalisation schema as per IETF RFC 8785"""
    return jcs.canonicalize(data)


def jcs_bytes_to_pyobject(data: bytes) -> typing.Any:
    """Convert JCS bytes to <dict, list e.t.c>"""
    return ast.literal_eval(data.decode())
