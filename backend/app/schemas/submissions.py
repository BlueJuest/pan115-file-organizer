from pydantic import BaseModel, Field


class SubmissionPreviewRequest(BaseModel):
    share_url: str
    receive_code: str | None = None
    media_type: str = "auto"
    quality: str = ""
    video_source: str = ""
    subtitles: str = ""
    custom_content: str = ""


class SubmissionMediaDetails(BaseModel):
    tmdb_id: int
    media_type: str
    title: str
    original_title: str = ""
    year: int | None = None
    overview: str = ""
    poster_path: str = ""
    backdrop_path: str = ""
    vote_average: float | None = None
    genres: list[str] = Field(default_factory=list)


class SubmissionPreviewResponse(BaseModel):
    share_url: str
    receive_code: str | None
    folder_name: str
    parsed_title: str
    parsed_year: int | None
    media: SubmissionMediaDetails
    quality: str
    video_source: str
    subtitles: str
    custom_content: str
    share_user: str
    share_user_url: str
    douban_rating: str
    douban_url: str
    total_size: int
    size_text: str
    image_url: str
    image_base64: str = ""
    mime_type: str = "image/jpeg"
    caption: str


class SubmissionPublishRequest(BaseModel):
    image_url: str
    caption: str = ""


class SubmissionPublishResponse(BaseModel):
    ok: bool
    message: str
    telegram_message_id: str = ""
