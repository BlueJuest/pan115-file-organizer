from pydantic import BaseModel, Field


class RenameRuleCreate(BaseModel):
    name: str
    media_type: str = "general"
    pattern: str
    template: str
    priority: int = 100
    enabled: bool = True
    sample_input: str = ""
    sample_output: str = ""


class RenameRuleRead(BaseModel):
    id: int
    name: str
    media_type: str
    pattern: str
    template: str
    priority: int
    enabled: bool
    sample_input: str
    sample_output: str
    hit_count: int


class RenameRuleTest(BaseModel):
    media_type: str = "general"
    pattern: str
    template: str
    priority: int = 100
    enabled: bool = True
    sample_input: str


class RenameRuleTestResult(BaseModel):
    matched: bool
    fields: dict[str, str] = Field(default_factory=dict)
    output: str = ""
    error: str = ""


class QualityProfileCreate(BaseModel):
    name: str
    resolution_weight: float = 40
    source_weight: float = 25
    video_codec_weight: float = 15
    audio_codec_weight: float = 10
    size_weight: float = 5
    subtitle_weight: float = 5
    min_upgrade_delta: float = 15
    default_old_file_action: str = "move_to_recycle"
    resolution_order: str = "2160p,1080p,720p,480p"
    source_order: str = "BluRay,WEB-DL,WEBRip,HDTV"
    video_codec_order: str = "H.265,HEVC,H.264,AVC"
    audio_codec_order: str = "TrueHD,DTS-HD,DDP,DD,AAC"


class QualityProfileRead(BaseModel):
    id: int
    name: str
    resolution_weight: float
    source_weight: float
    video_codec_weight: float
    audio_codec_weight: float
    size_weight: float
    subtitle_weight: float
    min_upgrade_delta: float
    default_old_file_action: str
    resolution_order: str
    source_order: str
    video_codec_order: str
    audio_codec_order: str
