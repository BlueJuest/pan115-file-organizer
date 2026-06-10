import re
from dataclasses import dataclass, field
from pathlib import PurePath


@dataclass(slots=True)
class RenameRuleInput:
    id: int
    name: str
    media_type: str
    pattern: str
    template: str
    priority: int
    enabled: bool


@dataclass(slots=True)
class RuleMatchResult:
    matched: bool
    rule_id: int | None = None
    template: str = ""
    fields: dict[str, str] = field(default_factory=dict)
    error: str = ""


class RuleEngine:
    def match(
        self,
        filename: str,
        rules: list[RenameRuleInput],
        media_type: str,
    ) -> RuleMatchResult:
        for rule in sorted(rules, key=lambda item: item.priority):
            if not rule.enabled:
                continue
            if rule.media_type not in {"general", media_type}:
                continue

            try:
                pattern = re.compile(rule.pattern)
            except re.error as exc:
                return RuleMatchResult(matched=False, error=str(exc))

            matched = pattern.search(filename)
            if not matched:
                continue

            fields = matched.groupdict()
            fields["ext"] = PurePath(filename).suffix.lstrip(".")
            return RuleMatchResult(
                matched=True,
                rule_id=rule.id,
                template=rule.template,
                fields=fields,
            )

        return RuleMatchResult(matched=False, error="没有命中规则")
