from __future__ import annotations

from app.repositories.anomalies import AnomalyRepository
from app.repositories.datasets import DatasetRepository
from app.repositories.models import ModelRepository
from app.repositories.settings import SettingsRepository
from app.repositories.transactions import TransactionRepository
from app.schemas.analytics import AnalysisInsightsResponse, CriticalFinding
from app.services.payment_explanation import explain_payment


class InsightService:
    def __init__(
        self,
        datasets: DatasetRepository,
        settings: SettingsRepository,
        models: ModelRepository,
        anomalies: AnomalyRepository,
    ) -> None:
        self.datasets = datasets
        self.settings = settings
        self.models = models
        self.anomalies = anomalies

    def summary(self) -> AnalysisInsightsResponse:
        dataset_id = self.settings.get('active_dataset_id')
        dataset = self.datasets.get(dataset_id) if dataset_id else None
        if not dataset:
            return AnalysisInsightsResponse(
                status='no_dataset',
                narrative='P.A.T.H. screens public fund disbursals for unusual payment patterns. '
                'No active dataset is available yet. '
                'An administrator must upload a CSV before analysis can begin.',
            )
        run_id = self.settings.active_run_id()
        run = self.models.get_run(run_id) if run_id else None
        count = int(dataset['row_count'])
        name = str(dataset['filename'])
        if not run_id or not run or run.get('dataset_id') != dataset_id:
            return AnalysisInsightsResponse(
                status='not_analyzed',
                dataset_id=dataset_id,
                dataset_name=name,
                transaction_count=count,
                narrative=f'{name} contains {count:,} public fund disbursal records. '
                'This upload has not been screened by a completed model run yet. '
                'Open ML Control and run a model to identify transactions for review.',
            )
        flagged = self.anomalies.count_for_run(run_id)
        critical = self.anomalies.count_for_run(run_id, 'Critical')
        findings = []
        transactions = TransactionRepository(self.anomalies.db)
        for doc in self.anomalies.list_for_run(run_id, 5, 'Critical'):
            explanation = explain_payment(doc, transactions.explanation_context(dataset_id, doc))
            findings.append(
                CriticalFinding(
                    transaction_id=str(doc['transaction_id']),
                    amount_paise=int(doc['amount_paise']),
                    agency=str(doc['agency']),
                    vendor=str(doc['vendor']),
                    score=float(doc['score']),
                    signals=[explanation.headline, *([explanation.support] if explanation.support else [])],
                    check=explanation.check_first,
                    amount_display=explanation.amount_display,
                    explanation=explanation,
                    priority=str(doc['risk']),
                )
            )
        return AnalysisInsightsResponse(
            status='ready',
            dataset_id=dataset_id,
            dataset_name=name,
            run_id=run_id,
            transaction_count=count,
            flagged_count=flagged,
            critical_count=critical,
            narrative=f'P.A.T.H. analyzed {count:,} public fund disbursal records from {name}. '
            f'The configured alert budget returned {flagged:,} transactions for human review; '
            f'{critical:,} of these have Critical priority. '
            'Open a transaction below to check its supporting records.',
            critical_records=findings,
        )
