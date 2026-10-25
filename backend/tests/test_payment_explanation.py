from __future__ import annotations

import re

import pytest

from app.services.payment_explanation import compact_amount, explain_payment, ratio_text, strength


@pytest.fixture
def payment():
    return {
        'transaction_id': 'TX-002562',
        'vendor': 'Vendor-212',
        'agency': 'Education',
        'scheme': 'School Upgrade',
        'district': 'Kalaburagi',
        'amount_paise': 833656000,
        'date': '2024-04-14',
        'risk': 'Critical',
        'path_insight': {
            'amount_vs_vendor_mean': 7.652,
            'amount_vs_agency_mean': 12.271,
            'amount_vs_scheme_mean': 12.271,
            'vendor_transactions_30d': 1,
            'days_since_previous_vendor_payment': 365,
            'scheme_utilization': 0.0632,
            'fiscal_year': '2024-25',
        },
    }


@pytest.mark.parametrize(
    ('ratio', 'expected'),
    [
        (1.99, 'normal'),
        (2, 'elevated'),
        (4.99, 'elevated'),
        (5, 'high'),
        (9.99, 'high'),
        (10, 'very_high'),
        (None, 'normal'),
    ],
)
def test_thresholds(ratio, expected):
    assert strength(ratio)[0] == expected


@pytest.mark.parametrize(('value', 'text'), [(7.652, '7.7'), (12.271, '12'), (4.25, '4.3')])
def test_rounding(value, text):
    assert ratio_text(value) == text


@pytest.mark.parametrize(
    ('paise', 'text'),
    [
        (833656000, '₹83.4 lakh'),
        (1200000000, '₹1.2 crore'),
        (1, '₹0.01'),
        (0, '₹0.00'),
        (1000000000000, '₹1000.0 crore'),
    ],
)
def test_amount_units(paise, text):
    assert compact_amount(paise) == text


def test_fixture_strongest_first_merged_and_single_payment(payment):
    result = explain_payment(payment, {'first_payment': True})
    assert result.headline == (
        'Vendor-212 was paid ₹83.4 lakh by Education, '
        'about 12 times the typical payment in this agency and scheme.'
    )
    assert result.support == "It is also about 7.7 times this vendor's usual payment."
    assert result.check_first == 'Check: the sanction and approval for this amount.'
    assert result.signals[0].key == 'amount_vs_agency_scheme_mean'
    assert result.signals[1].key == 'amount_vs_vendor_mean'
    assert result.signals[0].strength == 'very_high'
    assert result.signals[1].strength == 'high'
    assert result.signals[2].value_text == '1 payment'
    assert result.signals[2].tag == 'Normal'
    assert result.signals[3].value_text == 'First payment on record'
    assert result.signals[4].value_text == '6.3%'
    assert '1 payments' not in result.model_dump_json()
    prose = f'{result.headline} {result.support} {result.check_first}'
    assert len(prose.split()) < 60
    assert all(len(sentence.split()) <= 20 for sentence in re.split(r'(?<!\d)\. ', prose))
    assert not re.search(r'\b(fraud|corruption|misuse|percentile|z-score)\b', result.model_dump_json())


def test_365_needs_history_and_is_not_always_first(payment):
    for context, text in [
        ({'first_payment': True}, 'First payment on record'),
        ({'first_payment': False}, '365 days (about 1 year)'),
        ({}, 'Earlier payment history unavailable'),
    ]:
        result = explain_payment(payment, context)
        assert next(r for r in result.signals if r.key.startswith('days_since')).value_text == text
    assert payment['path_insight']['days_since_previous_vendor_payment'] == 365


def test_baselines_use_real_means_and_fallback_is_marked(payment):
    result = explain_payment(payment, {'vendor_mean_paise': 100000000})
    vendor = next(r for r in result.signals if r.key == 'amount_vs_vendor_mean')
    assert vendor.baseline_text == '₹10.0 lakh'
    assert 'including this payment' in vendor.help_text
    result = explain_payment(payment)
    assert next(r for r in result.signals if r.key == 'amount_vs_vendor_mean').baseline_text.startswith(
        'About '
    )


def test_null_zero_and_unrecognized_signals(payment):
    payment['path_insight'] = {
        'amount_vs_vendor_mean': None,
        'amount_vs_agency_mean': 0,
        'amount_vs_scheme_mean': float('nan'),
        'vendor_transactions_30d': 2,
    }
    result = explain_payment(payment)
    assert result.headline == 'No single signal stands out; flagged on the combined pattern.'
    assert result.support is None
    assert all(r.ratio is None for r in result.signals)
    assert result.signals[-1].value_text == '2 payments'
    payment['path_insight'] = None
    assert explain_payment(payment).support is None


def test_frequency_and_stable_ties(payment):
    payment['path_insight'] = {'vendor_transactions_30d': 3}
    result = explain_payment(payment)
    assert result.headline == 'The vendor received 3 payments in 30 days.'
    assert result.check_first == 'Check: whether payments were split.'
    payment['path_insight'] = {'amount_vs_vendor_mean': 5, 'amount_vs_agency_mean': 5}
    result = explain_payment(payment)
    assert result.signals[0].key == 'amount_vs_vendor_mean'
    assert result.check_first == "Check: this vendor's earlier invoices."


def test_long_names_keep_explanation_short_and_names_intact(payment):
    payment['vendor'] = ' '.join(['Vendor'] * 25)
    result = explain_payment(payment)
    assert result.headline.startswith('This payment is about 12 times')
    assert payment['vendor'] == ' '.join(['Vendor'] * 25)
    assert len(f'{result.headline} {result.support} {result.check_first}'.split()) < 60
