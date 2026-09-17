from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from packages.common.entities import SEED_ENTITIES, CanonicalEntity

from ..security.api_keys import APIClient, get_api_client

router = APIRouter(prefix="/entities", tags=["entities"])


class EntityAliasResponse(BaseModel):
    surface_form: str
    confidence: float
    provenance: str
    language: str | None = None


class EntityResponse(BaseModel):
    id: str
    name: str
    type: str
    sport: str
    aliases: list[str]
    alias_records: list[EntityAliasResponse]
    localized_names: dict[str, str]

    @classmethod
    def from_canonical(cls, entity: CanonicalEntity) -> "EntityResponse":
        return cls(
            id=entity.id,
            name=entity.name,
            type=entity.type.value if hasattr(entity.type, "value") else str(entity.type),
            sport=entity.sport,
            aliases=entity.aliases,
            alias_records=[
                EntityAliasResponse(
                    surface_form=rec.surface_form,
                    confidence=rec.confidence,
                    provenance=rec.provenance,
                    language=rec.language,
                )
                for rec in entity.alias_records
            ],
            localized_names=entity.localized_names,
        )


@router.get("/search", response_model=list[EntityResponse])
def search_entities(
    q: str = Query(..., min_length=1, description="Entity name or alias to search"),
    type: str | None = Query(default=None, description="Optional entity type filter (club, player, manager, competition)"),
    limit: int = Query(default=20, ge=1, le=100),
    client: APIClient = Depends(get_api_client),
) -> list[EntityResponse]:
    """Search canonical entity graph and multilingual alias dictionary."""
    normalized_q = q.strip().lower()
    type_filter = type.strip().lower() if type else None

    matches: list[CanonicalEntity] = []
    for entity in SEED_ENTITIES:
        entity_type_str = entity.type.value if hasattr(entity.type, "value") else str(entity.type).lower()
        if type_filter and entity_type_str != type_filter:
            continue

        # Check name
        if normalized_q in entity.name.lower():
            matches.append(entity)
            continue

        # Check aliases
        if any(normalized_q in alias.lower() for alias in entity.aliases):
            matches.append(entity)
            continue

        # Check alias records
        if any(normalized_q in rec.surface_form.lower() for rec in entity.alias_records):
            matches.append(entity)
            continue

        # Check localized names
        if any(normalized_q in loc.lower() for loc in entity.localized_names.values()):
            matches.append(entity)
            continue

    return [EntityResponse.from_canonical(e) for e in matches[:limit]]


@router.get("/{entity_id}", response_model=EntityResponse)
def get_entity_by_id(
    entity_id: str,
    client: APIClient = Depends(get_api_client),
) -> EntityResponse:
    """Retrieve canonical entity record by entity ID."""
    for entity in SEED_ENTITIES:
        if entity.id == entity_id:
            return EntityResponse.from_canonical(entity)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Entity not found: {entity_id}",
    )
