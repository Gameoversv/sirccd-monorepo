# P-03 Geospatial Zone Filters — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add administrative zone boundaries (PostGIS polygons) and wire them end-to-end: seed GeoJSON → Zone model → backend ST_Within filter → date range filter → frontend zone selector UI.

**Architecture:** A new `zones` table stores polygon boundaries as PostGIS `Geography(POLYGON, 4326)`. Incidents are filtered with `ST_Within(incident.location, zone.boundary)`. The frontend fetches zone names from a new `/zones` endpoint and passes a `zone_id` query param to `/incidents`.

**Tech Stack:** SQLAlchemy + GeoAlchemy2 + PostGIS `ST_Within`, Alembic migrations, FastAPI, React + TypeScript, Leaflet for zone boundary rendering.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `backend/models/zone.py` | Create | Zone SQLAlchemy model |
| `backend/models/__init__.py` | Modify | Export Zone model |
| `backend/schemas/zone.py` | Create | Pydantic schemas for Zone |
| `backend/api/routes/zones.py` | Create | `GET /zones` endpoint |
| `backend/api/routes/incidents.py` | Modify | Add `date_from`, `date_to`, `zone_id` params to `list_incidents` |
| `backend/main.py` | Modify | Register zones router |
| `backend/alembic/versions/004_add_zones_table.py` | Create | Migration: zones table |
| `backend/scripts/seed_zones.py` | Create | Seed Santiago zone GeoJSON into DB |
| `backend/data/santiago_zones.geojson` | Create | GeoJSON with zone polygons |
| `frontend/src/types/index.ts` | Modify | Add `Zone`, `ZoneFilters` types; add `zone_id` to `IncidentFilters` |
| `frontend/src/services/zonesService.ts` | Create | `GET /zones` API call |
| `frontend/src/components/FilterPanel.tsx` | Modify | Add zone selector section |
| `frontend/src/components/MapView.tsx` | Modify | Render zone boundary polygons on map |

---

## Task 1: Zone model and migration

**Files:**
- Create: `backend/models/zone.py`
- Modify: `backend/models/__init__.py`
- Create: `backend/alembic/versions/004_add_zones_table.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_zone_model.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import WKTElement
from db.base import Base
from models.zone import Zone

# Use in-memory SQLite is not viable for PostGIS — skip unit test,
# integration test against running DB is done in Task 3.
# This test just verifies the model can be imported and instantiated.

def test_zone_model_fields():
    zone = Zone(
        name="Centro",
        code="CTR-01",
        boundary=WKTElement(
            "POLYGON((-70.706 19.441, -70.693 19.441, -70.693 19.453, -70.706 19.453, -70.706 19.441))",
            srid=4326
        )
    )
    assert zone.name == "Centro"
    assert zone.code == "CTR-01"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_zone_model.py -v
```

Expected: `ImportError: cannot import name 'Zone' from 'models.zone'`

- [ ] **Step 3: Create `backend/models/zone.py`**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from geoalchemy2 import Geography
from db.base import Base


