"""Deterministic Chinese-number normalization for ASR output.

ASR models frequently emit Chinese numerals ("二零二五", "三千五百").
Prompts alone are not reliable, especially when the correction model is
unavailable or conservatively preserves the source.  This module converts the
high-confidence number patterns that appear in dictation, while leaving idioms
such as 一起 / 一直 / 十分重要 untouched.
"""

from __future__ import annotations

import re

_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_DIGIT_CHARS = "零〇一二三四五六七八九两"
_UNITS = {"十": 10, "百": 100, "千": 1000}
_BIG_UNITS = {"万": 10_000, "亿": 100_000_000}
_CHINESE_NUMBER = rf"[负]?[{_DIGIT_CHARS}十百千万亿]+(?:点[{_DIGIT_CHARS}]+)?"


def _parse_integer(token: str) -> str:
    token = token.lstrip("负")
    if not any(ch in token for ch in "十百千万亿"):
        # A pure digit string: keep leading zeroes (years, phone numbers).
        return "".join(str(_DIGITS[ch]) for ch in token if ch in _DIGITS)
    total = 0
    section = 0
    number = 0
    for char in token:
        if char in _DIGITS:
            number = _DIGITS[char]
        elif char in _UNITS:
            if number == 0:
                number = 1
            section += number * _UNITS[char]
            number = 0
        elif char in _BIG_UNITS:
            section += number
            number = 0
            if char == "万":
                total += section * 10_000
            else:
                total = (total + section) * 100_000_000
            section = 0
    return str(total + section + number)


def _parse_number(token: str) -> str:
    negative = token.startswith("负")
    token = token.lstrip("负")
    if "点" in token:
        whole, fraction = token.split("点", 1)
        whole_value = _parse_integer(whole) if whole else "0"
        fraction_value = "".join(
            str(_DIGITS[ch]) for ch in fraction if ch in _DIGITS
        )
        value = f"{whole_value}.{fraction_value or '0'}"
    else:
        value = _parse_integer(token)
    return f"-{value}" if negative else value


def _replace_percent(match: re.Match[str]) -> str:
    return f"{_parse_number(match.group(1))}%"


def _replace_number(match: re.Match[str]) -> str:
    return _parse_number(match.group(1))


def normalize_numbers(text: str) -> str:
    """Convert high-confidence Chinese number phrases to Arabic numerals."""
    if not text:
        return text
    result = text

    # Percentages first, so "百分之三十" does not become "百分之30".
    result = re.sub(rf"百分之({_CHINESE_NUMBER})", _replace_percent, result)

    # Four-digit year: 二零二五 -> 2025.
    result = re.sub(
        rf"([零〇一二三四五六七八九]{{4}})年",
        lambda m: f"{_parse_number(m.group(1))}年",
        result,
    )

    # Month / day: 十一月七日 -> 11月7日.
    result = re.sub(
        rf"({_CHINESE_NUMBER})月({_CHINESE_NUMBER})([日号])",
        lambda m: f"{_parse_number(m.group(1))}月{_parse_number(m.group(2))}{m.group(3)}",
        result,
    )

    # Phone-like long digit sequences: 一三八... -> 138...
    result = re.sub(
        rf"(?<![零〇一二三四五六七八九两])([零〇一二三四五六七八九]{{7,}})(?![零〇一二三四五六七八九两])",
        lambda m: _parse_integer(m.group(1)),
        result,
    )

    # General number + measure word, amount, date component, etc.
    units = (
        "块|元|岁|个|人|位|天|年|小时|分钟|秒|米|公里|公斤|斤|克|升|毫升|"
        "度|次|遍|倍|层|楼|页|张|本|台|件|套|条|只|头|匹|角|毛"
    )
    result = re.sub(
        rf"({_CHINESE_NUMBER})({units})",
        lambda m: f"{_parse_number(m.group(1))}{m.group(2)}",
        result,
    )

    return result
