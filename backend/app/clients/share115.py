from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ShareInspection:
    folder_name: str
    total_size: int
    share_user: str = ""


class Share115Client:
    def __init__(self, raw_client: Any | None = None) -> None:
        if raw_client is not None:
            self.raw = raw_client
        else:
            from p115client import P115Client

            self.raw = P115Client

    def inspect_share(self, share_url: str, receive_code: str | None = None) -> ShareInspection:
        from p115client.util import share_extract_payload

        payload = dict(share_extract_payload(share_url))
        if receive_code:
            payload["receive_code"] = receive_code
        payload.setdefault("receive_code", "")

        root_response = self.raw.share_snap({**payload, "cid": "0", "offset": 0, "limit": 1000})
        root_items = self._items(root_response)
        folder_name = self._folder_name(root_response, root_items)
        share_user = self._share_user(root_response)
        total_size = self._sum_items(payload, root_items)
        return ShareInspection(folder_name=folder_name, total_size=total_size, share_user=share_user)

    def _sum_items(self, payload: dict[str, Any], items: list[dict[str, Any]]) -> int:
        total = 0
        for item in items:
            if self._is_dir(item):
                cid = self._id(item)
                if cid:
                    response = self.raw.share_snap({**payload, "cid": cid, "offset": 0, "limit": 1000})
                    total += self._sum_items(payload, self._items(response))
            else:
                total += self._size(item)
        return total

    def _folder_name(self, response: dict[str, Any], items: list[dict[str, Any]]) -> str:
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        for source in (data, response):
            for key in ("file_name", "folder_name", "share_title", "title", "name"):
                value = source.get(key)
                if value:
                    return str(value)
        if len(items) == 1 and self._is_dir(items[0]):
            return self._name(items[0])
        if items:
            return self._name(items[0])
        raise ValueError("115 分享目录为空或无法读取目录名")

    def _share_user(self, response: dict[str, Any]) -> str:
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        sources = [data, response]
        user_info = data.get("user_info") or data.get("user") or response.get("user_info") or response.get("user")
        if isinstance(user_info, dict):
            sources.insert(0, user_info)
        for source in sources:
            for key in ("user_name", "username", "nick_name", "nickname", "share_user", "uname"):
                value = source.get(key)
                if value:
                    return str(value)
        return ""

    def _items(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        data = response.get("data")
        if isinstance(data, dict):
            for key in ("list", "items", "files", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    return value
        for key in ("list", "items", "files", "data"):
            value = response.get(key)
            if isinstance(value, list):
                return value
        return []

    def _is_dir(self, item: dict[str, Any]) -> bool:
        value = item.get("is_dir")
        if value is not None:
            return str(value) in {"1", "True", "true"}
        if "fc" in item:
            return str(item.get("fc")) == "0"
        if "cid" in item and not item.get("fid"):
            return True
        return bool(item.get("is_folder"))

    def _id(self, item: dict[str, Any]) -> str:
        return str(item.get("cid") or item.get("file_id") or item.get("fid") or item.get("id") or "")

    def _name(self, item: dict[str, Any]) -> str:
        return str(item.get("n") or item.get("name") or item.get("file_name") or "")

    def _size(self, item: dict[str, Any]) -> int:
        value = item.get("s") or item.get("size") or item.get("file_size") or 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
