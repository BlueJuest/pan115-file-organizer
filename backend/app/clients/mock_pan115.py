from app.clients.protocols import OperationResult, RemoteDir, RemoteFile


class MockPan115Client:
    def __init__(self, files: list[RemoteFile] | None = None) -> None:
        self._files: dict[str, RemoteFile] = {}
        if files is not None:
            self._files = {file.file_id: file for file in files}
        if "0" not in self._files:
            self._files["0"] = RemoteFile(
                file_id="0",
                name="",
                path="/",
                parent_id="",
                is_dir=True,
            )
        self._next_id = self._calculate_next_id()

    def test_connection(self) -> bool:
        return True

    def list_dir(self, dir_id: str) -> list[RemoteFile]:
        return [file for file in self._files.values() if file.parent_id == dir_id]

    def rename(self, file_id: str, new_name: str) -> OperationResult:
        file = self._files.get(file_id)
        if file is None:
            return OperationResult(False, "文件不存在")
        if file_id == "0":
            return OperationResult(False, "不能重命名根目录")

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
        if file_id == "0":
            return OperationResult(False, "不能移动根目录")
        if file_id == target_dir_id:
            return OperationResult(False, "不能移动到自身")
        if file.is_dir and self._is_descendant(target_dir_id, file_id):
            return OperationResult(False, "不能移动到自身子目录")

        file.parent_id = target_dir_id
        file.path = self._join_path(target.path, file.name)
        self._refresh_children_paths(file_id)
        return OperationResult(True)

    def delete(self, file_id: str) -> OperationResult:
        if file_id not in self._files:
            return OperationResult(False, "文件不存在")
        if file_id == "0":
            return OperationResult(False, "不能删除根目录")

        ids_to_delete = self._collect_descendant_ids(file_id)
        for current_id in ids_to_delete:
            del self._files[current_id]
        return OperationResult(True)

    def mkdir(self, parent_id: str, name: str) -> RemoteDir:
        parent = self._files.get(parent_id)
        if parent is None or not parent.is_dir:
            raise ValueError("父目录不存在")

        dir_id = str(self._next_id)
        self._next_id += 1
        path = self._join_path(parent.path, name)
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

    def _calculate_next_id(self) -> int:
        numeric_ids = [int(file_id) for file_id in self._files if file_id.isdigit()]
        if not numeric_ids:
            return 1
        return max(numeric_ids) + 1

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

    def _is_descendant(self, candidate_id: str, ancestor_id: str) -> bool:
        seen: set[str] = set()
        current_id = candidate_id
        while current_id and current_id not in seen:
            if current_id == ancestor_id:
                return True
            seen.add(current_id)
            current = self._files.get(current_id)
            if current is None:
                return False
            current_id = current.parent_id
        return False
