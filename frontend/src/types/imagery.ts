export interface Region { x: number; y: number; width: number; height: number; area_pixels?: number; label?: string; score?: number; source_type?: string }
export interface SatelliteStatus { demo_available: boolean; uploaded_before: boolean; uploaded_after: boolean; classical_cv_available: boolean; ml_model_configured: boolean }
export interface SatelliteResult { detector: string; source_type: string; changed_pixels: number; percent_changed: number; regions: Region[]; mask_data_url: string; width: number; height: number }
export interface SonarFrame { name: string; frame_number: number; width: number; height: number; image_url: string; metadata: { scenario: string; sample_index: number }; annotations: Region[] }
export interface SonarReplay { source_type: string; detector: string; frames: SonarFrame[] }
export interface SonarResult { detector: string; source_type: string; output_source: string; anomaly_count: number; anomaly_score: number; regions: Region[]; width: number; height: number }
