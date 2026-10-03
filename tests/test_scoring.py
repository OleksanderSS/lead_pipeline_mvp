"""The scoring rules and the budget buckets they depend on."""
import pytest

from classifier import classify_lead
from normalizer import normalize_lead


def _lead(**fields):
    base = {"name": "test", "email": "a@gmail.com"}
    base.update(fields)
    return normalize_lead(base)


def test_a_full_business_lead_is_hot():
    lead = _lead(email="cto@acme.io", company="Acme", phone="0671234567",
                 message="We need a CRM integration for 15 sales managers, by end of quarter.",
                 budget="5000")
    result = classify_lead(lead)
    assert result["score"] == 30 + 20 + 20 + 15 + 10
    assert result["label"] == "HOT"


def test_a_bare_lead_is_cold_with_no_reasons():
    result = classify_lead(_lead(message="hi"))
    assert result == {"score": 0, "label": "COLD", "reasons": []}


def test_the_label_boundaries():
    assert classify_lead(_lead(company="Acme", email="a@acme.io", budget="100"))["score"] == 45
    assert classify_lead(_lead(company="Acme", email="a@acme.io", budget="100"))["label"] == "WARM"
    assert classify_lead(_lead(company="Acme"))["label"] == "WARM"  # exactly 30
    assert classify_lead(_lead(phone="0671234567"))["label"] == "COLD"  # 20


@pytest.mark.parametrize("raw, bucket", [
    ("5000", "$2k–$10k"),
    ("5 000 грн", "$2k–$10k"),
    ("$5,000", "$2k–$10k"),
    ("5k", "$2k–$10k"),
    ("1.5k", "$500–$2k"),
    ("$2k–$10k", "$2k–$10k"),      # the form's own dropdown label
    ("$50k+", "$50k+"),
    ("about budget 3000", "$2k–$10k"),
    ("300", "< $500"),
])
def test_budget_text_lands_in_the_right_bucket(raw, bucket):
    assert _lead(budget=raw)["budget"] == bucket


def test_a_budget_without_a_number_is_kept_as_written():
    assert _lead(budget="не знаю")["budget"] == "не знаю"


def test_a_dropdown_budget_earns_the_high_budget_points():
    result = classify_lead(_lead(budget="$2k–$10k"))
    assert "budget $2k–$10k" in result["reasons"]