class Zone(Base):
    """Administrative zone boundary (polygon)."""
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=True, unique=True, index=True)
    boundary = Column(Geography(geometry_type="POLYGON", srid=4326), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Zone {self.id} - {self.name}>"
```

- [ ] **Step 4: Export from `backend/models/__init__.py`**

Add to imports:
```python
from .zone import Zone
```

Add to `__all__`:
```python
"Zone",
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/test_zone_model.py -v
```

Expected: PASS

- [ ] **Step 6: Create migration `backend/alembic/versions/004_add_zones_table.py`**

```python
"""add zones table

Revision ID: 004
Revises: 003
Create Date: 2026-05-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column(
            "boundary",
            Geography(geometry_type="POLYGON", srid=4326),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_zones_id"), "zones", ["id"], unique=False)
    op.create_index(op.f("ix_zones_name"), "zones", ["name"], unique=True)
    op.create_index(op.f("ix_zones_code"), "zones", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_zones_code"), table_name="zones")
    op.drop_index(op.f("ix_zones_name"), table_name="zones")
    op.drop_index(op.f("ix_zones_id"), table_name="zones")
    op.drop_table("zones")
```

- [ ] **Step 7: Run migration**

```bash
cd backend && alembic upgrade 004
```

Expected: `Running upgrade 003 -> 004`

- [ ] **Step 8: Commit**

```bash
git add backend/models/zone.py backend/models/__init__.py \
        backend/alembic/versions/004_add_zones_table.py \
        backend/tests/test_zone_model.py
git commit -m "feat: add Zone model and zones table migration"
```

---

## Task 2: Santiago de los Caballeros GeoJSON seed data + seed script

**Files:**
- Create: `backend/data/santiago_zones.geojson`
- Create: `backend/scripts/seed_zones.py`

Context: Santiago de los Caballeros, Dominican Republic (~19.45°N, -70.70°W). The polygons below are **approximate rectangles** for major sectors — replace with official ONE/GADM boundaries before going to production. Official source: [one.gob.do](https://one.gob.do) or GADM level 4 for Dominican Republic.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_seed_zones.py`:

```python
import json
import pytest
from pathlib import Path


def test_geojson_structure():
    path = Path(__file__).parent.parent / "data" / "santiago_zones.geojson"
    assert path.exists(), "santiago_zones.geojson not found"
    data = json.loads(path.read_text())
    assert data["type"] == "FeatureCollection"
    features = data["features"]
    assert len(features) >= 5, "Need at least 5 zone polygons"
    for f in features:
        assert f["type"] == "Feature"
        assert f["geometry"]["type"] in ("Polygon", "MultiPolygon")
        assert "name" in f["properties"]
        assert "code" in f["properties"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_seed_zones.py -v
```

Expected: `AssertionError: santiago_zones.geojson not found`

- [ ] **Step 3: Create `backend/data/santiago_zones.geojson`**

> ⚠️ These are approximate bounding rectangles. Replace with official ONE/GADM polygons before production.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "name": "Centro Histórico", "code": "STG-CTR" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-70.706, 19.441], [-70.693, 19.441],
          [-70.693, 19.453], [-70.706, 19.453],
          [-70.706, 19.441]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Los Jardines", "code": "STG-JAR" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-70.693, 19.453], [-70.678, 19.453],
          [-70.678, 19.466], [-70.693, 19.466],
          [-70.693, 19.453]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Pueblo Nuevo", "code": "STG-PNV" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-70.720, 19.441], [-70.706, 19.441],
          [-70.706, 19.453], [-70.720, 19.453],
          [-70.720, 19.441]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Bella Vista", "code": "STG-BVS" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-70.720, 19.453], [-70.706, 19.453],
          [-70.706, 19.466], [-70.720, 19.466],
          [-70.720, 19.453]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "La Joya", "code": "STG-JOY" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-70.693, 19.428], [-70.678, 19.428],
          [-70.678, 19.441], [-70.693, 19.441],
          [-70.693, 19.428]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Villa Olga", "code": "STG-VOL" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-70.720, 19.466], [-70.706, 19.466],
          [-70.706, 19.479], [-70.720, 19.479],
          [-70.720, 19.466]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Ensanche Espaillat", "code": "STG-ESP" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-70.706, 19.453], [-70.693, 19.453],
          [-70.693, 19.466], [-70.706, 19.466],
          [-70.706, 19.453]
        ]]
      }
    }
  ]
}
```

- [ ] **Step 4: Create `backend/scripts/seed_zones.py`**

```python
"""Seed administrative zone boundaries from GeoJSON into the zones table.

Usage (from backend/):
    python -m scripts.seed_zones
"""
import json
import sys
from pathlib import Path

# Allow running as a module from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from models.zone import Zone
from geoalchemy2.shape import from_shape
from shapely.geometry import shape


DATA_PATH = Path(__file__).parent.parent / "data" / "santiago_zones.geojson"


def seed_zones() -> None:
    db = SessionLocal()
    try:
        geojson = json.loads(DATA_PATH.read_text())
        inserted = 0
        skipped = 0
        for feature in geojson["features"]:
            props = feature["properties"]
            name: str = props["name"]
            code: str = props["code"]
            geom = shape(feature["geometry"])

            existing = db.query(Zone).filter(Zone.code == code).first()
            if existing:
                skipped += 1
                continue

            zone = Zone(
                name=name,
                code=code,
                boundary=from_shape(geom, srid=4326),
            )
            db.add(zone)
            inserted += 1

        db.commit()
        print(f"Seeded {inserted} zones, skipped {skipped} existing.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_zones()
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/test_seed_zones.py -v
```

Expected: PASS

- [ ] **Step 6: Run seed script against running DB**

```bash
cd backend && python -m scripts.seed_zones
```

Expected: `Seeded 6 zones, skipped 0 existing.`

- [ ] **Step 7: Verify in DB**

```bash
docker exec -it sirccd-postgres psql -U postgres -d sirccd -c "SELECT id, name, code FROM zones;"
```

Expected: 6 rows.

- [ ] **Step 8: Commit**

```bash
git add backend/data/santiago_zones.geojson backend/scripts/seed_zones.py \
        backend/tests/test_seed_zones.py
git commit -m "feat: add Santiago de los Caballeros zone GeoJSON and seed script"
```

---

## Task 3: Zones API endpoint + Pydantic schemas

**Files:**
- Create: `backend/schemas/zone.py`
- Create: `backend/api/routes/zones.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_zones_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)


def test_list_zones_requires_auth():
    response = client.get("/api/zones/")
    assert response.status_code == 401


def test_zones_schema_import():
    from schemas.zone import ZoneBriefResponse, ZoneListResponse
    z = ZoneBriefResponse(id=1, name="Centro Histórico", code="STG-CTR")
    assert z.name == "Centro"
    lst = ZoneListResponse(total=1, zones=[z])
    assert lst.total == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_zones_api.py -v
```

Expected: `ImportError: cannot import name 'ZoneBriefResponse'`

- [ ] **Step 3: Create `backend/schemas/zone.py`**

```python
from pydantic import BaseModel
from typing import List, Optional


class ZoneBriefResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None

    model_config = {"from_attributes": True}


class ZoneListResponse(BaseModel):
    total: int
    zones: List[ZoneBriefResponse]
```

- [ ] **Step 4: Create `backend/api/routes/zones.py`**

```python
"""Zones API — list administrative boundaries for filter UI."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from api.deps import get_current_active_user
from models.user import User
from models.zone import Zone
from schemas.zone import ZoneBriefResponse, ZoneListResponse

router = APIRouter()


@router.get("/", response_model=ZoneListResponse)
def list_zones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ZoneListResponse:
    """Return all administrative zones (id, name, code) for the filter selector."""
    zones = db.query(Zone).order_by(Zone.name).all()
    return ZoneListResponse(
        total=len(zones),
        zones=[ZoneBriefResponse.model_validate(z) for z in zones],
    )
```

- [ ] **Step 5: Register router in `backend/main.py`**

Find the section where other routers are included (look for `app.include_router`). Add:

```python
from api.routes import zones as zones_router
# ...
app.include_router(zones_router.router, prefix="/api/zones", tags=["zones"])
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/test_zones_api.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/schemas/zone.py backend/api/routes/zones.py \
        backend/main.py backend/tests/test_zones_api.py
git commit -m "feat: add zones API endpoint GET /api/zones/"
```

---

## Task 4: Backend date range + zone_id filters on `list_incidents`

**Files:**
- Modify: `backend/api/routes/incidents.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_incidents_filters.py` (create if not exists):

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)


def _auth_headers():
    # Replace with your test auth helper or a valid JWT for tests.
    # Assuming get_current_active_user can be overridden:
    return {}


def test_date_range_params_accepted(monkeypatch):
    """Backend must not reject date_from / date_to query params."""
    from api import deps
    mock_user = MagicMock()
    mock_user.id = 1

    app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user

    response = client.get(
        "/api/incidents/?date_from=2026-01-01T00:00:00&date_to=2026-12-31T23:59:59"
    )
    # 200 or 422 — if 422 the param is rejected by FastAPI (wrong type/name)
    assert response.status_code != 422, f"Param rejected: {response.json()}"

    app.dependency_overrides.clear()


def test_zone_id_param_accepted(monkeypatch):
    from api import deps
    mock_user = MagicMock()
    mock_user.id = 1

    app.dependency_overrides[deps.get_current_active_user] = lambda: mock_user

    response = client.get("/api/incidents/?zone_id=1")
    assert response.status_code != 422, f"Param rejected: {response.json()}"

    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_incidents_filters.py -v
```

Expected: `test_date_range_params_accepted` returns 422 (param unknown to FastAPI) or test fails.

- [ ] **Step 3: Add `date_from`, `date_to`, `zone_id` to `list_incidents` in `backend/api/routes/incidents.py`**

Add imports at top of file (if not present):
```python
from geoalchemy2.functions import ST_Within
```

Add parameters to `list_incidents` function signature (after `is_verified` param):
```python
date_from: Optional[datetime] = Query(None, description="Filtrar desde fecha (ISO 8601)"),
date_to: Optional[datetime] = Query(None, description="Filtrar hasta fecha (ISO 8601)"),
zone_id: Optional[int] = Query(None, description="Filtrar por zona administrativa (ID)"),
```

Add filter logic after the `is_verified` block (before `if filters:`):
```python
if date_from:
    filters.append(Incident.created_at >= date_from)

if date_to:
    filters.append(Incident.created_at <= date_to)

if zone_id is not None:
    from models.zone import Zone
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if zone:
        filters.append(ST_Within(Incident.location, zone.boundary))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/test_incidents_filters.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/routes/incidents.py backend/tests/test_incidents_filters.py
git commit -m "feat: add date_from, date_to, zone_id filters to list_incidents"
```

---

## Task 5: Frontend types + zones service

**Files:**
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/services/zonesService.ts`

- [ ] **Step 1: Add `Zone` types and `zone_id` to `IncidentFilters` in `frontend/src/types/index.ts`**

Find the `IncidentFilters` interface (line ~175) and add `zone_id`:

```typescript
export interface IncidentFilters {
  status?: IncidentStatus;
  damage_class?: DamageClass;
  severity?: SeverityLevel;
  date_from?: string;
  date_to?: string;
  priority_min?: number;
  priority_max?: number;
  zone_id?: number;           // <-- add this
}
```

Add Zone types near the bottom of the file (after `POILayerFilters`):

```typescript
export interface Zone {
  id: number;
  name: string;
  code?: string;
}

export interface ZoneListResponse {
  total: number;
  zones: Zone[];
}
```

- [ ] **Step 2: Create `frontend/src/services/zonesService.ts`**

```typescript
import apiClient from './api';
import type { ZoneListResponse } from '@/types';

export const zonesService = {
  async getZones(): Promise<ZoneListResponse> {
    const response = await apiClient.get<ZoneListResponse>('/zones/');
    return response.data;
  },
};
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/services/zonesService.ts
git commit -m "feat: add Zone types and zonesService"
```

---

## Task 6: FilterPanel — zone selector section

**Files:**
- Modify: `frontend/src/components/FilterPanel.tsx`

- [ ] **Step 1: Understand current FilterPanel structure**

Read `frontend/src/components/FilterPanel.tsx` lines 26-34 (props interface) and lines 308-381 (POI section) to understand the pattern before modifying.

- [ ] **Step 2: Update `FilterPanelProps` to accept zone data**

Find the `FilterPanelProps` interface (line ~26) and add:

```typescript
interface FilterPanelProps {
  filters: IncidentFilters;
  onChange: (filters: Partial<IncidentFilters>) => void;
  onClear: () => void;
  total?: number;
  layout?: 'horizontal' | 'sidebar';
  poiLayerFilters?: POILayerFilters;
  onPoiLayerFiltersChange?: (filters: POILayerFilters) => void;
  zones?: import('@/types').Zone[];         // <-- add
  zonesLoading?: boolean;                   // <-- add
}
```

- [ ] **Step 3: Add zone import to `FilterPanel.tsx`**

In the imports block, add `MapPin` to the lucide-react imports:
```typescript
import { Filter, ChevronDown, ChevronUp, RotateCcw, AlertTriangle, Activity, Calendar, Gauge, Layers, MapPin } from 'lucide-react';
```

And add `Zone` to the types import:
```typescript
import type { IncidentFilters, SeverityLevel, IncidentStatus, POILayerFilters, POILayerCategory, Zone } from '@/types';
```

- [ ] **Step 4: Add zone selector section inside `FilterPanel` render**

Add this `FilterSection` block after the date range section (before the POI section):

```tsx
<FilterSection
  title={t('filters.zone', 'Zona Administrativa')}
  icon={<MapPin className="h-4 w-4" />}
  defaultOpen={false}
>
  <div className="px-4 pb-3 space-y-1.5">
    {zonesLoading && (
      <p className="text-xs text-muted-foreground">{t('filters.loadingZones', 'Cargando zonas…')}</p>
    )}
    {!zonesLoading && (
      <>
        <button
          type="button"
          onClick={() => onChange({ zone_id: undefined })}
          className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
            filters.zone_id == null
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-muted text-foreground'
          }`}
        >
          {t('filters.allZones', 'Todas las zonas')}
        </button>
        {(zones ?? []).map((zone) => (
          <button
            key={zone.id}
            type="button"
            onClick={() => onChange({ zone_id: zone.id })}
            className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
              filters.zone_id === zone.id
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted text-foreground'
            }`}
          >
            {zone.name}
          </button>
        ))}
      </>
    )}
  </div>
