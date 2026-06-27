from dataclasses import dataclass, field
from string import Formatter

from jinja2 import TemplateError, meta
from jinja2.sandbox import SandboxedEnvironment

from app.core.security import clean_path_part


@dataclass(slots=True)
class TemplateRenderResult:
    ok: bool
    path: str = ""
    missing_fields: list[str] = field(default_factory=list)
    error: str = ""


class TemplateEngine:
    def __init__(self) -> None:
        self.jinja_env = SandboxedEnvironment(autoescape=False)

    def render(self, template: str, fields: dict[str, object]) -> TemplateRenderResult:
        if self._is_jinja_template(template):
            return self._render_jinja(template, fields)

        return self._render_format_template(template, fields)

    def _render_format_template(self, template: str, fields: dict[str, object]) -> TemplateRenderResult:
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

    def _render_jinja(self, template: str, fields: dict[str, object]) -> TemplateRenderResult:
        try:
            parsed = self.jinja_env.parse(template)
        except TemplateError as exc:
            return TemplateRenderResult(ok=False, error=str(exc))

        missing_fields = sorted(name for name in meta.find_undeclared_variables(parsed) if name not in fields)
        if missing_fields:
            return TemplateRenderResult(ok=False, missing_fields=missing_fields)

        try:
            rendered = self.jinja_env.from_string(template).render(fields)
            path = self._clean_rendered_path(rendered, leading_slash=rendered.startswith("/"))
        except TemplateError as exc:
            return TemplateRenderResult(ok=False, error=str(exc))
        except (AttributeError, ValueError, TypeError) as exc:
            return TemplateRenderResult(ok=False, error=str(exc))

        return TemplateRenderResult(ok=True, path=path)

    def _clean_rendered_path(self, rendered: str, leading_slash: bool) -> str:
        parts = rendered.split("/")
        if leading_slash:
            parts = parts[1:]
        cleaned = "/".join(clean_path_part(part) for part in parts)
        if leading_slash:
            return f"/{cleaned}"
        return cleaned

    def _is_jinja_template(self, template: str) -> bool:
        return "{{" in template or "{%" in template or "{#" in template

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
