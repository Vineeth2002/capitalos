from abc import ABC, abstractmethod

from app.data.contracts.financial_fact import CanonicalFinancialFact


class FinancialDataConnector(ABC):
    """
    Contract every future data provider adapter must implement.

    A connector's job is entirely translation: take whatever a provider
    returns, in whatever shape the provider uses, and produce
    CanonicalFinancialFact objects. This class intentionally says nothing
    about HTTP, files, APIs, or any transport - a connector may fetch data
    however it needs to; only its output shape is constrained.

    provider_name identifies which provider a connector represents, purely
    for logging/debugging - it is not used by the ingestion service to
    branch on provider-specific behavior.
    """

    provider_name: str

    @abstractmethod
    def fetch(self):
        # Returns provider-specific raw records, in whatever shape the
        # provider naturally uses. This method deliberately has no fixed
        # signature beyond returning something normalize() can consume -
        # different providers will fetch differently (API call, file read,
        # etc.), and that difference must stay contained here.
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_records) -> list[CanonicalFinancialFact]:
        # Converts provider-specific raw records into a list of
        # CanonicalFinancialFact objects. If a record cannot be mapped
        # safely (e.g. a required canonical field has no clear source in
        # the raw record), this method must raise rather than invent a
        # value or guess a date.
        raise NotImplementedError