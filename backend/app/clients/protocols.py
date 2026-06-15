from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class RemoteFile:
    file_id: str
    name: str
    path: str
    parent_id: str
    is_dir: bool
    size: int = 0


@dataclass(slots=True)
class OperationResult:
    ok: bool
    message: str = ""


@dataclass(slots=True)
class RemoteDir:
    dir_id: str
    name: str
    path: str


@dataclass(slots=True)
class TmdbCandidate:
    tmdb_id: int
    media_type: str
    title_cn: str
    title_original: str
    year: int | None
    confidence: float
    overview: str = ""
    poster_path: str = ""


class Pan115ClientProtocol(Protocol):
    def test_connection(self) -> bool: ...

    def list_dir(self, dir_id: str) -> list[RemoteFile]: ...

    def list_dir_recursive(self, dir_id: str) -> list[RemoteFile]: ...

    def ensure_dir_path(self, path: str, root_id: str = "0") -> str: ...

    def rename(self, file_id: str, new_name: str) -> OperationResult: ...

    def move(self, file_id: str, target_dir_id: str) -> OperationResult: ...

    def delete(self, file_id: str) -> OperationResult: ...

    def mkdir(self, parent_id: str, name: str) -> RemoteDir: ...

    def get_path(self, file_id: str) -> str: ...


class TmdbClientProtocol(Protocol):
    def search_movie(self, title: str, year: int | None) -> list[TmdbCandidate]: ...

    def search_tv(self, title: str, year: int | None) -> list[TmdbCandidate]: ...

    def get_details(self, tmdb_id: int, media_type: str) -> TmdbCandidate | None: ...
