import re
from dataclasses import dataclass


class SubmissionParseError(ValueError):
    pass


@dataclass(slots=True)
class ParsedSubmissionName:
    title: str
    year: int | None
    tmdb_id: int


TMDB_ID_RE = re.compile(r"\{\s*tmdbid\s*=\s*(\d+)\s*\}", re.IGNORECASE)
YEAR_RE = re.compile(r"\((\d{4})\)")


def parse_submission_folder_name(folder_name: str) -> ParsedSubmissionName:
    tmdb_match = TMDB_ID_RE.search(folder_name)
    if tmdb_match is None:
        raise SubmissionParseError("目录名缺少 {tmdbid=数字}")

    title_part = folder_name[: tmdb_match.start()].strip()
    year_match = YEAR_RE.search(title_part)
    year = int(year_match.group(1)) if year_match else None
    if year_match is not None:
        title_part = (title_part[: year_match.start()] + title_part[year_match.end() :]).strip()

    title = " ".join(title_part.split())
    if not title:
        raise SubmissionParseError("目录名缺少影视名称")

    return ParsedSubmissionName(title=title, year=year, tmdb_id=int(tmdb_match.group(1)))


def format_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(max(size, 0))
    unit = units[0]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            break
        value /= 1024
    if unit == "B":
        return f"{int(value)}B"
    return f"{value:.2f}{unit}"

