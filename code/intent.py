"""Intent classifier: detects whether request_text authorizes personal data erasure."""

import re
from typing import Tuple

# Multilingual erasure / deletion keywords (stems and phrases)
# English, German, French, Spanish, Portuguese, Japanese, Korean, Italian, Dutch
DELETION_PATTERNS = [
    # English
    r"\bdelet(?:e|ed|ing|ion)?\b",
    r"\beras(?:e|ed|ing|ure)?\b",
    r"\bremov(?:e|ed|ing|al)?\b",
    r"\bclose\s+(?:my\s+|this\s+)?account\b",
    r"\bcancel\s+(?:my\s+|this\s+)?account\b",
    r"\bwipe\b",
    r"\bright\s+to\s+be\s+forgotten\b",
    r"\bright\s+to\s+erasure\b",
    r"\brtbf\b",
    # German (löschen, Löschung, vergessen werden)
    r"l[öo]sch(?:en|ung)?",
    r"vergessen\s+werden",
    # French (supprimer, suppression, effacer, effacement)
    r"supprim(?:er|e|é|ée|és|ées|ation)?",
    r"suppression",
    r"effac(?:er|ement)",
    # Spanish (eliminar, eliminación, borrar, borrado, supresión)
    r"eliminaci[oó]n",
    r"eliminar",
    r"borr(?:ar|ado)",
    r"supresi[oó]n",
    # Portuguese (excluir, exclusão, eliminação, apagar)
    r"exclus[aã]o",
    r"excluir",
    r"apag(?:ar|ado)",
    # Japanese (削除, 消去, 忘れられる権利)
    r"削除",
    r"消去",
    # Korean (삭제, 삭제 요청)
    r"삭제",
    # Dutch (verwijderen, verwijdering)
    r"verwijder(?:en|ing)?",
    # Italian (cancellare, cancellazione, eliminare)
    r"cancell(?:are|azione)",
]

# Explicit negative stems / non-deletion signals
# Requests for access, rectification, export, marketing opt-out, password help
EXPLICIT_NON_DELETION_PATTERNS = [
    r"not\s+asking\s+for\s+deletion",
    r"leave\s+the\s+account\s+active",
    r"keep\s+the\s+account",
    r"do\s+not\s+close\s+the\s+account",
    r"do\s+not\s+delete",
    r"don't\s+delete",
    r"without\s+removing\s+any\s+of\s+my\s+records",
    r"marketing\s+lists\s+only",
    r"stop\s+the\s+promotional\s+emails",
    r"not\s+a\s+request\s+to\s+erase",
    r"leave\s+my\s+profile\s+and\s+purchase\s+history",
    r"want\s+to\s+continue\s+using\s+the\s+service",
    r"download\s+my\s+account\s+information\s+in\s+a\s+portable\s+format",
    r"mobile\s+number\s+on\s+my\s+profile\s+is\s+out\s+of\s+date",
    r"surname\s+is\s+misspelled",
    r"can't\s+access\s+my\s+profile\s+and\s+need\s+help",
    r"what\s+personal\s+information\s+you\s+hold",
    r"copy\s+of\s+last\s+year's\s+invoices",
    r"copy\s+of\s+the\s+information\s+held",
]


def classify_intent(request_text: str) -> Tuple[str, str]:
    """Classifies request_text into ('ERASURE', reason) or ('NON_DELETION', reason).
    
    A request that authorizes deletion yields 'ERASURE'.
    A request for access, rectification, marketing opt-out, or explicitly negated
    deletion yields 'NON_DELETION'.
    """
    if not request_text:
        return "NON_DELETION", "Empty request text"

    text_lower = request_text.lower()

    # 1. Check explicit non-deletion signals first
    for pat in EXPLICIT_NON_DELETION_PATTERNS:
        if re.search(pat, text_lower, re.IGNORECASE):
            return "NON_DELETION", f"Matched non-deletion pattern: {pat}"

    # 2. Check erasure / deletion keywords across all languages
    for pat in DELETION_PATTERNS:
        if re.search(pat, text_lower, re.IGNORECASE):
            return "ERASURE", f"Matched deletion pattern: {pat}"

    # Default if no deletion intent found
    return "NON_DELETION", "No deletion authorization found in text"
