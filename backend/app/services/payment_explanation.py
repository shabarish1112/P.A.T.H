"""Deterministic presentation only; never changes stored features or model decisions."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

from app.schemas.explanations import PaymentExplanation, SignalEvidence

VERY_HIGH_RATIO = 10
HIGH_RATIO = 5
ELEVATED_RATIO = 2
SUMMARY_FREQUENCY_MIN = 3
FIRST_PAYMENT_SENTINEL = 365
CRITICAL_HELP = 'Critical = in the top 1% of risk scores in this run. It is not a confirmed finding.'


def number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def rounded(value: float, places: int = 1) -> str:
    quantum = Decimal('0.1') if places else Decimal('1')
    return str(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP))


def ratio_text(value: float) -> str:
    return rounded(value, 1 if value < 10 else 0)


def compact_amount(paise: int | float) -> str:
    rupees = paise / 100
    if abs(rupees) >= 10_000_000:
        return f'₹{rounded(rupees / 10_000_000)} crore'
    if abs(rupees) >= 100_000:
        return f'₹{rounded(rupees / 100_000)} lakh'
    return f'₹{rupees:,.2f}'


def strength(value: float | None) -> tuple[Literal['very_high', 'high', 'elevated', 'normal'], str]:
    if value is not None and value >= VERY_HIGH_RATIO:
        return 'very_high', 'Very high'
    if value is not None and value >= HIGH_RATIO:
        return 'high', 'High'
    if value is not None and value >= ELEVATED_RATIO:
        return 'elevated', 'Elevated'
    return 'normal', 'Normal' if value is not None else 'Unavailable'


def comparison_help(group: str, ratio: float | None, derived: bool) -> str:
    comparison = {
        'vendor': 'the average amount paid to this vendor',
        'agency': 'the average payment made by this agency',
        'scheme': 'the average payment under this scheme',
        'agency_scheme': 'the average payment amount in this agency and scheme',
    }[group]
    if ratio is None:
        return 'There is not enough information to compare this amount with other payments in your file.'
    estimate = ' The average shown is an estimate.' if derived else ''
    return (
        f'This payment is about {ratio_text(ratio)} times {comparison}. '
        f'The average uses your uploaded file, including this payment.{estimate}'
    )


def explain_payment(
    doc: dict[str, Any], context: dict[str, Any] | None = None, *, selected_for_review: bool = True
) -> PaymentExplanation:
    context = context or {}
    raw = doc.get('path_insight') or {}
    amount = number(doc.get('amount_paise'))
    amount_display = compact_amount(amount) if amount is not None else 'Amount unavailable'
    rows: list[SignalEvidence] = []
    comparisons: dict[str, str] = {}
    for group, label, comparison in (
        ('vendor', "Vendor's usual payment", "this vendor's usual payment"),
        ('agency', 'Typical agency payment', 'the typical payment in this agency'),
        ('scheme', 'Typical scheme payment', 'the typical payment in this scheme'),
    ):
        key = f'amount_vs_{group}_mean'
        ratio = number(raw.get(key))
        ratio = ratio if ratio is not None and ratio > 0 else None
        baseline = number(context.get(f'{group}_mean_paise'))
        derived = baseline is None
        # Historic runs store rounded ratios, not means; division is an approximate fallback only.
        if derived and ratio is not None and amount is not None:
            baseline = amount / ratio
        baseline_text = (
            f'{"About " if derived else ""}{compact_amount(baseline)}'
            if baseline is not None and baseline > 0
            else 'Baseline unavailable'
        )
        level, tag = strength(ratio)
        rows.append(
            SignalEvidence(
                key=key,
                label=label,
                value_text=amount_display,
                baseline_text=baseline_text,
                ratio=ratio,
                multiple_text=f'About {ratio_text(ratio)}x' if ratio is not None else None,
                strength=level,
                tag=tag,
                help_text=comparison_help(group, ratio, derived),
            )
        )
        comparisons[key] = comparison
    agency, scheme = rows[1:3]
    if agency.ratio is not None and agency.ratio == scheme.ratio:
        agency.key = 'amount_vs_agency_scheme_mean'
        agency.label = 'Typical agency and scheme payment'
        comparisons[agency.key] = 'the typical payment in this agency and scheme'
        agency.help_text = comparison_help(
            'agency_scheme',
            agency.ratio,
            number(context.get('agency_mean_paise')) is None
            or number(context.get('scheme_mean_paise')) is None,
        )
        if agency.baseline_text != scheme.baseline_text:
            agency.baseline_text = f'Agency: {agency.baseline_text}; scheme: {scheme.baseline_text}'
        rows.remove(scheme)
    rows.sort(key=lambda row: row.ratio if row.ratio is not None else -1, reverse=True)
    candidates = [row for row in rows if row.ratio is not None and row.ratio >= ELEVATED_RATIO]
    frequency = number(raw.get('vendor_transactions_30d'))
    frequency = frequency if frequency is not None and frequency >= 0 and frequency.is_integer() else None
    if frequency is not None:
        count = int(frequency)
        rows.append(
            SignalEvidence(
                key='vendor_transactions_30d',
                label='Vendor payments in 30 days',
                value_text=f'{count} payment{"" if count == 1 else "s"}',
                baseline_text='30-day window ending on this payment, including this payment',
                tag='Worth checking' if count >= SUMMARY_FREQUENCY_MIN else 'Normal',
                strength='elevated' if count >= SUMMARY_FREQUENCY_MIN else 'normal',
                help_text=(
                    f'This vendor received {count} payment{"" if count == 1 else "s"} '
                    'in the 30 days up to this transaction, including this payment. '
                    'This count alone does not show a problem.'
                ),
            )
        )
    gap = number(raw.get('days_since_previous_vendor_payment'))
    if gap is not None and gap >= 0:
        first = context.get('first_payment')
        gap_text = f'{gap:g} days' if gap != 1 else '1 day'
        if gap == FIRST_PAYMENT_SENTINEL:
            gap_text = (
                'First payment on record'
                if first is True
                else '365 days (about 1 year)'
                if first is False
                else 'Earlier payment history unavailable'
            )
        if gap == FIRST_PAYMENT_SENTINEL and first is True:
            gap_help = (
                'This is the earliest payment to this vendor in your uploaded file. '
                'Your file does not tell us whether the vendor was paid before that.'
            )
        elif gap == FIRST_PAYMENT_SENTINEL and first is None:
            gap_help = (
                "We cannot tell from the available history whether this is the vendor's first payment "
                'or a year-long gap between payments.'
            )
        else:
            gap_help = (
                f'The uploaded records show {gap_text} between this payment '
                "and this vendor's previous payment."
            )
        rows.append(
            SignalEvidence(
                key='days_since_previous_vendor_payment',
                label='Previous vendor payment',
                value_text=gap_text,
                baseline_text='Within this uploaded dataset',
                tag='Context',
                help_text=gap_help,
            )
        )
    utilization = number(raw.get('scheme_utilization'))
    if utilization is not None and utilization >= 0:
        rows.append(
            SignalEvidence(
                key='scheme_utilization',
                label='Scheme spending against supplied sanction',
                value_text=f'{rounded(utilization * 100)}%',
                baseline_text='Largest supplied sanction for this scheme and financial year',
                tag='Context',
                help_text=(
                    'Up to and including this payment, the recorded scheme payments add up to '
                    f'{rounded(utilization * 100)}% of the highest approved amount listed '
                    'for this scheme and financial year. This uses only the amounts in your file.'
                ),
            )
        )
    support = None
    if candidates:
        lead = candidates[0]
        paid = (
            f'{doc.get("vendor", "Vendor unavailable")} was paid {amount_display} '
            f'by {doc.get("agency", "Agency unavailable")}'
        )
        comparison = f'about {ratio_text(lead.ratio or 0)} times {comparisons[lead.key]}.'
        headline = f'{paid}, {comparison}'
        if len(headline.split()) > 20:
            headline = f'{paid}. The amount is {comparison}'
        if len(paid.split()) > 20:
            # Full supplied names remain in the record header/context, without truncation.
            headline = f'This payment is {comparison}'
        if len(candidates) > 1:
            second = candidates[1]
            support = f'It is also about {ratio_text(second.ratio or 0)} times {comparisons[second.key]}.'
        elif frequency is not None and frequency >= SUMMARY_FREQUENCY_MIN:
            support = f'The vendor received {int(frequency)} payments in 30 days.'
        action = (
            "this vendor's earlier invoices"
            if lead.key == 'amount_vs_vendor_mean'
            else 'the sanction and approval for this amount'
        )
    elif frequency is not None and frequency >= SUMMARY_FREQUENCY_MIN:
        headline = f'The vendor received {int(frequency)} payments in 30 days.'
        action = 'whether payments were split'
    else:
        headline = (
            'No single signal stands out; flagged on the combined pattern.'
            if selected_for_review
            else 'No individual comparison stands out in these payment records.'
        )
        action = 'the invoice and approval'
    check_first = f'Check: {action}.'
    if len(f'{headline} {support or ""} {check_first}'.split()) >= 60:
        support = None
    return PaymentExplanation(
        headline=headline,
        support=support,
        check_first=check_first,
        signals=rows,
        tags=['Unusually large payment']
        if candidates
        else ['Payment frequency worth checking']
        if frequency is not None and frequency >= SUMMARY_FREQUENCY_MIN
        else [],
        amount_display=amount_display,
    )
