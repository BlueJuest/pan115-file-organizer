from dataclasses import dataclass, field
from string import Formatter

from app.core.security import clean_path_part


@dataclass(slots=True)
class TemplateRenderResult:
    ok: bool
    path: str = ""
    missing_fields: list[str] = field(default_factory=list)
    error: str = ""


class TemplateEngine:
    def render(self, template: str, fields: dict[str, object]) -> TemplateRenderResult:
        try:
            field_names = self._field_names(template)
        except (ValueError, TypeError) as exc:
            return TemplateRenderResult(ok=False, error=str(exc))

        missing_fields = [name for name in field_names if name not in fields]
        if missing_fields:
            return TemplateRenderResult(ok=False, missing_fields=missing_fields)

        try:
            leading_slash = template.startswith("/")
            parts = template.split("/")
            if leading_slash:
                parts = parts[1:]

            rendered_parts = [clean_path_part(part.format(**fields)) for part in parts]
            path = "/".join(rendered_parts)
            if leading_slash:
                path = f"/{path}"
        except (KeyError, IndexError) as exc:
            return TemplateRenderResult(ok=False, missing_fields=[str(exc)])
        except (AttributeError, ValueError, TypeError) as exc:
            return TemplateRenderResult(ok=False, error=str(exc))

        return TemplateRenderResult(ok=True, path=path)

    def _field_names(self, template: str) -> list[str]:
        names: list[str] = []
        formatter = Formatter()

        for _, field_name, format_spec, _ in formatter.parse(template):
            if field_name:
                name = self._base_field_name(field_name)
                if name not in names:
                    names.append(name)
            if format_spec:
                for _, nested_field_name, _, _ in formatter.parse(format_spec):
                    if nested_field_name:
                        name = self._base_field_name(nested_field_name)
                        if name not in names:
                            names.append(name)

        return names

    def _base_field_name(self, field_name: str) -> str:
        if "." in field_name or "[" in field_name or "]" in field_name:
            raise ValueError(f"不支持复杂字段访问: {field_name}")
        return field_name
