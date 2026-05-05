"""
Servicio de Priorización de Incidentes (B-08)

Calcula y recalcula el score de prioridad de incidentes basado en múltiples factores:
- Severidad del daño
- Tipo de daño
- Tiempo transcurrido
- Ubicación (POIs cercanos)
- Afluencia vehicular estimada
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from geoalchemy2.functions import ST_DWithin, ST_Distance
from geoalchemy2.elements import WKTElement

from models.incident import Incident, IncidentStatus, PriorityLevel
from models.incident_audit_log import IncidentAuditLog
from models.report import SeverityLevel, DamageType, Report
from models.poi import POI
from models.priority_setting import PrioritySetting
from core.config import settings


class PriorityService:
    """
    Servicio de cálculo de prioridad de incidentes
    """
    
    # Pesos para el cálculo de score
    WEIGHT_SEVERITY = 0.35      # 35% - Severidad del daño
    WEIGHT_AGE = 0.20           # 20% - Tiempo transcurrido
    WEIGHT_DAMAGE_TYPE = 0.15   # 15% - Tipo de daño
    WEIGHT_LOCATION = 0.20      # 20% - Proximidad a POIs importantes
    WEIGHT_DUPLICATES = 0.10    # 10% - Reportes duplicados en área
    
    # Scores base por severidad (0-100)
    SEVERITY_SCORES = {
        SeverityLevel.BAJA: 25,
        SeverityLevel.MEDIA: 50,
        SeverityLevel.ALTA: 100,
    }
    
    # Scores base por tipo de daño (0-100)
    DAMAGE_TYPE_SCORES = {
        DamageType.BACHE: 80,    # Baches son más peligrosos
        DamageType.GRIETA: 60,   # Grietas son menos urgentes
    }
    
    # Transiciones de estado válidas
    VALID_TRANSITIONS = {
        IncidentStatus.OPEN: [IncidentStatus.IN_PROGRESS, IncidentStatus.CLOSED],
        IncidentStatus.IN_PROGRESS: [IncidentStatus.RESOLVED, IncidentStatus.OPEN],
        IncidentStatus.RESOLVED: [IncidentStatus.VERIFIED, IncidentStatus.IN_PROGRESS],
        IncidentStatus.VERIFIED: [IncidentStatus.CLOSED, IncidentStatus.RESOLVED],
        IncidentStatus.CLOSED: [],  # Estado final
    }
    
    def __init__(self, db: Session):
        self.db = db

    def _get_priority_settings(self) -> Optional[PrioritySetting]:
        try:
            return self.db.query(PrioritySetting).order_by(PrioritySetting.id.asc()).first()
        except Exception:
            return None

    def _effective_weights(self, cfg: Optional[PrioritySetting] = None) -> tuple[float, float, float, float, float]:
        cfg = cfg or self._get_priority_settings()

        w_severity = float(cfg.weight_severity) if cfg else float(self.WEIGHT_SEVERITY)
        w_age = float(cfg.weight_age) if cfg else float(self.WEIGHT_AGE)
        w_damage = float(cfg.weight_damage_type) if cfg else float(self.WEIGHT_DAMAGE_TYPE)
        w_location = float(cfg.weight_location) if cfg else float(self.WEIGHT_LOCATION)
        w_duplicates = float(cfg.weight_duplicates) if cfg else float(self.WEIGHT_DUPLICATES)

        total = w_severity + w_age + w_damage + w_location + w_duplicates
        if total <= 0:
            return (
                float(self.WEIGHT_SEVERITY),
                float(self.WEIGHT_AGE),
                float(self.WEIGHT_DAMAGE_TYPE),
                float(self.WEIGHT_LOCATION),
                float(self.WEIGHT_DUPLICATES),
            )

        return (
            w_severity / total,
            w_age / total,
            w_damage / total,
            w_location / total,
            w_duplicates / total,
        )
    
    def calculate_priority_score(
        self,
        incident: Incident,
        nearby_pois_count: Optional[int] = None,
        nearby_duplicates_count: Optional[int] = None
    ) -> Tuple[float, PriorityLevel]:
        """
        Calcula el score de prioridad de un incidente (0-100)
        
        Args:
            incident: Incidente a evaluar
            nearby_pois_count: Número de POIs cercanos (si ya se calculó)
            nearby_duplicates_count: Número de reportes duplicados (si ya se calculó)
        
        Returns:
            Tuple[float, PriorityLevel]: Score (0-100) y nivel de prioridad
        """
        score = 0.0
        cfg = self._get_priority_settings()
        w_severity, w_age, w_damage, w_location, w_duplicates = self._effective_weights(cfg)
        
        # 1. Score por severidad (35%)
        severity_score = self.SEVERITY_SCORES.get(incident.severity, 50)
        score += severity_score * w_severity
        
        # 2. Score por edad del incidente (20%)
        age_score = self._calculate_age_score(incident.created_at)
        score += age_score * w_age
        
        # 3. Score por tipo de daño (15%)
        damage_score = self.DAMAGE_TYPE_SCORES.get(incident.damage_type, 50)
        score += damage_score * w_damage
        
        # 4. Score por ubicación - POIs cercanos (20%)
        if nearby_pois_count is None:
            nearby_pois_count = self._count_nearby_pois(incident, cfg)
        location_score = self._calculate_location_score(nearby_pois_count)
        score += location_score * w_location
        
        # 5. Score por reportes duplicados en área (10%)
        if nearby_duplicates_count is None:
            nearby_duplicates_count = self._count_nearby_duplicates(incident, cfg)
        duplicate_score = self._calculate_duplicate_score(nearby_duplicates_count)
        score += duplicate_score * w_duplicates
        
        # Determinar nivel de prioridad
        priority_level = self._score_to_priority_level(score)
        
        return round(score, 2), priority_level

    def calculate_priority_breakdown(self, incident: Incident) -> dict:
        """Retorna desglose detallado del score de prioridad"""
        cfg = self._get_priority_settings()
        w_severity, w_age, w_damage, w_location, w_duplicates = self._effective_weights(cfg)
        nearby_pois_count = self._count_nearby_pois(incident, cfg)
        nearby_duplicates_count = self._count_nearby_duplicates(incident, cfg)

        severity_score = self.SEVERITY_SCORES.get(incident.severity, 50)
        age_score = self._calculate_age_score(incident.created_at)
        damage_score = self.DAMAGE_TYPE_SCORES.get(incident.damage_type, 50)
        location_score = self._calculate_location_score(nearby_pois_count)
        duplicate_score = self._calculate_duplicate_score(nearby_duplicates_count)

        return {
            "severity":   {"score": round(severity_score * w_severity, 2),   "raw": severity_score,   "weight": round(w_severity, 4),   "detail": str(incident.severity)},
            "age":        {"score": round(age_score * w_age, 2),              "raw": age_score,        "weight": round(w_age, 4),        "detail": f"{nearby_pois_count} POIs cercanos" if False else "antigüedad"},
            "damage":     {"score": round(damage_score * w_damage, 2),   "raw": damage_score,     "weight": round(w_damage, 4), "detail": str(incident.damage_type)},
            "location":   {"score": round(location_score * w_location, 2),   "raw": location_score,   "weight": round(w_location, 4),   "detail": f"{nearby_pois_count} POIs en {self._poi_radius_meters(cfg)}m"},
            "duplicates": {"score": round(duplicate_score * w_duplicates, 2), "raw": duplicate_score, "weight": round(w_duplicates, 4),  "detail": f"{nearby_duplicates_count} reportes visualmente similares"},
        }

    def recalculate_priority(self, incident_id: int, user_id: Optional[int] = None) -> Incident:
        """
        Recalcula y actualiza la prioridad de un incidente

        Args:
            incident_id: ID del incidente
            user_id: ID del usuario que solicita el recálculo (para auditoría)

        Returns:
            Incident actualizado

        Raises:
            ValueError: Si el incidente no existe
        """
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incidente {incident_id} no encontrado")

        old_priority = incident.priority
        old_score = incident.priority_score

        # Calcular nuevo score
        score, priority_level = self.calculate_priority_score(incident)

        # Actualizar
        incident.priority_score = score
        incident.priority = priority_level
        incident.updated_at = datetime.utcnow()

        # Registrar en bitácora (P-07)
        audit_entry = IncidentAuditLog(
            incident_id=incident_id,
            user_id=user_id,
            event_type="priority_recalculated",
            field_name="priority",
            old_value=f"{old_priority.value} ({old_score})" if old_priority else None,
            new_value=f"{priority_level.value} ({score})",
        )
        self.db.add(audit_entry)

        self.db.commit()
        self.db.refresh(incident)

        return incident
    
    def update_incident_status(
        self,
        incident_id: int,
        new_status: IncidentStatus,
        notes: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Incident:
        """
        Actualiza el estado de un incidente con validación de transiciones
        
        Args:
            incident_id: ID del incidente
            new_status: Nuevo estado
            notes: Notas opcionales
            user_id: ID del usuario que hace el cambio
        
        Returns:
            Incident actualizado
        
        Raises:
            ValueError: Si el incidente no existe o la transición es inválida
        """
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incidente {incident_id} no encontrado")
        
        # Validar transición
        if not self._is_valid_transition(incident.status, new_status):
            raise ValueError(
                f"Transición inválida: {incident.status} -> {new_status}. "
                f"Transiciones permitidas: {self.VALID_TRANSITIONS.get(incident.status, [])}"
            )
        
        # Actualizar estado
        old_status = incident.status
        incident.status = new_status
        incident.updated_at = datetime.utcnow()
        
        # Actualizar timestamps según el estado
        if new_status == IncidentStatus.IN_PROGRESS and not incident.started_at:
            incident.started_at = datetime.utcnow()
        elif new_status == IncidentStatus.RESOLVED and not incident.completed_at:
            incident.completed_at = datetime.utcnow()
        elif new_status == IncidentStatus.VERIFIED:
            incident.verified_at = datetime.utcnow()
            incident.is_verified = True
            if user_id:
                incident.verified_by = user_id
        
        # Registrar en bitácora de auditoría (P-07)
        audit_entry = IncidentAuditLog(
            incident_id=incident_id,
            user_id=user_id,
            event_type="status_change",
            field_name="status",
            old_value=old_status.value,
            new_value=new_status.value,
            notes=notes,
        )
        self.db.add(audit_entry)

        self.db.commit()
        self.db.refresh(incident)
        
        return incident
    
    def _calculate_age_score(self, created_at: datetime) -> float:
        """
        Calcula score basado en la edad del incidente (0-100)
        Incidentes más antiguos tienen mayor prioridad
        
        Args:
            created_at: Fecha de creación del incidente
        
        Returns:
            Score 0-100
        """
        now = datetime.utcnow()
        age_hours = (now - created_at).total_seconds() / 3600
        
        # Score aumenta linealmente hasta 168 horas (7 días)
        # Después de 7 días, score máximo de 100
        if age_hours >= 168:
            return 100.0
        else:
            return (age_hours / 168) * 100
    
    def _poi_radius_meters(self, cfg: Optional[PrioritySetting] = None) -> int:
        cfg = cfg or self._get_priority_settings()
        if cfg and cfg.poi_radius_meters:
            return int(cfg.poi_radius_meters)
        return int(getattr(settings, 'PRIORITY_POI_RADIUS_METERS', 500))

    def _duplicate_radius_meters(self, cfg: Optional[PrioritySetting] = None) -> int:
        cfg = cfg or self._get_priority_settings()
        if cfg and cfg.duplicate_radius_meters:
            return int(cfg.duplicate_radius_meters)
        return int(getattr(settings, 'PRIORITY_DUPLICATE_RADIUS_METERS', 100))

    def _duplicate_window_days(self, cfg: Optional[PrioritySetting] = None) -> int:
        cfg = cfg or self._get_priority_settings()
        if cfg and cfg.duplicate_time_window_days:
            return int(cfg.duplicate_time_window_days)
        return int(getattr(settings, 'PRIORITY_DUPLICATE_TIME_WINDOW_DAYS', 30))

    def _count_nearby_pois(self, incident: Incident, cfg: Optional[PrioritySetting] = None) -> int:
        """
        Cuenta POIs importantes dentro de radio configurable
        
        Args:
            incident: Incidente a evaluar
        
        Returns:
            Número de POIs cercanos
        """
        radius_meters = self._poi_radius_meters(cfg)
        
        try:
            count = self.db.query(func.count(POI.id)).filter(
                ST_DWithin(
                    POI.location,
                    incident.location,
                    radius_meters
                )
            ).scalar()
            return count or 0
        except Exception:
            # Si no hay tabla POI o hay error, retornar 0
            return 0
    
    def _count_nearby_duplicates(self, incident: Incident, cfg: Optional[PrioritySetting] = None) -> int:
        """
        Cuenta reportes similares cercanos para prioridad.
        Se aplica filtro visual para evitar falsos duplicados por cercania.
        """
        radius_meters = self._duplicate_radius_meters(cfg)
        time_window_days = self._duplicate_window_days(cfg)
        visual_gate = float(getattr(settings, "DEDUP_VISUAL_GATE_THRESHOLD", 0.82))
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)

        try:
            candidate_reports = self.db.query(Report).filter(
                and_(
                    Report.id != incident.report_id,
                    Report.damage_type == incident.damage_type,
                    Report.created_at >= cutoff_date,
                    ST_DWithin(
                        Report.location,
                        incident.location,
                        radius_meters
                    )
                )
            ).all()

            if not candidate_reports:
                return 0

            from services.deduplication_service import load_image_from_url, compute_visual_similarity

            base_image = load_image_from_url(incident.before_image_url) if incident.before_image_url else None
            if base_image is None:
                return 0

            similar_count = 0
            for report in candidate_reports:
                if not report.image_url:
                    continue

                candidate_image = load_image_from_url(report.image_url)
                if candidate_image is None:
                    continue

                similarity = compute_visual_similarity(base_image, candidate_image)
                if similarity is None:
                    continue

                if similarity >= visual_gate:
                    similar_count += 1

            return similar_count
        except Exception:
            return 0

    def _calculate_location_score(self, nearby_pois_count: int) -> float:
        """
        Calcula score basado en proximidad a POIs (0-100)
        
        Args:
            nearby_pois_count: Número de POIs cercanos
        
        Returns:
            Score 0-100
        """
        if nearby_pois_count == 0:
            return 0.0
        elif nearby_pois_count <= 2:
            return 40.0
        elif nearby_pois_count <= 5:
            return 70.0
        else:
            return 100.0
    
    def _calculate_duplicate_score(self, nearby_duplicates_count: int) -> float:
        """
        Calcula score basado en reportes duplicados (0-100)
        Más duplicados = mayor prioridad (problema recurrente)
        
        Args:
            nearby_duplicates_count: Número de duplicados
        
        Returns:
            Score 0-100
        """
        if nearby_duplicates_count == 0:
            return 0.0
        elif nearby_duplicates_count <= 2:
            return 30.0
        elif nearby_duplicates_count <= 5:
            return 60.0
        else:
            return 100.0
    
    def _score_to_priority_level(self, score: float) -> PriorityLevel:
        """
        Convierte score numérico a nivel de prioridad
        
        Args:
            score: Score 0-100
        
        Returns:
            PriorityLevel
        """
        if score >= 75:
            return PriorityLevel.CRITICA
        elif score >= 50:
            return PriorityLevel.ALTA
        elif score >= 25:
            return PriorityLevel.MEDIA
        else:
            return PriorityLevel.BAJA
    
    def _is_valid_transition(
        self,
        current_status: IncidentStatus,
        new_status: IncidentStatus
    ) -> bool:
        """
        Valida si una transición de estado es permitida
        
        Args:
            current_status: Estado actual
            new_status: Estado destino
        
        Returns:
            True si la transición es válida
        """
        if current_status == new_status:
            return True  # Permitir asignación al mismo estado
        
        valid_next_states = self.VALID_TRANSITIONS.get(current_status, [])
        return new_status in valid_next_states


def get_priority_service(db: Session) -> PriorityService:
    """
    Factory function para obtener instancia del servicio
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        PriorityService
    """
    return PriorityService(db)
