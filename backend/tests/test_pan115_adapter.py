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
