from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entity import Entity
from app.schemas.entity import EntityCreate, EntityUpdate, EntityResponse

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("", response_model=EntityResponse)
def create_entity(entity_in: EntityCreate, db: Session = Depends(get_db)):
    entity = Entity(**entity_in.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@router.get("", response_model=list[EntityResponse])
def list_entities(db: Session = Depends(get_db)):
    return db.query(Entity).all()


@router.get("/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.patch("/{entity_id}", response_model=EntityResponse)
def update_entity(entity_id: int, entity_in: EntityUpdate, db: Session = Depends(get_db)):
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    update_data = entity_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity