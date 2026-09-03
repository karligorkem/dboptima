export type OptimizationStatus =
  | "RECOMMENDED"
  | "REVIEW"
  | "REJECTED";

export type MLPrediction = {
  model_version: string;
  predicted_improvement_percent: number;
  predicted_status: OptimizationStatus;
  benchmark_priority: string;
  recommended_threshold: number;
  review_threshold: number;
  feature_count: number;
  model_path?: string;
  feature_schema: string;
};

export type BenchmarkStats = {
  runs_ms: number[];
  median_ms: number;
  mean_ms: number;
  min_ms: number;
  max_ms: number;
  p95_ms: number;
};

export type BenchmarkResult = {
  before_ms: number;
  after_ms: number;
  improvement_ms: number;
  improvement_percent: number;
  is_improvement: boolean;
  index_kept: boolean;

  benchmark_config: {
    warmup_runs: number;
    measurement_runs: number;
    decision_metric: string;
  };

  before: BenchmarkStats;
  after: BenchmarkStats;
};

export type RecommendationDecision = {
  status: OptimizationStatus;
  confidence: number;
  reason: string;
  benchmark_stability: number;
  history_confidence: number;
  sample_confidence: number;

  confidence_components: {
    improvement_confidence: number;
    benchmark_stability: number;
    history_confidence: number;
    sample_confidence: number;
  };

  thresholds: {
    recommended_percent: number;
    review_percent: number;
  };
};

export type IndexRecommendation = {
  type: string;
  schema: string;
  table: string;
  columns: string[];
  index_name: string;
  sql_command: string;
  reason: string;

  source?: {
    node_type?: string;
    filter?: string;
    plan_rows?: number;
    actual_rows?: number;
    actual_total_time?: number;
    rows_removed_by_filter?: number;
  };
};

export type OptimizationCandidate = {
  ml_rank: number;
  actual_rank: number;

  recommendation: IndexRecommendation;

  ml_prediction: MLPrediction;

  benchmark: BenchmarkResult;

  decision: RecommendationDecision;

  prediction_error_percent: number;
};

export type SequentialScanIssue = {
  node_type: string;
  relation_name: string;
  schema: string;
  alias?: string;
  filter?: string;
  plan_rows?: number;
  actual_rows?: number;
  actual_loops?: number;
  startup_cost?: number;
  total_cost?: number;
  actual_startup_time?: number;
  actual_total_time?: number;
  rows_removed_by_filter?: number;
};

export type EvaluationContext = {
  query_id: number;
  latency_sample_count: number;

  query_stats: {
    total_calls: number;
    avg_latency_ms: number;
    min_latency_ms: number;
    max_latency_ms: number;
    p95_latency_ms: number;
  };

  recommendation_history: {
    total_runs: number;
    recommended_runs: number;
    success_rate: number;
    avg_improvement_percent: number;
    best_improvement_percent: number;
    worst_improvement_percent: number;
    avg_confidence: number;
    latest_improvement_percent: number;
    avg_improvement?: number;
  };

  query: string;
};

export type OptimizeQueryResponse = {
  database_id: number;

  query: string;

  ml_model: {
    version: string;
    feature_schema: string;
    ranking_enabled: boolean;
  };

  baseline: {
    execution_time_ms: number;
    planning_time_ms: number;
  };

  issues: SequentialScanIssue[];

  candidate_count: number;

  evaluation_context: EvaluationContext;

  candidates: OptimizationCandidate[];

  persistence?: Record<string, unknown>;
};