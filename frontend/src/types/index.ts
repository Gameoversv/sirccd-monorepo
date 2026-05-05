// Types for authentication and users
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export enum UserRole {
  CIUDADANO = 'ciudadano',
  SUPERVISOR = 'supervisor',
  ADMIN = 'admin',
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: number;
  username: string;
  email: string;
  role: UserRole;
  full_name: string | null;
}

// Types for reports and incidents
export interface Report {
  id: number;
  user_id: number;
  description: string;
  image_url: string;
  image_hash?: string;
  location: GeoPoint;
  address?: string;
  detected_class?: DamageClass;
  confidence?: number;
  severity?: SeverityLevel;
  status: ReportStatus;
  is_duplicate: boolean;
  duplicate_of?: number;
  created_at: string;
  updated_at: string;
}

export interface Incident {
  id: number;
  report_id: number;
  damage_class: DamageClass;
  severity: SeverityLevel;
  location: GeoPoint;
  address: string;
  priority_score: number;
  status: IncidentStatus;
  assigned_at?: string;
  started_at?: string;
  completed_at?: string;
  verified_at?: string;
  before_image_url: string;
  after_image_url?: string;
  repair_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface GeoPoint {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
}

export enum DamageClass {
  BACHE = 'bache',
  GRIETA = 'grieta',
}

export enum SeverityLevel {
  BAJA = 'baja',
  MEDIA = 'media',
  ALTA = 'alta',
}

export enum ReportStatus {
  PENDIENTE = 'pendiente',
  EN_REVISION = 'en_revision',
  APROBADO = 'aprobado',
  RECHAZADO = 'rechazado',
  DUPLICADO = 'duplicado',
}

export enum IncidentStatus {
  REPORTADO = 'reportado',
  ASIGNADO = 'asignado',
  EN_PROGRESO = 'en_progreso',
  COMPLETADO = 'completado',
  VERIFICADO = 'verificado',
  CERRADO = 'cerrado',
}

// Types for POIs
export interface POI {
  id: number;
  name: string;
  category: POICategory;
  location: GeoPoint;
  address?: string;
  risk_weight: number;
  created_at: string;
}

export enum POICategory {
  ESCUELA = 'escuela',
  UNIVERSIDAD = 'universidad',
  HOSPITAL = 'hospital',
  CLINICA = 'clinica',
  BOMBEROS = 'bomberos',
  POLICIA = 'policia',
  PUENTE = 'puente',
}

// Types for metrics and KPIs
export interface SystemMetrics {
  total_reports: number;
  total_incidents: number;
  pending_incidents: number;
  in_progress_incidents: number;
  completed_incidents: number;
  duplicate_rate: number;
  avg_resolution_time: number;
  f1_score?: number;
  precision?: number;
  recall?: number;
}

// Pagination and filters
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Incident list response (matches backend schema)
export interface IncidentListResponse {
  total: number;
  incidents: any[]; // Using any temporarily, could be typed as IncidentBrief[]
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ReportFilters {
  status?: ReportStatus;
  damage_class?: DamageClass;
  severity?: SeverityLevel;
  date_from?: string;
  date_to?: string;
  user_id?: number;
}

export interface IncidentFilters {
  status?: IncidentStatus;
  damage_class?: DamageClass;
  severity?: SeverityLevel;
  date_from?: string;
  date_to?: string;
  priority_min?: number;
  priority_max?: number;
  zone_id?: number;
}

// API Response types
export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  message?: string;
}

// Map and visualization types
export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface MapFilter {
  showReports: boolean;
  showIncidents: boolean;
  showPOIs: boolean;
  damageClasses: DamageClass[];
  statuses: IncidentStatus[];
  severities: SeverityLevel[];
}

// POI Layers (P-02)
export type POILayerCategory =
  | 'school'
  | 'hospital'
  | 'fire_station'
  | 'community_center';

export interface POILayerItem {
  id: number;
  name: string;
  category: POILayerCategory;
  source_category: string;
  latitude: number;
  longitude: number;
  address?: string;
  city?: string;
  priority_weight: number;
  recommended_buffer_m: number;
}

export interface POILayerResponse {
  total: number;
  pois: POILayerItem[];
  categories: POILayerCategory[];
  min_buffer_m: number;
  default_buffer_m: number;
  max_buffer_m: number;
}

export interface POILayerFilters {
  showPOIs: boolean;
  showRiskBuffers: boolean;
  bufferRadiusMeters: number;
  categories: Record<POILayerCategory, boolean>;
}

// Export formats
export interface ExportOptions {
  format: 'csv' | 'geojson';
  filters?: IncidentFilters;
  include_kpis?: boolean;
}

// Backend incident statuses (English values from API)
export enum BackendIncidentStatus {
  OPEN = 'open',
  ASSIGNED = 'assigned',
  IN_PROGRESS = 'in_progress',
  RESOLVED = 'resolved',
  VERIFIED = 'verified',
  CLOSED = 'closed',
}

// Backend priority levels
export enum BackendPriorityLevel {
  BAJA = 'baja',
  MEDIA = 'media',
  ALTA = 'alta',
  CRITICA = 'critica',
}

// Valid status transitions (backend rules: open, in_progress, resolved, verified, closed)
export const STATUS_TRANSITIONS: Record<string, string[]> = {
  open: ['in_progress', 'closed'],
  in_progress: ['resolved', 'open'],
  resolved: ['verified', 'in_progress'],
  verified: ['closed', 'resolved'],
  closed: [],
};

// ── User management (W-08) ────────────────────────────────────────────────────

export interface UserDetail {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
}

export interface UserListResponse {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  users: UserDetail[];
}

export interface CreateUserData {
  email: string;
  username: string;
  full_name?: string;
  phone?: string;
  role: UserRole;
  password: string;
}

export interface UpdateUserData {
  email?: string;
  username?: string;
  full_name?: string;
  phone?: string;
  role?: UserRole;
  is_active?: boolean;
  password?: string;
}

// Priority settings (admin)
export interface PrioritySettings {
  id: number;
  weight_severity: number;
  weight_age: number;
  weight_damage_type: number;
  weight_location: number;
  weight_duplicates: number;
  weights_total: number;
  poi_radius_meters: number;
  duplicate_radius_meters: number;
  duplicate_time_window_days: number;
  clustering_eps_meters: number;
  clustering_min_samples: number;
  updated_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface UpdatePrioritySettingsData {
  weight_severity?: number;
  weight_age?: number;
  weight_damage_type?: number;
  weight_location?: number;
  weight_duplicates?: number;
  poi_radius_meters?: number;
  duplicate_radius_meters?: number;
  duplicate_time_window_days?: number;
  clustering_eps_meters?: number;
  clustering_min_samples?: number;
}

// Audit log (P-07)
export interface AuditLogEntry {
  id: number;
  incident_id: number;
  user_id: number | null;
  event_type: 'status_change' | 'priority_recalculated' | 'manual_update' | 'image_uploaded' | string;
  field_name: string | null;
  old_value: string | null;
  new_value: string | null;
  notes: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  total: number;
  entries: AuditLogEntry[];
}

// Detailed incident from GET /incidents/{id}
export interface IncidentDetail {
  id: number;
  report_id: number;
  reported_by: number;
  latitude: number | null;
  longitude: number | null;
  address: string | null;
  city: string | null;
  province: string | null;
  damage_type: string;
  severity: string;
  priority: string;
  priority_score: number | null;
  status: string;
  assigned_at: string | null;
  estimated_repair_hours: number | null;
  started_at: string | null;
  completed_at: string | null;
  verified_at: string | null;
  is_verified: boolean;
  verified_by: number | null;
  verification_notes: string | null;
  before_image_url: string | null;
  after_image_url: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}