</FilterSection>
```

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/FilterPanel.tsx
git commit -m "feat: add zone selector to FilterPanel"
```

---

## Task 7: Wire zones into the parent page/component

**Files:**
- Modify: the parent component that renders `<FilterPanel>` (find with `grep -r "FilterPanel" frontend/src --include="*.tsx" -l`)

- [ ] **Step 1: Find the parent**

```bash
grep -r "FilterPanel" frontend/src --include="*.tsx" -l
```

Note the file path — it will be something like `frontend/src/app/dashboard/page.tsx` or `frontend/src/components/Dashboard.tsx`.

- [ ] **Step 2: Import zones service and add state**

In the parent component file, add:

```typescript
import { zonesService } from '@/services/zonesService';
import type { Zone } from '@/types';
```

Add inside the component:

```typescript
const [zones, setZones] = useState<Zone[]>([]);
const [zonesLoading, setZonesLoading] = useState(false);

useEffect(() => {
  setZonesLoading(true);
  zonesService.getZones()
    .then((res) => setZones(res.zones))
    .catch(console.error)
    .finally(() => setZonesLoading(false));
}, []);
```

- [ ] **Step 3: Pass props to `<FilterPanel>`**

Find the `<FilterPanel` JSX and add:

```tsx
<FilterPanel
  ...existingProps
  zones={zones}
  zonesLoading={zonesLoading}
/>
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add <parent-component-file>
git commit -m "feat: load zones and pass to FilterPanel"
```

