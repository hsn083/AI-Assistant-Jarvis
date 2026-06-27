"""
Backend/NumberFix.py
====================
Shared utility: converts all Eastern/Arabic-Indic numerals in a string
to standard Western Arabic digits (0-9), and provides the system-prompt
rule that instructs the LLM to never produce Eastern numerals in the
first place.

Eastern numeral sets handled:
  • Extended Arabic-Indic  (U+0660–U+0669)  — ٠١٢٣٤٥٦٧٨٩
  • Arabic-Indic           (U+06F0–U+06F9)  — ۰۱۲۳۴۵۶۷۸۹  (Urdu/Persian/Pashto)
  • Devanagari             (U+0966–U+096F)  — ०१२३४५६७८९
  • Bengali                (U+09E6–U+09EF)  — ০১২৩৪৫৬৭৮৯
  • Gujarati               (U+0AE6–U+0AEF)
  • Gurmukhi               (U+0A66–U+0A6F)
  • Kannada                (U+0CE6–U+0CEF)
  • Malayalam              (U+0D66–U+0D6F)
  • Oriya                  (U+0B66–U+0B6F)
  • Tamil                  (U+0BE6–U+0BEF)
  • Telugu                 (U+0C66–U+0C6F)
  • Tibetan                (U+0F20–U+0F29)
  • Thai                   (U+0E50–U+0E59)
  • Myanmar                (U+1040–U+1049)
  • Khmer                  (U+17E0–U+17E9)
  • Mongolian              (U+1810–U+1819)
"""

import re

# ── Master translation table ───────────────────────────────────────────────────
# Maps every known Eastern/Indic digit codepoint to its Western equivalent.
_EASTERN_TO_WESTERN: dict[int, int] = {}

_DIGIT_RANGES = [
    0x0660,   # Extended Arabic-Indic  ٠١٢٣٤٥٦٧٨٩
    0x06F0,   # Arabic-Indic (Urdu)    ۰۱۲۳۴۵۶۷۸۹
    0x0966,   # Devanagari             ०१२३४५६७८९
    0x09E6,   # Bengali
    0x0A66,   # Gurmukhi
    0x0AE6,   # Gujarati
    0x0B66,   # Oriya
    0x0BE6,   # Tamil
    0x0C66,   # Telugu
    0x0CE6,   # Kannada
    0x0D66,   # Malayalam
    0x0E50,   # Thai
    0x0F20,   # Tibetan
    0x1040,   # Myanmar
    0x1090,   # Myanmar Shan
    0x17E0,   # Khmer
    0x1810,   # Mongolian
    0x1946,   # Limbu
    0x19D0,   # New Tai Lue
    0x1A80,   # Tai Tham Hora
    0x1A90,   # Tai Tham Tham
    0x1B50,   # Balinese
    0x1BB0,   # Sundanese
    0x1C40,   # Lepcha
    0x1C50,   # Ol Chiki
    0xA620,   # Vai
    0xA8D0,   # Saurashtra
    0xA900,   # Kayah Li
    0xA9D0,   # Javanese
    0xAA50,   # Cham
    0xABF0,   # Meetei Mayek
    0xFF10,   # Fullwidth digits  ０１２３４５６７８９
]

for _base in _DIGIT_RANGES:
    for _offset in range(10):
        _EASTERN_TO_WESTERN[_base + _offset] = ord('0') + _offset

_TRANSLATION_TABLE = str.maketrans(_EASTERN_TO_WESTERN)


def fix_numbers(text: str) -> str:
    """
    Replace every Eastern/Indic numeral in *text* with its Western digit.
    Also normalises the Eastern decimal separator ٫ (U+066B) to a period.
    All other characters are untouched.

    Examples
    --------
    >>> fix_numbers("۳۷۳٫۷۸ روپے")
    '373.78 روپے'
    >>> fix_numbers("آج کا درجہ حرارت ۳۴°C ہے")
    'آج کا درجہ حرارت 34°C ہے'
    """
    if not text:
        return text
    # Convert Eastern decimal separator to period first
    text = text.replace('\u066B', '.').replace('\u066C', ',')
    return text.translate(_TRANSLATION_TABLE)


# ── LLM instruction (add this to every system prompt) ─────────────────────────
NUMBER_FORMAT_RULE = (
    "\n*** NUMBER FORMATTING RULE (HIGHEST PRIORITY — NEVER IGNORE): "
    "Always write ALL numbers using standard Western Arabic digits (0-9). "
    "NEVER use Urdu, Arabic-Indic, Persian, or any Eastern numerals "
    "(۰۱۲۳۴۵۶۷۸۹ or ٠١٢٣٤٥٦٧٨٩ are FORBIDDEN). "
    "This applies to: prices, currency, dates, times, phone numbers, "
    "percentages, distances, temperatures, measurements, and every other "
    "numeric value. Keep the response language the same as the user's, "
    "but ALL digits must be 0-9. "
    "✅ Correct: 373.78 روپے فی لیٹر  "
    "❌ Wrong:   ۳۷۳٫۷۸ روپے فی لیٹر ***"
)


# ── Self-test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        ("۳۷۳٫۷۸ روپے",           "373.78 روپے"),
        ("۲۹۹٫۵ روپے",            "299.5 روپے"),
        ("آج ۳۴ ڈگری ہے",         "آج 34 ڈگری ہے"),
        ("٣٤٥ ڈالر",              "345 ڈالر"),
        ("رات ۱۰:۳۰ بجے",         "رات 10:30 بجے"),
        ("0-9 unchanged",         "0-9 unchanged"),
        ("price: ۱,۲۳,۴۵۶",      "price: 1,23,456"),
    ]
    all_pass = True
    for inp, expected in tests:
        result = fix_numbers(inp)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_pass = False
        print(f"{status}  Input:    {inp}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}\n")
    print("All tests passed ✅" if all_pass else "Some tests FAILED ❌")
