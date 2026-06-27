import base64
from dataclasses import dataclass
from io import BytesIO
from textwrap import wrap
from typing import Callable

import httpx

from app.schemas.submissions import SubmissionMediaDetails


@dataclass(slots=True)
class SubmissionCard:
    share_url: str
    receive_code: str | None
    media: SubmissionMediaDetails
    quality: str
    video_source: str
    subtitles: str
    custom_content: str
    share_user: str
    size_text: str


@dataclass(slots=True)
class RenderedCard:
    image_base64: str
    mime_type: str = "image/png"


@dataclass(frozen=True, slots=True)
class CardRow:
    icon: str
    label: str
    value: Callable[[SubmissionCard], str]


CARD_ROWS = [
    CardRow("film", "类型", lambda card: "电影" if card.media.media_type == "movie" else "剧集"),
    CardRow("star", "TMDB评分", lambda card: _score(card.media.vote_average)),
    CardRow("tv", "画质", lambda card: card.quality),
    CardRow("tape", "视频", lambda card: card.video_source),
    CardRow("chat", "字幕", lambda card: card.subtitles),
    CardRow("disk", "大小", lambda card: card.size_text),
    CardRow("user", "分享", lambda card: card.share_user),
]


class SubmissionCardRenderer:
    def render(self, card: SubmissionCard) -> RenderedCard:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as exc:
            raise RuntimeError("Pillow is required to render submission cards") from exc

        width = 760
        hero_height = 420
        padding = 24
        line_height = 31
        canvas_height = 1040
        image = Image.new("RGB", (width, canvas_height), "#f7f3ee")
        draw = ImageDraw.Draw(image)
        font_regular = self._font(ImageFont, 24)
        font_bold = self._font(ImageFont, 28, bold=True)
        font_small = self._font(ImageFont, 21)

        hero = self._load_hero(Image, card.media.backdrop_path or card.media.poster_path, width, hero_height)
        image.paste(hero, (0, 0))

        y = hero_height + 22
        title = card.media.title or card.media.original_title
        year = f" ({card.media.year})" if card.media.year else ""
        self._draw_icon(draw, "camera", padding, y + 4)
        draw.text((padding + 34, y), f"{title}{year}", fill="#1f2937", font=font_bold)
        y += 54

        for row in CARD_ROWS:
            value = row.value(card)
            if value:
                self._draw_icon(draw, row.icon, padding, y + 4)
                draw.text((padding + 34, y), f"{row.label}：{value}", fill="#263241", font=font_regular)
                y += line_height

        if card.custom_content:
            y = self._quote_box(draw, padding, y + 8, width - padding * 2, card.custom_content, font_small)

        y += 24
        self._draw_icon(draw, "link", padding, y + 4)
        draw.text((padding + 34, y), "链接：115网盘", fill="#9f534e", font=font_regular)
        y += 56

        if card.media.overview:
            y = self._quote_box(draw, padding, y, width - padding * 2, f"简介：\n{card.media.overview}", font_small)

        tags = " ".join(f"#{genre}" for genre in card.media.genres[:4])
        if tags:
            self._draw_icon(draw, "tag", padding, y + 30)
            draw.text((padding + 34, y + 28), f"标签：{tags}", fill="#b15f62", font=font_small)

        output = BytesIO()
        image.save(output, format="PNG")
        return RenderedCard(image_base64=base64.b64encode(output.getvalue()).decode("ascii"))

    def _draw_icon(self, draw, icon: str, x: int, y: int) -> None:
        fill = "#64748b"
        accent = "#8b5cf6"
        if icon == "star":
            draw.polygon([(x + 12, y), (x + 15, y + 8), (x + 24, y + 8), (x + 17, y + 14), (x + 20, y + 23), (x + 12, y + 17), (x + 4, y + 23), (x + 7, y + 14), (x, y + 8), (x + 9, y + 8)], fill="#f5c542")
        elif icon == "camera":
            draw.rounded_rectangle((x, y + 4, x + 24, y + 21), radius=4, outline=fill, width=2)
            draw.rectangle((x + 4, y, x + 13, y + 5), fill=fill)
            draw.ellipse((x + 8, y + 8, x + 18, y + 18), outline=accent, width=2)
        elif icon == "film":
            draw.rounded_rectangle((x + 1, y + 2, x + 23, y + 22), radius=3, outline=fill, width=2)
            for dot_y in (y + 5, y + 12, y + 19):
                draw.rectangle((x + 4, dot_y, x + 7, dot_y + 2), fill=accent)
                draw.rectangle((x + 17, dot_y, x + 20, dot_y + 2), fill=accent)
        elif icon == "tv":
            draw.rounded_rectangle((x, y + 4, x + 24, y + 19), radius=3, outline=fill, width=2)
            draw.line((x + 8, y + 23, x + 16, y + 23), fill=fill, width=2)
        elif icon == "tape":
            draw.rounded_rectangle((x, y + 5, x + 24, y + 20), radius=4, outline=fill, width=2)
            draw.ellipse((x + 5, y + 9, x + 11, y + 15), outline=accent, width=2)
            draw.ellipse((x + 14, y + 9, x + 20, y + 15), outline=accent, width=2)
        elif icon == "chat":
            draw.rounded_rectangle((x, y + 3, x + 24, y + 18), radius=5, outline=fill, width=2)
            draw.polygon([(x + 7, y + 18), (x + 7, y + 24), (x + 13, y + 18)], fill=fill)
        elif icon == "disk":
            draw.rounded_rectangle((x + 2, y + 1, x + 22, y + 23), radius=4, outline=fill, width=2)
            draw.rectangle((x + 6, y + 4, x + 18, y + 11), fill=accent)
            draw.line((x + 6, y + 18, x + 18, y + 18), fill=fill, width=2)
        elif icon == "user":
            draw.ellipse((x + 7, y + 2, x + 17, y + 12), outline=fill, width=2)
            draw.arc((x + 2, y + 11, x + 22, y + 30), 200, 340, fill=fill, width=2)
        elif icon == "link":
            draw.arc((x + 1, y + 5, x + 16, y + 20), 40, 310, fill=fill, width=2)
            draw.arc((x + 8, y + 5, x + 23, y + 20), 220, 130, fill=accent, width=2)
        elif icon == "tag":
            draw.polygon([(x + 2, y + 4), (x + 15, y + 4), (x + 24, y + 13), (x + 13, y + 24), (x + 2, y + 13)], outline=fill, fill=None)
            draw.ellipse((x + 7, y + 9, x + 11, y + 13), fill=accent)

    def _quote_box(self, draw, x: int, y: int, width: int, text: str, font) -> int:
        lines: list[str] = []
        for paragraph in text.splitlines():
            lines.extend(wrap(paragraph, width=32) or [""])
        height = max(54, len(lines) * 28 + 24)
        draw.rounded_rectangle((x, y, x + width, y + height), radius=8, fill="#eadcf0")
        draw.rectangle((x, y, x + 6, y + height), fill="#8b5cf6")
        text_y = y + 12
        for line in lines:
            draw.text((x + 18, text_y), line, fill="#243041", font=font)
            text_y += 28
        return y + height + 12

    def _load_hero(self, image_module, path: str, width: int, height: int):
        if not path:
            return self._fallback_hero(image_module, width, height)
        url = path if path.startswith("http") else f"https://image.tmdb.org/t/p/w1280{path}"
        try:
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            hero = image_module.open(BytesIO(response.content)).convert("RGB")
        except Exception:
            return self._fallback_hero(image_module, width, height)
        hero_ratio = hero.width / hero.height
        target_ratio = width / height
        if hero_ratio > target_ratio:
            new_height = height
            new_width = int(height * hero_ratio)
        else:
            new_width = width
            new_height = int(width / hero_ratio)
        hero = hero.resize((new_width, new_height))
        left = max(0, (new_width - width) // 2)
        top = max(0, (new_height - height) // 2)
        return hero.crop((left, top, left + width, top + height))

    def _fallback_hero(self, image_module, width: int, height: int):
        image = image_module.new("RGB", (width, height), "#172033")
        draw = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(image)
        for index in range(height):
            color = int(22 + index / height * 45)
            draw.line((0, index, width, index), fill=(color, 35, 58))
        return image

    def _font(self, image_font_module, size: int, bold: bool = False):
        candidates = [
            "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "arial.ttf",
        ]
        for candidate in candidates:
            try:
                return image_font_module.truetype(candidate, size=size)
            except OSError:
                continue
        return image_font_module.load_default()


def _score(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.1f}/10"

