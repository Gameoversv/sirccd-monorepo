# Registro de decisiones arquitectónicas (ADR)

[← Volver al índice](../README.md)

Este directorio guarda decisiones arquitectónicas relevantes usando el formato Architecture Decision Record (ADR). Un ADR documenta una decisión, su contexto y sus consecuencias — no un plan a futuro ni un requerimiento.

## Cuándo crear un ADR

- Al elegir entre alternativas técnicas con impacto duradero (framework, estrategia de autenticación, patrón de comunicación entre servicios).
- Al revertir o modificar sustancialmente una decisión previa.
- Al documentar retroactivamente una decisión ya tomada pero nunca registrada (como el ADR-001 de este proyecto).

## Cómo crear uno nuevo

1. Copiar la plantilla de `ADR-001-current-architecture.md`.
2. Numerar secuencialmente (`ADR-002-...`, `ADR-003-...`).
3. Completar Contexto, Decisión, Alternativas consideradas, Consecuencias (positivas y negativas) y Riesgos.
4. No modificar ADRs ya aceptados — si la decisión cambia, crear un ADR nuevo que reemplace al anterior y referenciarlo.

## Índice

- [ADR-001: Arquitectura actual del sistema](ADR-001-current-architecture.md)
