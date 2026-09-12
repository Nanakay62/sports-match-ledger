from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from packages.database.registry import SourceRegistryService
from packages.database.session import get_db

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/registry")
def list_source_registry(
    status: str | None = Query(None, description="Filter by status (proposed, technical_review, rights_review, approved, rejected)"),
    db: Session = Depends(get_db),
):
    """Lists all sources in the registry and their current review status."""
    sources = SourceRegistryService.list_sources(session=db, status=status)
    return [
        {
            "id": s.id,
            "source_name": s.source_name,
            "feed_url": s.feed_url,
            "feed_format": s.feed_format,
            "language": s.language,
            "coverage_category": s.coverage_category,
            "authority_rank": s.authority_rank,
            "status": s.status,
            "technical_check_passed": s.technical_check_passed,
            "technical_notes": s.technical_notes,
            "rights_review_passed": s.rights_review_passed,
            "rights_notes": s.rights_notes,
            "polling_interval_minutes": s.polling_interval_minutes,
            "approved_at": s.approved_at.isoformat() if s.approved_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sources
    ]


@router.get("/approved")
def list_approved_sources(
    db: Session = Depends(get_db),
):
    """Lists all active approved sources ready for pipeline polling."""
    sources = SourceRegistryService.list_sources(session=db, status="approved")
    return [
        {
            "id": s.id,
            "source_name": s.source_name,
            "feed_url": s.feed_url,
            "language": s.language,
            "coverage_category": s.coverage_category,
            "authority_rank": s.authority_rank,
            "polling_interval_minutes": s.polling_interval_minutes,
            "approved_at": s.approved_at.isoformat() if s.approved_at else None,
        }
        for s in sources
    ]
