export interface Finding {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  dimension: string;
  rule_id: string;
  description: string;
  location?: string;
}

export interface Report {
  report_id: string;
  compliance_score: number;
  findings: Finding[];
  summary: string;
}

export interface UploadResponse {
  path: string;
  type: 'prd' | 'prototype';
  filename: string;
}

export interface ReviewRequest {
  document_path: string;
  review_types: ('prd' | 'prototype')[];
}