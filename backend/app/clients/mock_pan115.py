from app.clients.protocols import OperationResult, RemoteDir, RemoteFile


class MockPan115Client:
    def __init__(self) -> None:
        self._next_id = 1
        self._files: dict[str, RemoteFile] = {
            "0": RemoteFile(
                file_id="0",
                name="",
                path="/",
                parent_id="",
                is_dir=True,
            )
        }

    def test_connection(self) -> bool:
        return True

    def list_dir(self, dir_id: str) -> list[RemoteFile]:
        return [file for file in self._files.values() if file.parent_id == dir_id]

    def rename(self, file_id: str, new_name: str) -> OperationResult:
        file = self._files.get(file_id)
        if file is None:
            return OperationResult(False, "文件不存在")

        file.name = new_name
        file.path = self._join_path(self._parent_path(file.parent_id), new_name)
        self._refresh_children_paths(file_id)
        return OperationResult(True)

    def move(self, file_id: str, target_dir_id: str) -> OperationResult:
        file = self._files.get(file_id)
        target = self._files.get(target_dir_id)
        if file is None:
            return OperationResult(False, "文件不存在")
        if target is None or not target.is_dir:
            return OperationResult(False, "目标目录不存在")

        file.parent_id = target_dir_id
        file.path = self._join_path(target.path, file.name)
        self._refresh_children_paths(file_id)
        return OperationResult(True)

    def delete(self, file_id: str) -> OperationResult:
        if file_id not in self._files:
            return OperationResult(False, "文件不存在")

        ids_to_delete = self._collect_descendant_ids(file_id)
        for current_id in ids_to_delete:
            del self._files[current_id]
        return OperationResult(True)

    def mkdir(self, parent_id: str, name: str) -> RemoteDir:
        parent = self._files.get(parent_id)
        parent_path = parent.path if parent and parent.is_dir else "/"
        dir_id = str(self._next_id)
        self._next_id += 1
        path = self._join_path(parent_path, name)
        self._files[dir_id] = RemoteFile(
            file_id=dir_id,
            name=name,
            path=path,
            parent_id=parent_id,
            is_dir=True,
        )
        return RemoteDir(dir_id=dir_id, name=name, path=path)

    def get_path(self, file_id: str) -> str:
        file = self._files.get(file_id)
        if file is None:
            return ""
        return file.path

    def _parent_path(self, parent_id: str) -> str:
        parent = self._files.get(parent_id)
        if parent is None:
            return "/"
        return parent.path

    def _join_path(self, parent_path: str, name: str) -> str:
        if parent_path == "/":
            return f"/{name}"
        return f"{parent_path}/{name}"

    def _refresh_children_paths(self, file_id: str) -> None:
        parent = self._files[file_id]
        for child in self.list_dir(file_id):
            child.path = self._join_path(parent.path, child.name)
            if child.is_dir:
                self._refresh_children_paths(child.file_id)

    def _collect_descendant_ids(self, file_id: str) -> list[str]:
        ids = [file_id]
        for child in self.list_dir(file_id):
            ids.extend(self._collect_descendant_ids(child.file_id))
        return ids
