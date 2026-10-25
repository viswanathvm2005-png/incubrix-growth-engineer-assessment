"""Heuristic flags for factual-language review; not a truth detector."""

import re

_REVIEW_PATTERNS = (
    re.compile(
        r"\bwe\s+(?:tested|test|measure|measured|simulate|simulated|"
        r"examined|evaluate|evaluated|analyze|analysed|analyzed)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bthis\s+(?:assessment|analysis|review)\s+"
        r"(?:checks|checked|confirms|confirmed|demonstrates|demonstrated|"
        r"found|finds|shows|showed)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:results|testing|measurements)\s+(?:show|showed|prove|proved|"
        r"confirm|confirmed|demonstrate|demonstrated)\b",
        re.IGNORECASE,
    ),
)


def find_factual_language_flags(*texts: str) -> list[str]:
    """Return review warnings for wording that may imply completed testing.

    A match is only a review signal. It does not establish that a statement
    is false, and no match does not establish that content is factually true.
    """
    flags: list[str] = []

    for text in texts:
        if not text:
            continue

        for pattern in _REVIEW_PATTERNS:
            if pattern.search(text):
                message = (
                    "Potentially unsupported testing/result language; "
                    "verify against evidence before publication."
                )
                if message not in flags:
                    flags.append(message)
                break

    return flags
