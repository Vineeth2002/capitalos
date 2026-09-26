from app.data.connectors.base import FinancialDataConnector
from app.data.contracts.financial_fact import CanonicalFinancialFact


class MockProviderBConnector(FinancialDataConnector):
    """
    Deterministic mock connector for architectural verification only.
    Never makes a network call. Simulates a DIFFERENT provider that uses
    entirely different field names: issuer_code, sales, fiscal_start,
    fiscal_end, currency, provenance_id - proving normalization is
    provider-shape-independent, not just directory-independent.
    """

    provider_name = "mock_provider_b"

    def __init__(self, raw_records=None):
        self._raw_records = raw_records if raw_records is not None else []

    def fetch(self):
        return self._raw_records

    def normalize(self, raw_records) -> list[CanonicalFinancialFact]:
        canonical = []
        for record in raw_records:
            required = ["issuer_code", "sales", "fiscal_start", "fiscal_end"]
            for field in required:
                if field not in record:
                    raise ValueError(
                        "MockProviderB record missing required field: " + field
                    )

            canonical.append(
                CanonicalFinancialFact(
                    entity_id=record["issuer_code"],
                    fact_type="revenue",
                    value_numeric=record["sales"],
                    currency=record.get("currency"),
                    period_start=record["fiscal_start"],
                    period_end=record["fiscal_end"],
                    source_id=record.get("provenance_id"),
                )
            )
        return canonical