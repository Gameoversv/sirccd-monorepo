"""
Tests para el Servicio de Priorización (B-08)

Verifica:
- Cálculo de scores de prioridad
- Transiciones de estado válidas e inválidas  
- Ponderación de factores
- Conversión de score a nivel de prioridad
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Mock de los imports de SQLAlchemy/GeoAlchemy
import sys
sys.path.insert(0, '..')

# Simular imports antes de importar el servicio
from models.report import SeverityLevel, DamageType


def test_severity_scores():
    """Test 1: Verificar scores base por severidad"""
    print("\n" + "="*60)
    print("TEST 1: Scores base por severidad")
    print("="*60)
    
    from services.priority_service import PriorityService
    
    expected_scores = {
        SeverityLevel.ALTA: 100,
        SeverityLevel.MEDIA: 50,
        SeverityLevel.BAJA: 25
    }
    
    assert PriorityService.SEVERITY_SCORES == expected_scores
    print("✓ Scores de severidad correctos:")
    for severity, score in expected_scores.items():
        print(f"  - {severity.value}: {score}")
    
    print("\n✅ TEST 1 PASADO\n")


def test_damage_type_scores():
    """Test 2: Verificar scores base por tipo de daño"""
    print("="*60)
    print("TEST 2: Scores base por tipo de daño")
    print("="*60)
    
    from services.priority_service import PriorityService
    
    expected_scores = {
        DamageType.BACHE: 80,
        DamageType.GRIETA: 60
    }
    
    assert PriorityService.DAMAGE_TYPE_SCORES == expected_scores
    print("✓ Scores de tipo de daño correctos:")
    for damage_type, score in expected_scores.items():
        print(f"  - {damage_type.value}: {score}")
    
    print("\n✅ TEST 2 PASADO\n")


def test_weight_factors():
    """Test 3: Verificar que los pesos suman 1.0"""
    print("="*60)
    print("TEST 3: Pesos del algoritmo")
    print("="*60)
    
    from services.priority_service import PriorityService
    
    total_weight = (
        PriorityService.WEIGHT_SEVERITY +
        PriorityService.WEIGHT_AGE +
        PriorityService.WEIGHT_DAMAGE_TYPE +
        PriorityService.WEIGHT_LOCATION +
        PriorityService.WEIGHT_DUPLICATES
    )
    
    print(f"Pesos individuales:")
    print(f"  - Severidad: {PriorityService.WEIGHT_SEVERITY * 100}%")
    print(f"  - Edad: {PriorityService.WEIGHT_AGE * 100}%")
    print(f"  - Tipo de daño: {PriorityService.WEIGHT_DAMAGE_TYPE * 100}%")
    print(f"  - Ubicación: {PriorityService.WEIGHT_LOCATION * 100}%")
    print(f"  - Duplicados: {PriorityService.WEIGHT_DUPLICATES * 100}%")
    print(f"\nSuma total: {total_weight}")
    
    assert abs(total_weight - 1.0) < 0.001, f"Los pesos deben sumar 1.0, suma actual: {total_weight}"
    print("✓ Los pesos suman correctamente 1.0")
    
    print("\n✅ TEST 3 PASADO\n")


def test_age_score_calculation():
    """Test 4: Calcular score por edad del incidente"""
    print("="*60)
    print("TEST 4: Cálculo de score por edad")
    print("="*60)
    
    from services.priority_service import PriorityService
    
    # Mock de db session
    mock_db = Mock()
    service = PriorityService(mock_db)
    
    now = datetime.utcnow()
    
    test_cases = [
        (now, 0.0, "Recién creado"),
        (now - timedelta(hours=24), 14.3, "1 día"),
        (now - timedelta(hours=72), 42.9, "3 días"),
        (now - timedelta(hours=168), 100.0, "7 días"),
        (now - timedelta(hours=336), 100.0, "14 días (máximo)")
    ]
    
    print("Escenarios de edad:")
    for created_at, expected_score, description in test_cases:
        actual_score = service._calculate_age_score(created_at)
        print(f"  - {description}: {actual_score:.1f} (esperado: ~{expected_score})")
        assert abs(actual_score - expected_score) < 1.0, f"Score de edad incorrecto para {description}"
    
    print("\n✅ TEST 4 PASADO\n")


def test_location_score_calculation():
    """Test 5: Calcular score por ubicación (POIs cercanos)"""
    print("="*60)
    print("TEST 5: Cálculo de score por ubicación")
    print("="*60)
    
    from services.priority_service import PriorityService
    
    mock_db = Mock()
    service = PriorityService(mock_db)
    
    test_cases = [
        (0, 0.0, "Zona rural (sin POIs)"),
        (1, 40.0, "1 POI cercano"),
        (3, 70.0, "3 POIs cercanos"),
        (6, 100.0, "6+ POIs (zona céntrica)")
    ]
    
    print("Escenarios de ubicación:")
    for pois_count, expected_score, description in test_cases:
        actual_score = service._calculate_location_score(pois_count)
        print(f"  - {description}: {actual_score:.1f}")
        assert actual_score == expected_score, f"Score de ubicación incorrecto para {pois_count} POIs"
    
    print("\n✅ TEST 5 PASADO\n")


def test_duplicate_score_calculation():
    """Test 6: Calcular score por reportes duplicados"""
    print("="*60)
    print("TEST 6: Cálculo de score por duplicados")
    print("="*60)
    
    from services.priority_service import PriorityService
    
    mock_db = Mock()
    service = PriorityService(mock_db)
    
    test_cases = [
        (0, 0.0, "Incidente aislado"),
        (2, 30.0, "2 duplicados"),
        (4, 60.0, "4 duplicados"),
        (8, 100.0, "8+ duplicados (crítico)")
    ]
    
    print("Escenarios de duplicados:")
    for duplicates_count, expected_score, description in test_cases:
        actual_score = service._calculate_duplicate_score(duplicates_count)
        print(f"  - {description}: {actual_score:.1f}")
        assert actual_score == expected_score, f"Score de duplicados incorrecto para {duplicates_count}"
    
    print("\n✅ TEST 6 PASADO\n")


def test_score_to_priority_level():
    """Test 7: Conversión de score a nivel de prioridad"""
    print("="*60)
    print("TEST 7: Conversión score → nivel de prioridad")
    print("="*60)
    
    from services.priority_service import PriorityService
    from models.incident import PriorityLevel
    
    mock_db = Mock()
    service = PriorityService(mock_db)
    
    test_cases = [
        (10, PriorityLevel.BAJA, "Score 10 → BAJA"),
        (24, PriorityLevel.BAJA, "Score 24 → BAJA"),
        (25, PriorityLevel.MEDIA, "Score 25 → MEDIA"),
        (49, PriorityLevel.MEDIA, "Score 49 → MEDIA"),
        (50, PriorityLevel.ALTA, "Score 50 → ALTA"),
        (74, PriorityLevel.ALTA, "Score 74 → ALTA"),
        (75, PriorityLevel.CRITICA, "Score 75 → CRITICA"),
        (100, PriorityLevel.CRITICA, "Score 100 → CRITICA")
    ]
    
    print("Conversiones:")
    for score, expected_level, description in test_cases:
        actual_level = service._score_to_priority_level(score)
        print(f"  - {description}: {actual_level.value}")
        assert actual_level == expected_level, f"Nivel incorrecto para score {score}"
    
    print("\n✅ TEST 7 PASADO\n")


def test_valid_transitions():
    """Test 8: Verificar transiciones de estado válidas"""
    print("="*60)
    print("TEST 8: Transiciones de estado válidas")
    print("="*60)
    
    from services.priority_service import PriorityService
    from models.incident import IncidentStatus
    
    mock_db = Mock()
    service = PriorityService(mock_db)
    
    # Transiciones que DEBEN ser válidas
    valid_transitions = [
        (IncidentStatus.OPEN, IncidentStatus.ASSIGNED, "OPEN → ASSIGNED"),
        (IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS, "ASSIGNED → IN_PROGRESS"),
        (IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED, "IN_PROGRESS → RESOLVED"),
        (IncidentStatus.RESOLVED, IncidentStatus.VERIFIED, "RESOLVED → VERIFIED"),
        (IncidentStatus.VERIFIED, IncidentStatus.CLOSED, "VERIFIED → CLOSED"),
        # Retrocesos permitidos
        (IncidentStatus.ASSIGNED, IncidentStatus.OPEN, "ASSIGNED → OPEN (reasignación)"),
        (IncidentStatus.RESOLVED, IncidentStatus.IN_PROGRESS, "RESOLVED → IN_PROGRESS (reabrir)")
    ]
    
    print("Transiciones válidas:")
    for current, new, description in valid_transitions:
        is_valid = service._is_valid_transition(current, new)
        print(f"  - {description}: {'✓' if is_valid else '✗'}")
        assert is_valid, f"Transición {description} debería ser válida"
    
    print("\n✅ TEST 8 PASADO\n")


def test_invalid_transitions():
    """Test 9: Verificar transiciones de estado inválidas"""
    print("="*60)
    print("TEST 9: Transiciones de estado inválidas")
    print("="*60)
    
    from services.priority_service import PriorityService
    from models.incident import IncidentStatus
    
    mock_db = Mock()
    service = PriorityService(mock_db)
    
    # Transiciones que NO deben ser válidas
    invalid_transitions = [
        (IncidentStatus.OPEN, IncidentStatus.RESOLVED, "OPEN → RESOLVED (saltar pasos)"),
        (IncidentStatus.OPEN, IncidentStatus.VERIFIED, "OPEN → VERIFIED (saltar pasos)"),
        (IncidentStatus.ASSIGNED, IncidentStatus.RESOLVED, "ASSIGNED → RESOLVED (sin trabajo)"),
        (IncidentStatus.CLOSED, IncidentStatus.OPEN, "CLOSED → OPEN (reabrir cerrado)"),
        (IncidentStatus.CLOSED, IncidentStatus.ASSIGNED, "CLOSED → ASSIGNED (estado final)")
    ]
    
    print("Transiciones inválidas (deben fallar):")
    for current, new, description in invalid_transitions:
        is_valid = service._is_valid_transition(current, new)
        print(f"  - {description}: {'✗ (correcto)' if not is_valid else '✓ (ERROR!)'}")
        assert not is_valid, f"Transición {description} NO debería ser válida"
    
    print("\n✅ TEST 9 PASADO\n")


def test_full_score_calculation():
    """Test 10: Cálculo completo de score (caso integrado)"""
    print("="*60)
    print("TEST 10: Cálculo completo de score")
    print("="*60)
    
    from services.priority_service import PriorityService
    from models.incident import PriorityLevel
    
    # Crear mock de incidente con todos los atributos
    mock_incident = Mock()
    mock_incident.severity = SeverityLevel.ALTA  # 100 puntos
    mock_incident.created_at = datetime.utcnow() - timedelta(hours=72)  # 3 días ≈ 42.9 puntos
    mock_incident.damage_type = DamageType.BACHE  # 80 puntos
    mock_incident.location = Mock()
    
    mock_db = Mock()
    service = PriorityService(mock_db)
    
    # Simular conteos
    nearby_pois = 5  # 70 puntos
    nearby_duplicates = 3  # 60 puntos
    
    score, priority = service.calculate_priority_score(
        incident=mock_incident,
        nearby_pois_count=nearby_pois,
        nearby_duplicates_count=nearby_duplicates
    )
    
    # Cálculo esperado:
    # (100 × 0.35) + (42.9 × 0.20) + (80 × 0.15) + (70 × 0.20) + (60 × 0.10)
    # = 35 + 8.58 + 12 + 14 + 6
    # = 75.58 → CRITICA
    
    expected_min = 74.0
    expected_max = 77.0
    
    print(f"\nEscenario: Bache severo en zona céntrica (3 días)")
    print(f"  - Severidad: ALTA (100 × 0.35 = 35.0)")
    print(f"  - Edad: 3 días (~42.9 × 0.20 = 8.6)")
    print(f"  - Tipo: BACHE (80 × 0.15 = 12.0)")
    print(f"  - Ubicación: 5 POIs (70 × 0.20 = 14.0)")
    print(f"  - Duplicados: 3 (60 × 0.10 = 6.0)")
    print(f"\n  Score final: {score}")
    print(f"  Prioridad: {priority.value}")
    
    assert expected_min <= score <= expected_max, f"Score debe estar entre {expected_min} y {expected_max}, obtenido: {score}"
    assert priority == PriorityLevel.CRITICA, f"Prioridad debe ser CRITICA, obtenida: {priority}"
    
    print("\n✅ TEST 10 PASADO\n")


def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "🧪"*30)
    print("TESTS DEL SERVICIO DE PRIORIZACIÓN (B-08)")
    print("🧪"*30 + "\n")
    
    tests = [
        test_severity_scores,
        test_damage_type_scores,
        test_weight_factors,
        test_age_score_calculation,
        test_location_score_calculation,
        test_duplicate_score_calculation,
        test_score_to_priority_level,
        test_valid_transitions,
        test_invalid_transitions,
        test_full_score_calculation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FALLÓ: {e}\n")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}\n")
            failed += 1
    
    print("="*60)
    print("RESUMEN DE TESTS")
    print("="*60)
    print(f"✅ Pasados: {passed}/{len(tests)}")
    print(f"❌ Fallidos: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 TODOS LOS TESTS PASARON 🎉")
        print("\n✓ El servicio de priorización está listo para usar")
        print("✓ Algoritmo de cálculo validado")
        print("✓ Transiciones de estado correctas")
    else:
        print(f"\n⚠️ {failed} test(s) fallaron")
    
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