---

## Task 8: Render zone boundaries on the map

**Files:**
- Modify: `frontend/src/components/MapView.tsx` (or wherever Leaflet is used — find with `grep -r "useMap\|L\.map\|MapContainer" frontend/src --include="*.tsx" -l`)

- [ ] **Step 1: Find the map component**

```bash
grep -r "MapContainer\|useMap\|L\.geoJSON" frontend/src --include="*.tsx" -l
```

- [ ] **Step 2: Add props for zone rendering**

In the map component's props interface, add:

```typescript
interface MapViewProps {
  // ...existing props...
  zones?: import('@/types').Zone[];
  selectedZoneId?: number;
}
```

- [ ] **Step 3: Fetch zone GeoJSON for rendering**

Zone polygons for rendering come from a new endpoint `GET /zones/{id}/geojson` OR we embed the boundary in the list response. For the map layer, we need the polygon coordinates. The simplest approach: add a `GeoJSON` field to `ZoneBriefResponse` OR render zone outlines by fetching `/zones/geojson` (a bulk GeoJSON endpoint).

Add a bulk GeoJSON endpoint to `backend/api/routes/zones.py`:

```python
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

@router.get("/geojson")
def zones_geojson(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Return all zones as a GeoJSON FeatureCollection for map rendering."""
    zones = db.query(Zone).order_by(Zone.name).all()
    features = []
    for zone in zones:
        geom = to_shape(zone.boundary)
        features.append({
            "type": "Feature",
            "properties": {"id": zone.id, "name": zone.name, "code": zone.code},
            "geometry": mapping(geom),
        })
    return {"type": "FeatureCollection", "features": features}
```

