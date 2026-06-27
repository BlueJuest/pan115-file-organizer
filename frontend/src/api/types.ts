export interface SettingsRead {
  id: number
  pan115_cookie_masked: string
  tmdb_api_key_masked: string
  tmdb_language: string
  telegram_bot_token_masked: string
  telegram_channel_id: string
  default_share_user: string
  default_source_dir: string
  default_target_dir: string
  default_recycle_dir: string
  allow_delete_old_files: boolean
  recursive_scan: boolean
}

export interface SubmissionMediaDetails {
  tmdb_id: number
  media_type: string
  title: string
  original_title: string
  year: number | null
  overview: string
  poster_path: string
  backdrop_path: string
  vote_average: number | null
  genres: string[]
}

export interface SubmissionPreviewResponse {
  share_url: string
  receive_code: string | null
  folder_name: string
  parsed_title: string
  parsed_year: number | null
  media: SubmissionMediaDetails
  quality: string
  video_source: string
  subtitles: string
  custom_content: string
  share_user: string
  share_user_url: string
  douban_rating: string
  douban_url: string
  total_size: number
  size_text: string
  image_url: string
  image_base64: string
  mime_type: string
  caption: string
}

export interface SubmissionPublishResponse {
  ok: boolean
  message: string
  telegram_message_id: string
}

export interface RenameRuleRead {
  id: number
  name: string
  media_type: string
  pattern: string
  template: string
  priority: number
  enabled: boolean
  sample_input: string
  sample_output: string
  hit_count: number
}

export interface PreviewItemRead {
  id: number
  file_id: string
  original_path: string
  new_path: string
  file_size: number
  media_type: string
  tmdb_title: string
  confidence: number
  conflict_status: string
  upgrade_suggestion: string
  final_action: string
  status: string
  error_message: string
}

export interface ExecutionRead {
  id: number
  item_count: number
  success_count: number
  failed_count: number
  skipped_count: number
  status: string
}
