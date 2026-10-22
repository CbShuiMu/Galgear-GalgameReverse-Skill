"""Only unsigned integer helpers needed by the adjacent original crypt.py.

Function excerpt from trigger-segfault/majiro-py, Robert Jordan, 2021.
MIT; see ../../../../licenses/majiro-py-MIT.txt.
GalSkill adaptation 2026-10-22: omit unrelated terminal/color/script helpers.
"""
from struct import pack, unpack


def unsigned_I(num: int) -> int:
    if num < 0:
        return unpack('=I', pack('=i', num))[0]
    return unpack('=I', pack('=I', num))[0]


def unsigned_Q(num: int) -> int:
    if num < 0:
        return unpack('=Q', pack('=q', num))[0]
    return unpack('=Q', pack('=Q', num))[0]
