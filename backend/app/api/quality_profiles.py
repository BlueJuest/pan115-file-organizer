from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.rules import QualityProfile
from app.schemas.rules import QualityProfileCreate, QualityProfileRead

router = APIRouter(prefix="/api/quality-profiles", tags=["quality-profiles"])


def to_read(profile: QualityProfile) -> QualityProfileRead:
    return QualityProfileRead(
        id=profile.id,
        name=profile.name,
        resolution_weight=profile.resolution_weight,
        source_weight=profile.source_weight,
        video_codec_weight=profile.video_codec_weight,
        audio_codec_weight=profile.audio_codec_weight,
        size_weight=profile.size_weight,
        subtitle_weight=profile.subtitle_weight,
        min_upgrade_delta=profile.min_upgrade_delta,
        default_old_file_action=profile.default_old_file_action,
        resolution_order=profile.resolution_order,
        source_order=profile.source_order,
        video_codec_order=profile.video_codec_order,
        audio_codec_order=profile.audio_codec_order,
    )


def apply_payload(profile: QualityProfile, payload: QualityProfileCreate) -> None:
    profile.name = payload.name
    profile.resolution_weight = payload.resolution_weight
    profile.source_weight = payload.source_weight
    profile.video_codec_weight = payload.video_codec_weight
    profile.audio_codec_weight = payload.audio_codec_weight
    profile.size_weight = payload.size_weight
    profile.subtitle_weight = payload.subtitle_weight
    profile.min_upgrade_delta = payload.min_upgrade_delta
    profile.default_old_file_action = payload.default_old_file_action
    profile.resolution_order = payload.resolution_order
    profile.source_order = payload.source_order
    profile.video_codec_order = payload.video_codec_order
    profile.audio_codec_order = payload.audio_codec_order


@router.get("", response_model=list[QualityProfileRead])
def list_profiles(db: Session = Depends(get_db)) -> list[QualityProfileRead]:
    profiles = db.scalars(select(QualityProfile)).all()
    return [to_read(profile) for profile in profiles]


@router.post("", response_model=QualityProfileRead)
def create_profile(
    payload: QualityProfileCreate,
    db: Session = Depends(get_db),
) -> QualityProfileRead:
    profile = QualityProfile()
    apply_payload(profile, payload)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return to_read(profile)


@router.put("/{profile_id}", response_model=QualityProfileRead)
def update_profile(
    profile_id: int,
    payload: QualityProfileCreate,
    db: Session = Depends(get_db),
) -> QualityProfileRead:
    profile = db.get(QualityProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="洗版策略不存在")

    apply_payload(profile, payload)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return to_read(profile)


@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    profile = db.get(QualityProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="洗版策略不存在")

    db.delete(profile)
    db.commit()
    return {"ok": True}
