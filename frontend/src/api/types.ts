export interface SettingsRead {
  id: number
  pan115_cookie_masked: string
  tmdb_api_key_masked: string
  tmdb_language: string
  default_source_dir: string
  default_target_dir: string
  default_recycle_dir: string
  allow_delete_old_files: boolean
  recursive_scan: boolean
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
