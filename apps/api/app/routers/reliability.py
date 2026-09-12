import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.common.scoring import evaluate_reliability
from packages.database.models import ClaimModel, SourceModel
from packages.database.session import get_db

router = APIRouter(prefix="/reliability", tags=["reliability"])


def slugify_name(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    return re.sub(r"[-\s]+", "-", s)


class CategoryRecord(BaseModel):
    category: str
    correct: int
    total: int


class ClaimResolution(BaseModel):
    claim: str
    outcome: str


class ReliabilityScoreResponse(BaseModel):
    subject_name: str
    slug: str
    subject_type: str
    sample_size: int
    correct_count: int
    wilson_lower_bound: float | None = None
    is_insufficient_record: bool = True
    total_claims: int = 0
    score_by_category: list[CategoryRecord] = []
    recent_resolutions: list[ClaimResolution] = []
    affiliation: str | None = None
    beat: str | None = None


@router.get("", response_model=list[ReliabilityScoreResponse])
def list_reliability_scores(
    db: Session = Depends(get_db),
):
    """Lists reliability records and scores for all tracked outlets and reporters."""
    sources = db.query(SourceModel).order_by(SourceModel.name.asc()).all()

    claims_count_by_source: dict[str, int] = {
        str(row[0]): int(row[1])
        for row in db.execute(select(ClaimModel.source_id, func.count(ClaimModel.id)).group_by(ClaimModel.source_id)).all()
    }

    results: list[ReliabilityScoreResponse] = []
    for s in sources:
        slug = slugify_name(s.name)
        metrics = evaluate_reliability(
            subject_name=s.name,
            subject_type=s.source_type,
            correct_count=s.correct_count,
            sample_size=s.sample_size,
            min_sample_threshold=10,
        )
        total_claims = claims_count_by_source.get(s.id, 0)
        results.append(
            ReliabilityScoreResponse(
                subject_name=s.name,
                slug=slug,
                subject_type=s.source_type,
                sample_size=s.sample_size,
                correct_count=s.correct_count,
                wilson_lower_bound=metrics.wilson_lower_bound,
                is_insufficient_record=metrics.is_insufficient_record,
                total_claims=total_claims,
                score_by_category=[CategoryRecord(category="Transfers", correct=s.correct_count, total=s.sample_size)]
                if s.sample_size > 0
                else [],
                recent_resolutions=[],
                affiliation=s.affiliation,
                beat=s.beat,
            )
        )

    # Sort: outlets with highest claims first
    results.sort(key=lambda r: (r.total_claims, r.sample_size), reverse=True)
    return results


@router.get("/{subject_slug}", response_model=ReliabilityScoreResponse)
def get_reliability_score(
    subject_slug: str,
    db: Session = Depends(get_db),
):
    """Retrieve public reliability score and record for an outlet or reporter."""
    normalized = subject_slug.replace("-", " ").strip().lower()
    sources = db.query(SourceModel).all()
    target_source = None
    for s in sources:
        if s.name.lower() == normalized or s.id == subject_slug or slugify_name(s.name) == subject_slug or s.id == f"src-{subject_slug}":
            target_source = s
            break

    if not target_source:
        disp_name = subject_slug.replace("-", " ").title()
        return ReliabilityScoreResponse(
            subject_name=disp_name,
            slug=subject_slug,
            subject_type="outlet",
            sample_size=0,
            correct_count=0,
            wilson_lower_bound=None,
            is_insufficient_record=True,
            total_claims=0,
            score_by_category=[],
            recent_resolutions=[],
        )

    metrics = evaluate_reliability(
        subject_name=target_source.name,
        subject_type=target_source.source_type,
        correct_count=target_source.correct_count,
        sample_size=target_source.sample_size,
        min_sample_threshold=10,
    )

    total_claims = (
        db.query(func.count(ClaimModel.id))
        .filter(
            (ClaimModel.source_id == target_source.id)
            | (ClaimModel.reporter == target_source.name)
            | (ClaimModel.reporter_id == target_source.id)
        )
        .scalar()
        or 0
    )

    return ReliabilityScoreResponse(
        subject_name=target_source.name,
        slug=slugify_name(target_source.name),
        subject_type=target_source.source_type,
        sample_size=target_source.sample_size,
        correct_count=target_source.correct_count,
        wilson_lower_bound=metrics.wilson_lower_bound,
        is_insufficient_record=metrics.is_insufficient_record,
        total_claims=total_claims,
        score_by_category=[CategoryRecord(category="Transfers", correct=target_source.correct_count, total=target_source.sample_size)]
        if target_source.sample_size > 0
        else [],
        recent_resolutions=[],
        affiliation=target_source.affiliation,
        beat=target_source.beat,
    )
