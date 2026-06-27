import httpx


class TelegramClient:
    def __init__(self, bot_token: str, channel_id: str) -> None:
        self.bot_token = bot_token
        self.channel_id = channel_id

    def send_photo(self, image: str, caption: str) -> str:
        response = httpx.post(
            f"https://api.telegram.org/bot{self.bot_token}/sendPhoto",
            data={
                "chat_id": self.channel_id,
                "photo": image,
                "caption": caption,
                "parse_mode": "HTML",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(str(payload.get("description") or "Telegram sendPhoto failed"))
        result = payload.get("result") or {}
        return str(result.get("message_id") or "")

