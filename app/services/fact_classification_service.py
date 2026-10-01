from app.models.fact_classification import FactClassification


class ClassificationError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def create_classification(db, classification_in):
    applies_to = classification_in.applies_to.value
    existing = (
        db.query(FactClassification)
        .filter(
            FactClassification.applies_to == applies_to,
            FactClassification.type_name == classification_in.type_name,
        )
        .first()
    )
    if existing:
        raise ClassificationError(
            409, "A classification for this type_name and applies_to already exists"
        )

    classification = FactClassification(
        applies_to=applies_to,
        type_name=classification_in.type_name,
        category=classification_in.category,
        description=classification_in.description,
    )
    db.add(classification)
    db.commit()
    db.refresh(classification)
    return classification


def list_classifications(db, applies_to=None):
    query = db.query(FactClassification)
    if applies_to is not None:
        query = query.filter(FactClassification.applies_to == applies_to)
    return query.order_by(FactClassification.id.asc()).all()


def lookup_classification(db, applies_to, type_name):
    return (
        db.query(FactClassification)
        .filter(
            FactClassification.applies_to == applies_to,
            FactClassification.type_name == type_name,
        )
        .first()
    )