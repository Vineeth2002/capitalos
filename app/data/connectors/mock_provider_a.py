from app.data.connectors.base import FinancialDataConnector
from app.data.contracts.financial_fact import CanonicalFinancialFact


class MockProviderAConnector(FinancialDataConnector):
    """
    Deterministic mock connector for architectural verification only.
    Never makes a network call. Simulates a provider that uses field
    names: company_id, revenue, period, currency_code, source_ref.
    """

    provider_name = "mock_provider_a"

    def __init__(self, raw_records=None):
        self._raw_records = raw_records if raw_records is not None else []

    def fetch(self):
        return self._raw_records

    def normalize(self, raw_records) -> list[CanonicalFinancialFact]:
        canonical = []
        for record in raw_records:
            required = ["company_id", "revenue", "period_start", "period_end"]
            for field in required:
                if field not in record:
                    raise ValueError(
                        "MockProviderA record missing required field: " + field
                    )

            canonical.append(
                CanonicalFinancialFact(
                    entity_id=record["company_id"],
                    fact_type="revenue",
                    value_numeric=record["revenue"],
                    currency=record.get("currency_code"),
                    period_start=record["period_start"],
                    period_end=record["period_end"],
                    source_id=record.get("source_ref"),
                )
            )
        return canonical