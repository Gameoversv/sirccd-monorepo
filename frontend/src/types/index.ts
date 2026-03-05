// Types for authentication and users
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  brigade_id?: number;
}

export enum UserRole {
  CIUDADANO = 'ciudadano',
  BRIGADA = 'brigada',
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
  assigned_brigade_id?: number;
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

// Types for brigades
export interface Brigade {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  members?: User[];
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
  brigade_id?: number;
  date_from?: string;
  date_to?: string;
  priority_min?: number;
  priority_max?: number;
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
  showBrigades: boolean;
  damageClasses: DamageClass[];
  statuses: IncidentStatus[];
  severities: SeverityLevel[];
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

// Valid status transitions (backend rules)
export const STATUS_TRANSITIONS: Record<string, string[]> = {
  open: ['assigned', 'closed'],
  assigned: ['in_progress', 'open'],
  in_progress: ['resolved', 'assigned'],
  resolved: ['verified', 'in_progress'],
  verified: ['closed', 'resolved'],
  closed: [],
};

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
  assigned_brigade_id: number | null;
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
