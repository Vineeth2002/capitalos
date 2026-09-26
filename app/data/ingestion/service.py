from app.data.connectors.registry import get_connector_class
from app.services import financial_fact_service
from app.schemas.financial_fact import FinancialFactCreate


class IngestionValidationError(Exception):
    pass


def ingest_from_provider(db, provider_name, raw_records):
    # Looks up a connector ONLY by provider_name through the registry.
    # This function never imports or references a specific connector
    # class - adding Provider N means calling register_connector()
    # somewhere once; this function needs zero changes.
    connector_class = get_connector_class(provider_name)
    connector = connector_class(raw_records=raw_records)
    canonical_facts = connector.normalize(connector.fetch())
    return ingest_canonical_facts(db, canonical_facts)


def ingest_canonical_facts(db, canonical_facts):
    """
    Persists a list of CanonicalFinancialFact objects through the existing
    FinancialFact creation path. This function knows nothing about where
    the canonical facts came from - no provider awareness at all.
    """
    from app.models.entity import Entity
    from app.models.research_source import ResearchSource

    created = []
    for fact in canonical_facts:
        if fact.entity_id is None:
            raise IngestionValidationError(
                "Canonical fact is missing required entity_id"
            )
        if not fact.fact_type:
            raise IngestionValidationError(
                "Canonical fact is missing required fact_type"
            )
        if fact.value_numeric is None:
            raise IngestionValidationError(
                "Canonical fact is missing required value_numeric"
            )

        entity = db.get(Entity, fact.entity_id)
        if not entity:
            raise IngestionValidationError(
                "Entity not found for entity_id=" + str(fact.entity_id)
            )

        if fact.source_id is not None:
            source = db.get(ResearchSource, fact.source_id)
            if not source:
                raise IngestionValidationError(
                    "Source not found for source_id=" + str(fact.source_id)
                )

        fact_in = FinancialFactCreate(
            entity_id=fact.entity_id,
            fact_type=fact.fact_type,
            value_numeric=fact.value_numeric,
            unit=fact.unit,
            currency=fact.currency,
            period_start=fact.period_start,
            period_end=fact.period_end,
            as_of_date=fact.as_of_date,
            source_id=fact.source_id,
        )
        created_fact = financial_fact_service.create_fact(db, fact_in)
        created.append(created_fact)

    return created