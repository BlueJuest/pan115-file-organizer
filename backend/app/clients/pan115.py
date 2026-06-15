from typing import Any

from app.clients.protocols import OperationResult, RemoteDir, RemoteFile


class Pan115Client:
    def __init__(self, cookie: str, raw_client: Any | None = None) -> None:
        self.cookie = cookie
        if raw_client is not None:
            self.raw = raw_client
        else:
            from p115client import P115Client

            self.raw = P115Client(cookie)

    def test_connection(self) -> bool:
        try:
            self.list_dir("0")
        except Exception:
            return False
        return True

    def list_dir(self, dir_id: str) -> list[RemoteFile]:
        response = self.raw.fs_files({"cid": dir_id, "limit": 1000, "offset": 0})
        items = response.get("data") or response.get("files") or []
        return [self._file(item, dir_id) for item in items]

    def list_dir_recursive(self, dir_id: str) -> list[RemoteFile]:
        files: list[RemoteFile] = []
        seen: set[str] = set()

        def collect(current_id: str) -> None:
            if current_id in seen:
                return
            seen.add(current_id)
            for file in self.list_dir(current_id):
                files.append(file)
                if file.is_dir:
                    collect(file.file_id)

        collect(dir_id)
        return files

    def ensure_dir_path(self, path: str, root_id: str = "0") -> str:
        current_id = root_id
        for name in [part for part in path.strip("/").split("/") if part]:
            children = self.list_dir(current_id)
            existing = next((file for file in children if file.is_dir and file.name == name), None)
            if existing is None:
                existing_dir = self.mkdir(current_id, name)
                current_id = existing_dir.dir_id
            else:
                current_id = existing.file_id
        return current_id

    def rename(self, file_id: str, new_name: str) -> OperationResult:
        response = self.raw.fs_rename({f"files_new_name[{file_id}]": new_name})
        return self._result(response, "重命名成功")

    def move(self, file_id: str, target_dir_id: str) -> OperationResult:
        response = self.raw.fs_move({"ids": file_id, "to_cid": target_dir_id})
        return self._result(response, "移动成功")

    def delete(self, file_id: str) -> OperationResult:
        response = self.raw.fs_delete({"file_ids": file_id})
        return self._result(response, "删除成功")

    def mkdir(self, parent_id: str, name: str) -> RemoteDir:
        response = self.raw.fs_mkdir({"name": name}, pid=parent_id)
        dir_name = str(response.get("file_name") or response.get("name") or name)
        return RemoteDir(
            dir_id=str(response.get("cid") or response.get("file_id") or response.get("id") or ""),
            name=dir_name,
            path=str(response.get("path") or f"{parent_id}/{dir_name}"),
        )

    def get_path(self, file_id: str) -> str:
        return ""

    def _file(self, item: dict[str, Any], fallback_parent_id: str) -> RemoteFile:
        is_dir = item.get("is_dir")
        if is_dir is None and "fc" in item:
            is_dir = item.get("fc") == "0"
        return RemoteFile(
            file_id=str(item.get("fid") or item.get("cid") or item.get("id") or ""),
            name=str(item.get("n") or item.get("name") or ""),
            path=str(item.get("pc") or item.get("path") or ""),
            parent_id=str(item.get("pid") or item.get("cid") or item.get("parent_id") or fallback_parent_id),
            is_dir=bool(is_dir),
            size=int(item.get("s") or item.get("size") or 0),
        )

    def _result(self, response: dict[str, Any], success_message: str) -> OperationResult:
        ok = bool(response.get("state", True) or response.get("ok", False))
        if ok:
            return OperationResult(True, success_message)
        message = response.get("message") or response.get("error") or "115 操作失败"
        return OperationResult(False, str(message))
