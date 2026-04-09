export type ComplianceCitation = {
  source_title: string;
  country_code: string;
  page_num: string;
  heading_path: string;
  block_id: string;
  source_url: string;
};

export type ComplianceIssue = {
  excerpt: string;
  risk_level: string;
  issue_type: string;
  reason: string;
  suggested_fix: string;
  citations: ComplianceCitation[];
};

export type ComplianceReport = {
  overall_status: string;
  overall_risk: string;
  headline: string;
  overall_commentary: string;
  closing_note: string;
  issues: ComplianceIssue[];
};

export type TrendSource = {
  title: string;
  url: string;
  score: number | string;
  content: string;
};

export type TrendBenchmark = {
  title: string;
  url: string;
  platform: string;
  platform_key: string;
  view_count: number;
  view_count_label: string;
  summary: string;
  score: number;
  image_url: string;
  favicon: string;
};

export type TrendModuleMeta = {
  error: string;
  cached_at: string;
  from_cache: boolean;
  stale: boolean;
};

export type IndustryArticle = {
  title: string;
  url: string;
  summary: string;
  source: string;
  score: number;
};

export type IndustryInsight = {
  key: string;
  label: string;
  query: string;
  summary: string;
  articles: IndustryArticle[];
};

export type GenerateScriptRequest = {
  user_id: number;
  topic: string;
  target_languages: string[];
  video_duration: string;
  target_platform: string;
  target_country: string;
  distribution_mode: string;
  product_category: string;
  brand_id: string;
  creativity: number;
  persist_result: boolean;
};

export type TalentProfile = {
  id: number;
  user_id: number | null;
  name: string;
  platform: string;
  email: string;
  recent_video_link: string;
  notes: string;
  collaboration_progress: string;
  updated_at: string;
};

export type TalentMutationRequest = {
  name: string;
  platform: string;
  email: string;
  recent_video_link: string;
  notes: string;
  collaboration_progress: string;
};

export type TalentsResponse = {
  items: TalentProfile[];
  total: number;
};

export type TalentMutationResponse = {
  item: TalentProfile;
};

export type TalentDeleteResponse = {
  deleted: boolean;
  id: number;
};

export type ReviewScriptRequest = {
  script: string;
  topic?: string;
  user_id?: number;
  style_prompt?: string;
  target_languages: string[];
  target_platform: string;
  target_country: string;
  distribution_mode: string;
  product_category: string;
  brand_id: string;
};

export type GenerateScriptResponse = {
  initial_state: Record<string, unknown>;
  final_state: {
    final_script?: string;
    approved_script?: string;
    compliance_report?: ComplianceReport;
    trend_query?: string;
    trend_data?: string;
    trend_sources?: TrendSource[];
    script_model_provider?: string;
    script_model_name?: string;
    script_model_fallback_used?: boolean;
  } & Record<string, unknown>;
  saved_record_id: number | null;
};

export type ReviewScriptResponse = {
  initial_state: Record<string, unknown>;
  final_state: {
    final_script?: string;
    approved_script?: string;
    compliance_report?: ComplianceReport;
    rule_issues?: ComplianceIssue[];
    retrieved_evidence?: Array<Record<string, unknown>>;
  } & Record<string, unknown>;
};

export type TrendsResponse = {
  filters: Record<string, unknown>;
  trend_hunter: {
    trend_query: string;
    trend_data: string;
    trend_sources: TrendSource[];
  };
  benchmarks: TrendBenchmark[];
  benchmarks_error: string;
  videos: {
    items: TrendBenchmark[];
  } & TrendModuleMeta;
  industry: {
    topic_brief: {
      trend_query: string;
      trend_data: string;
      trend_sources: TrendSource[];
    };
    categories: IndustryInsight[];
  } & TrendModuleMeta;
};

export type LibraryHealthResponse = {
  collection_name: string;
  chunks: number;
  documents: number;
  embedding_backend: string;
  built_at: string;
  status: string;
  knowledge_base_root: string;
  raw_root: string;
  processed_root: string;
};

export type LibraryDocument = {
  source_id: string;
  title: string;
  category: string;
  platform: string;
  market: string;
  region: string;
  language: string;
  source_url: string;
  notes: string;
  priority: string;
  status: string;
  updated_at: string;
  raw_path: string;
  markdown_path: string;
  metadata_path: string;
  raw_suffix: string;
  file_origin: string;
};

export type LibraryDocumentsResponse = {
  items: LibraryDocument[];
  total: number;
  built_at: string;
};

export type LibraryUploadResponse = {
  item: LibraryDocument;
};

export type LibraryRebuildResponse = {
  normalized: {
    raw_files: number;
    processed_documents: number;
    manifest_path: string;
  };
  runtime: LibraryHealthResponse;
};
