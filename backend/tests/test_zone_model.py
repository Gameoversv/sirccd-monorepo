import pytest
from geoalchemy2 import WKTElement
from models.zone import Zone


# Use in-memory SQLite is not viable for PostGIS — skip unit test,
# integration test against running DB is done in Task 3.
# This test just verifies the model can be imported and instantiated.

def test_zone_model_fields():
    zone = Zone(
        name="Centro Histórico",
        code="STG-CTR",
        boundary=WKTElement(
            "POLYGON((-70.706 19.441, -70.693 19.441, -70.693 19.453, -70.706 19.453, -70.706 19.441))",
            srid=4326
        )
    )
    assert zone.name == "Centro Histórico"
    assert zone.code == "STG-CTR"
