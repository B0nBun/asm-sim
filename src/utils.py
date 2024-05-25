from typing import NoReturn
import sys

_iota_cnt = 0


def iota() -> int:
    global _iota_cnt
    _iota_cnt += 1
    return _iota_cnt


def iota_reset() -> int:
    global _iota_cnt
    tmp = _iota_cnt + 1
    _iota_cnt = 0
    return tmp