- [ ] **Step 4: Add `getZonesGeoJSON` to `zonesService.ts`**

```typescript
async getZonesGeoJSON(): Promise<GeoJSON.FeatureCollection> {
  const response = await apiClient.get<GeoJSON.FeatureCollection>('/zones/geojson');
  return response.data;
},
```

Add `@types/geojson` if not present:
```bash
cd frontend && npm install --save-dev @types/geojson
```

- [ ] **Step 5: Render zone polygons on the Leaflet map**

In the map component, add a `useEffect` that fetches zone GeoJSON and adds a Leaflet GeoJSON layer:

```typescript
import { useEffect, useRef } from 'react';
// L is assumed to be imported already

useEffect(() => {
  if (!mapRef.current) return;
  let layer: L.GeoJSON | null = null;

  zonesService.getZonesGeoJSON().then((geojson) => {
    layer = L.geoJSON(geojson, {
      style: (feature) => ({
        color: feature?.properties?.id === selectedZoneId ? '#2563eb' : '#64748b',
        weight: selectedZoneId && feature?.properties?.id === selectedZoneId ? 3 : 1.5,
        fillOpacity: 0.05,
        fillColor: '#64748b',
      }),
      onEachFeature: (feature, lyr) => {
        lyr.bindTooltip(feature.properties.name, { sticky: true });
      },
    }).addTo(mapRef.current!);
  });

  return () => {
    layer?.remove();
  };
}, [selectedZoneId]);
```

