from app.models.financial_fact import FinancialFact


def create_fact(db, fact_in):
    fact = FinancialFact(
        entity_id=fact_in.entity_id,
        fact_type=fact_in.fact_type,
        value_numeric=fact_in.value_numeric,
        unit=fact_in.unit,
        currency=fact_in.currency,
        period_start=fact_in.period_start,
        period_end=fact_in.period_end,
        as_of_date=fact_in.as_of_date,
        source_id=fact_in.source_id,
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)
    return fact


def get_fact(db, fact_id):
    return db.get(FinancialFact, fact_id)


def list_facts(db, entity_id=None, fact_type=None):
    query = db.query(FinancialFact)
    if entity_id is not None:
        query = query.filter(FinancialFact.entity_id == entity_id)
    if fact_type is not None:
        query = query.filter(FinancialFact.fact_type == fact_type)
    return query.order_by(FinancialFact.created_at.asc()).all()