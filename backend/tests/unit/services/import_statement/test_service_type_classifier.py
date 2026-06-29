from __future__ import annotations

import pytest

from app.services.import_statement.classifier import ServiceTypeClassifier


@pytest.mark.parametrize(
    ("purpose", "expected"),
    [
        ("Оплата за услуги по SEO-продвижению сайта", "SEO"),
        ("Настройка и сопровождение Директа с 13.07 по 12.08", "Директ"),
        ("Настройка и ведение кампании контекстной рекламы", "контекст"),
        ("услуги SERM 15.07-14.08", "SERM"),
        ("SMM-сопровождение проекта", "SMM"),
        ("Оплата за разработку личного кабинета по счету № 776", "разработка"),
        ("Финальный платеж за этап дизайна", "дизайн"),
        ("Оплата за разработку лендинга учебного проекта", "лендинг"),
        ("Ежемесячное сопровождение сайта и услуги наполнения", "сопровождение"),
        ("За маркетинговые услуги", "маркетинг"),
        ("За публикацию новых материалов на сайте", "публикация"),
        ("Размещение объявлений на сервисе \"Объявления\" (этап 1)", "объявления"),
        ("за подготовку коммерческих текстов", "тексты"),
        ("Оплата за программную лицензию по сч. № 790", "лицензия"),
        ("Авансовый платеж на создание презентации", "презентация"),
        ("Оплата за техническое сопровождение сайта", "сопровождение"),
    ],
)
def test_classifies_known_purposes(purpose: str, expected: str) -> None:
    assert ServiceTypeClassifier().classify(purpose) == expected


def test_returns_other_when_no_keyword_matches() -> None:
    assert ServiceTypeClassifier().classify("Оплата по счёту № 768 от 18 июля 2026 г.") == "прочее"


def test_classification_is_case_insensitive() -> None:
    assert ServiceTypeClassifier().classify("ОПЛАТА SEO-УСЛУГ") == "SEO"


def test_first_matching_keyword_wins() -> None:
    # When multiple keywords match, the priority order in the dictionary applies.
    # "разработк" precedes "дизайн" — designed for the "разработка и дизайн" case.
    result = ServiceTypeClassifier().classify("Услуги разработки и дизайна сайта")
    assert result == "разработка"
