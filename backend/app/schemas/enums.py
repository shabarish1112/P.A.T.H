from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    member = 'member'
    analyst = 'analyst'
    reviewer = 'reviewer'
    admin = 'admin'


class ReviewStatus(StrEnum):
    pending_review = 'Pending Review'
    confirmed_finding = 'Confirmed Finding'
    false_alert = 'False Alert'
    escalated = 'Escalated'


class RiskLevel(StrEnum):
    critical = 'Critical'
    high = 'High'
    medium = 'Medium'
    low = 'Low'
    normal = 'Normal'


class ModelName(StrEnum):
    isolation_forest = 'if'
    extended_isolation_forest = 'eif'
    deep_isolation_forest = 'dif'


REVIEW_STATUSES = tuple(item.value for item in ReviewStatus)
RISK_LEVELS = tuple(item.value for item in RiskLevel)
MODEL_OPTIONS = tuple(item.value for item in ModelName)