- [ ] **Step 6: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add backend/api/routes/zones.py frontend/src/services/zonesService.ts \
        frontend/src/components/MapView.tsx
git commit -m "feat: render zone boundaries on map with Leaflet GeoJSON layer"
```

---

## Task 9: Connect zone filter to map highlight + table reload

**Files:**
- Modify: parent page/component (same file as Task 7)

- [ ] **Step 1: Pass `selectedZoneId` to map**

In the parent component, ensure `filters.zone_id` is passed to `<MapView>` as `selectedZoneId`:

```tsx
<MapView
  ...existingProps
  selectedZoneId={filters.zone_id}
/>
```

- [ ] **Step 2: Verify filter change triggers incident reload**

The `onChange` from `FilterPanel` should already call `incidentsService.getIncidents(filters)` if the parent component has a `useEffect` watching `filters`. Confirm this — if not, add it:

```typescript
useEffect(() => {
  incidentsService.getIncidents(filters).then(setIncidents).catch(console.error);
}, [filters]);
```

- [ ] **Step 3: Manual smoke test**

1. Start dev server: `cd frontend && npm run dev`
2. Login and open the map dashboard.
3. Open FilterPanel → Zone section.
4. Select "Centro" — verify:
   - Map highlights Centro boundary in blue.
   - Incident table/markers update to show only incidents inside Centro.
   - Selecting "Todas las zonas" restores all incidents.
5. Set a date range (date_from = 2026-01-01) — verify incident count changes.

- [ ] **Step 4: Commit**

```bash
git add <parent-component-file>
git commit -m "feat: wire zone filter to map highlight and incident table reload"
```

---

## Self-Review

### Spec coverage

| Requirement | Task |
|-------------|------|
| Zone boundaries (PostGIS polygons) | Task 1 (model + migration) |
| Seed GeoJSON data | Task 2 |
| Backend ST_Within zone filter | Task 4 |
| Backend date range filter | Task 4 |
| Zone list API endpoint | Task 3 |
| Zone GeoJSON endpoint for map | Task 8 |
| Frontend zone selector UI | Task 6 |
| Frontend zone types + service | Task 5 |
| Wire zones into parent page | Task 7 |
| Map boundary highlight | Task 8 |
| Map + table update on filter change | Task 9 |

### No gaps found.

### Type consistency check
- `Zone.id: int` used consistently across `models/zone.py`, `schemas/zone.py`, `types/index.ts`, and the map highlight comparison `feature.properties.id === selectedZoneId`.
- `zone_id: Optional[int]` in `IncidentFilters` (TypeScript) matches `zone_id: Optional[int] = Query(...)` in FastAPI.
- `ZoneBriefResponse.model_validate(z)` uses Pydantic v2 API — consistent with existing schemas (check `schemas/incident.py` uses `model_config = {"from_attributes": True}`).
