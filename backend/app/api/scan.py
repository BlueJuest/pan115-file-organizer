from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.mock_pan115 import MockPan115Client
from app.clients.protocols import RemoteFile
from app.core.database import get_db
from app.models import PreviewItem, RenameRule, ScanBatch
from app.schemas.scan import PreviewItemRead, PreviewItemUpdate, ScanCreate, ScanRead
from app.services.media_identifier import MediaIdentifier
from app.services.preview_builder import PreviewBuilder
from app.services.rule_engine import RenameRuleInput

router = APIRouter(prefix="/api", tags=["scans"])


def scan_to_read(scan: ScanBatch) -> ScanRead:
    return ScanRead(
        id=scan.id,
        source_dir=scan.source_dir,
        target_dir=scan.target_dir,
        media_type=scan.media_type,
        recursive=bool(scan.recursive),
        file_count=scan.file_count,
        recognized_count=scan.recognized_count,
        need_confirm_count=scan.need_confirm_count,
        status=scan.status,
        created_at=scan.created_at,
    )


def preview_item_to_read(item: PreviewItem) -> PreviewItemRead:
    return PreviewItemRead(
        id=item.id,
        scan_batch_id=item.scan_batch_id,
        file_id=item.file_id,
        original_path=item.original_path,
        new_path=item.new_path,
        file_size=item.file_size,
        media_type=item.media_type,
        title=item.title,
        year=item.year,
        season=item.season,
        episode=item.episode,
        tmdb_id=item.tmdb_id,
        tmdb_title=item.tmdb_title,
        confidence=item.confidence,
        matched_rule_id=item.matched_rule_id,
        quality_score=item.quality_score,
        conflict_status=item.conflict_status,
        upgrade_suggestion=item.upgrade_suggestion,
        final_action=item.final_action,
        status=item.status,
        error_message=item.error_message,
        created_at=item.created_at,
    )


def _rule_inputs(db: Session) -> list[RenameRuleInput]:
    rules = db.scalars(select(RenameRule).order_by(RenameRule.priority)).all()
    return [
        RenameRuleInput(
            id=rule.id,
            name=rule.name,
            media_type=rule.media_type,
            pattern=rule.pattern,
            template=rule.template,
            priority=rule.priority,
            enabled=bool(rule.enabled),
        )
        for rule in rules
    ]


def _scan_client() -> MockPan115Client:
    return MockPan115Client(
        [
            RemoteFile("root", "", "/", "", True),
            RemoteFile("src", "src", "/src", "root", True),
            RemoteFile("f1", "流浪地球 2019 2160p WEB-DL.mkv", "/src/流浪地球 2019 2160p WEB-DL.mkv", "src", False, 1024),
        ]
    )


@router.post("/scans", response_model=ScanRead)
def create_scan(payload: ScanCreate, db: Session = Depends(get_db)) -> ScanRead:
    result = PreviewBuilder(_scan_client(), MediaIdentifier()).build(
        payload.source_dir,
        payload.target_dir,
        payload.media_type,
        payload.recursive,
        _rule_inputs(db),
    )
    scan = ScanBatch(
        source_dir=payload.source_dir,
        target_dir=payload.target_dir,
        media_type=payload.media_type,
        recursive=int(payload.recursive),
        file_count=result.file_count,
        recognized_count=result.recognized_count,
        need_confirm_count=result.need_confirm_count,
        status="preview_ready",
    )
    db.add(scan)
    db.flush()

    for built_item in result.items:
        db.add(
            PreviewItem(
                scan_batch_id=scan.id,
                file_id=built_item.file_id,
                original_path=built_item.original_path,
                new_path=built_item.new_path,
                file_size=built_item.file_size,
                media_type=built_item.media_type,
                title=built_item.title,
                year=built_item.year,
                season=built_item.season,
                episode=built_item.episode,
                tmdb_id=built_item.tmdb_id,
                tmdb_title=built_item.tmdb_title,
                confidence=built_item.confidence,
                matched_rule_id=built_item.matched_rule_id,
                quality_score=built_item.quality_score,
                conflict_status=built_item.conflict_status,
                upgrade_suggestion=built_item.upgrade_suggestion,
                final_action=built_item.final_action,
                status=built_item.status,
                error_message=built_item.error_message,
            )
        )

    db.commit()
    db.refresh(scan)
    return scan_to_read(scan)


@router.get("/scans/{scan_id}", response_model=ScanRead)
def get_scan(scan_id: int, db: Session = Depends(get_db)) -> ScanRead:
    scan = db.get(ScanBatch, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="扫描不存在")
    return scan_to_read(scan)


@router.get("/scans/{scan_id}/items", response_model=list[PreviewItemRead])
def list_scan_items(scan_id: int, db: Session = Depends(get_db)) -> list[PreviewItemRead]:
    scan = db.get(ScanBatch, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="扫描不存在")
    items = db.scalars(select(PreviewItem).where(PreviewItem.scan_batch_id == scan_id)).all()
    return [preview_item_to_read(item) for item in items]


@router.put("/preview-items/{item_id}", response_model=PreviewItemRead)
def update_preview_item(
    item_id: int,
    payload: PreviewItemUpdate,
    db: Session = Depends(get_db),
) -> PreviewItemRead:
    item = db.get(PreviewItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="预览项不存在")
    if payload.new_path is not None:
        item.new_path = payload.new_path
    if payload.media_type is not None:
        item.media_type = payload.media_type
    if payload.final_action is not None:
        item.final_action = payload.final_action
    if payload.status is not None:
        item.status = payload.status
    db.add(item)
    db.commit()
    db.refresh(item)
    return preview_item_to_read(item)
