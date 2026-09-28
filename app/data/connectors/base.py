from abc import ABC, abstractmethod
from typing import Optional

from app.data.contracts.financial_fact import CanonicalFinancialFact


class FinancialDataConnector(ABC):
    """
    Contract every data provider adapter must implement.

    A connector only translates: provider-native records in, canonical facts
    out. Nothing here constrains transport (HTTP, files, etc.).

    provider_name is recorded on the IngestionRun for lineage.
    connector_version is optional and, when set, is recorded on the run so
    "which normalization version produced this" stays answerable.
    """

    provider_name: str
    connector_version: Optional[str] = None

    @abstractmethod
    def fetch(self):
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_records) -> list[CanonicalFinancialFact]:
        # Must raise rather than invent a value or guess a date.
        raise NotImplementedError