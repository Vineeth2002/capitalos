from app.models.entity import Entity
from app.models.listing import Listing
from app.models.security import Security


class IdentityError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _entity_type_value(entity):
    entity_type = entity.entity_type
    return getattr(entity_type, "value", entity_type)


def create_security(db, security_in):
    issuer = db.get(Entity, security_in.issuer_entity_id)
    if not issuer:
        raise IdentityError(404, "Issuer entity not found")
    if _entity_type_value(issuer) != "company":
        raise IdentityError(422, "Issuer entity must have entity_type 'company'")

    if security_in.identifier is not None:
        existing = (
            db.query(Security)
            .filter(
                Security.identifier_type == security_in.identifier_type,
                Security.identifier == security_in.identifier,
            )
            .first()
        )
        if existing:
            raise IdentityError(409, "A security with this identifier already exists")

    security = Security(
        issuer_entity_id=security_in.issuer_entity_id,
        identifier_type=security_in.identifier_type,
        identifier=security_in.identifier,
    )
    db.add(security)
    db.commit()
    db.refresh(security)
    return security


def get_security(db, security_id):
    return db.get(Security, security_id)


def list_securities(db):
    return db.query(Security).order_by(Security.id.asc()).all()


def create_listing(db, listing_in):
    security = db.get(Security, listing_in.security_id)
    if not security:
        raise IdentityError(404, "Security not found")

    exchange = listing_in.exchange.strip().upper()
    symbol = listing_in.symbol.strip()
    if not exchange or not symbol:
        raise IdentityError(422, "exchange and symbol must not be empty")

    existing = (
        db.query(Listing)
        .filter(
            Listing.security_id == listing_in.security_id,
            Listing.exchange == exchange,
            Listing.symbol == symbol,
        )
        .first()
    )
    if existing:
        raise IdentityError(409, "This listing already exists for the security")

    listing = Listing(security_id=listing_in.security_id, exchange=exchange, symbol=symbol)
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def get_listing(db, listing_id):
    return db.get(Listing, listing_id)


def list_listings(db):
    return db.query(Listing).order_by(Listing.id.asc()).all()