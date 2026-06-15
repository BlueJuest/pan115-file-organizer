from app.clients.mock_pan115 import MockPan115Client
from app.clients.pan115 import Pan115Client


class FakeRawClient:
    def __init__(self):
        self.calls = []

    def fs_files(self, payload):
        self.calls.append(("fs_files", payload))
        return {"data": [{"fid": "f1", "n": "测试.mkv", "cid": "src", "pc": "/下载/测试.mkv", "sha": "", "s": 100, "is_dir": 0}]}

    def fs_rename(self, payload):
        self.calls.append(("fs_rename", payload))
        return {"state": True}

    def fs_move(self, payload):
        self.calls.append(("fs_move", payload))
        return {"state": True}

    def fs_delete(self, payload):
        self.calls.append(("fs_delete", payload))
        return {"state": True}

    def fs_mkdir(self, payload, pid=0):
        self.calls.append(("fs_mkdir", payload, pid))
        return {"cid": "newdir", "file_name": payload["name"]}


class FakeTreeRawClient(FakeRawClient):
    def __init__(self):
        super().__init__()
        self.children = {
            "0": [],
            "101": [],
            "102": [],
        }
        self.next_id = 101

    def fs_files(self, payload):
        self.calls.append(("fs_files", payload))
        cid = str(payload["cid"])
        return {"data": self.children.get(cid, [])}

    def fs_mkdir(self, payload, pid=0):
        parent_id = str(pid)
        self.calls.append(("fs_mkdir", payload, parent_id))
        dir_id = str(self.next_id)
        self.next_id += 1
        item = {"cid": dir_id, "n": payload["name"], "pid": parent_id, "fc": "0"}
        self.children.setdefault(parent_id, []).append(item)
        self.children.setdefault(dir_id, [])
        return {"cid": dir_id, "file_name": payload["name"]}


def test_pan115_ensure_dir_path_creates_missing_dirs():
    raw = FakeTreeRawClient()
    client = Pan115Client(cookie="UID=abc", raw_client=raw)

    dir_id = client.ensure_dir_path("/电影/流浪地球", root_id="0")

    assert dir_id == "102"
    assert ("fs_mkdir", {"name": "电影"}, "0") in raw.calls
    assert ("fs_mkdir", {"name": "流浪地球"}, "101") in raw.calls


def test_mock_pan115_ensure_dir_path_uses_default_root_id():
    client = MockPan115Client()

    dir_id = client.ensure_dir_path("/电影")

    assert client.get_path(dir_id) == "/电影"


def test_pan115_adapter_maps_files_and_operations():
    raw = FakeRawClient()
    client = Pan115Client(cookie="UID=abc", raw_client=raw)

    files = client.list_dir("src")
    renamed = client.rename("f1", "新名.mkv")
    moved = client.move("f1", "target")
    deleted = client.delete("f1")
    directory = client.mkdir("root", "电影")

    assert client.cookie == "UID=abc"
    assert files[0].file_id == "f1"
    assert files[0].name == "测试.mkv"
    assert renamed.ok is True
    assert moved.ok is True
    assert deleted.ok is True
    assert directory.dir_id == "newdir"
    assert directory.path == "root/电影"
    assert raw.calls[1] == ("fs_rename", {"files_new_name[f1]": "新名.mkv"})
