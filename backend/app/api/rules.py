from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.rules import RenameRule
from app.schemas.rules import (
    RenameRuleCreate,
    RenameRuleRead,
    RenameRuleTest,
    RenameRuleTestResult,
)
from app.services.rule_engine import RenameRuleInput, RuleEngine
from app.services.template_engine import TemplateEngine

router = APIRouter(prefix="/api/rules", tags=["rules"])


def to_read(rule: RenameRule) -> RenameRuleRead:
    return RenameRuleRead(
        id=rule.id,
        name=rule.name,
        media_type=rule.media_type,
        pattern=rule.pattern,
        template=rule.template,
        priority=rule.priority,
        enabled=bool(rule.enabled),
        sample_input=rule.sample_input,
        sample_output=rule.sample_output,
        hit_count=rule.hit_count,
    )


def apply_payload(rule: RenameRule, payload: RenameRuleCreate) -> None:
    rule.name = payload.name
    rule.media_type = payload.media_type
    rule.pattern = payload.pattern
    rule.template = payload.template
    rule.priority = payload.priority
    rule.enabled = int(payload.enabled)
    rule.sample_input = payload.sample_input
    rule.sample_output = payload.sample_output


@router.get("", response_model=list[RenameRuleRead])
def list_rules(db: Session = Depends(get_db)) -> list[RenameRuleRead]:
    rules = db.scalars(select(RenameRule).order_by(RenameRule.priority)).all()
    return [to_read(rule) for rule in rules]


@router.post("", response_model=RenameRuleRead)
def create_rule(payload: RenameRuleCreate, db: Session = Depends(get_db)) -> RenameRuleRead:
    rule = RenameRule()
    apply_payload(rule, payload)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return to_read(rule)


@router.put("/{rule_id}", response_model=RenameRuleRead)
def update_rule(
    rule_id: int,
    payload: RenameRuleCreate,
    db: Session = Depends(get_db),
) -> RenameRuleRead:
    rule = db.get(RenameRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="规则不存在")

    apply_payload(rule, payload)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return to_read(rule)


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    rule = db.get(RenameRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="规则不存在")

    db.delete(rule)
    db.commit()
    return {"ok": True}


@router.post("/test", response_model=RenameRuleTestResult)
def test_rule(payload: RenameRuleTest) -> RenameRuleTestResult:
    rule = RenameRuleInput(
        id=0,
        name="test",
        media_type=payload.media_type,
        pattern=payload.pattern,
        template=payload.template,
        priority=payload.priority,
        enabled=payload.enabled,
    )
    match_result = RuleEngine().match(
        payload.sample_input,
        [rule],
        media_type=payload.media_type,
    )
    if not match_result.matched:
        return RenameRuleTestResult(
            matched=False,
            fields=match_result.fields,
            error=match_result.error,
        )

    render_result = TemplateEngine().render(match_result.template, match_result.fields)
    if not render_result.ok:
        error = render_result.error
        if render_result.missing_fields:
            error = f"缺少字段: {', '.join(render_result.missing_fields)}"
        return RenameRuleTestResult(
            matched=True,
            fields=match_result.fields,
            error=error,
        )

    return RenameRuleTestResult(
        matched=True,
        fields=match_result.fields,
        output=render_result.path,
    )
