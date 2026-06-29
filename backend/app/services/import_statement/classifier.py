"""Maps a free-form payment purpose to a canonical service type."""

from __future__ import annotations

# Order matters — the first matching substring wins. Listing more specific
# terms before generic ones means "разработка" beats "дизайн" when both appear.
_KEYWORD_MAP: tuple[tuple[str, str], ...] = (
    ("seo", "SEO"),
    ("директ", "Директ"),
    ("контекст", "контекст"),
    ("serm", "SERM"),
    ("smm", "SMM"),
    ("лендинг", "лендинг"),
    ("разработк", "разработка"),
    ("дизайн", "дизайн"),
    ("сопровожден", "сопровождение"),
    ("маркетинг", "маркетинг"),
    ("публикац", "публикация"),
    ("объявлен", "объявления"),
    ("копирайт", "тексты"),
    ("текст", "тексты"),
    ("лицензи", "лицензия"),
    ("презентац", "презентация"),
)

OTHER = "прочее"


class ServiceTypeClassifier:
    """Keyword-based classifier for payment purposes.

    Deliberately simple — keywords are tuned to the test PDF's wording. A future
    LLM-based classifier could replace this without touching call sites.
    """

    def classify(self, payment_purpose: str) -> str:
        haystack = payment_purpose.lower()
        for needle, service_type in _KEYWORD_MAP:
            if needle in haystack:
                return service_type
        return OTHER
