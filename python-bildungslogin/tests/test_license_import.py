# -*- coding: utf-8 -*-
import datetime

import attr
import pytest
from jsonschema import ValidationError, validate

from univention.bildungslogin.license_import import LICENSE_SCHEMA, load_license
from univention.bildungslogin.models import License

test_license_raw = {
    "lizenzcode": "VHT-7bd46a45-345c-4237-a451-4444736eb011",
    "product_id": "urn:bilo:medium:A0023#48-85-TZ",
    "lizenzanzahl": 25,
    "lizenzgeber": "VHT",
    "kaufreferenz": "2014-04-11T03:28:16 -02:00 4572022",
    "nutzungssysteme": "Antolin",
    "gueltigkeitsbeginn": "",
    "gueltigkeitsende": "14-08-2022",
    "gueltigkeitsdauer": "Ein Jahr",
    "sonderlizenz": "Lehrer",
}


test_license = License(
    license_code="VHT-7bd46a45-345c-4237-a451-4444736eb011",
    product_id="urn:bilo:medium:A0023#48-85-TZ",
    license_quantity=25,
    license_provider="VHT",
    purchasing_reference="2014-04-11T03:28:16 -02:00 4572022",
    utilization_systems="Antolin",
    validity_start_date=None,
    validity_end_date=datetime.date(2022, 8, 14),
    validity_duration="Ein Jahr",
    license_special_type="Lehrer",
    ignored_for_display=False,
    delivery_date=datetime.date.today(),
    license_school="test_schule",
)


def test_license_schema():
    """Test that the schema works with our sample test_license_raw. We assume the test_license_raw to be valid"""
    validate(instance=test_license_raw, schema=LICENSE_SCHEMA)


@pytest.mark.parametrize("field_name", LICENSE_SCHEMA["required"])
def test_license_schema_validation_required_fails(field_name):
    """A missing value in the license should raise a ValidationError"""
    test_license_broken = test_license_raw.copy()
    del test_license_broken[field_name]
    with pytest.raises(ValidationError):
        validate(instance=test_license_broken, schema=LICENSE_SCHEMA)


@pytest.mark.parametrize(
    "field_name",
    [name for name in LICENSE_SCHEMA["properties"] if name not in LICENSE_SCHEMA["required"]],
)
def test_license_schema_validation_optionals(field_name):
    """An optional value can be left out from the license"""
    test_license_broken = test_license_raw.copy()
    del test_license_broken[field_name]
    validate(instance=test_license_broken, schema=LICENSE_SCHEMA)


def test_license_schema_validation_number_fails():
    """'Lizenzanzahl' has to be a number"""
    test_license_broken = test_license_raw.copy()
    test_license_broken["lizenzanzahl"] = "wrong"
    with pytest.raises(ValidationError):
        validate(instance=test_license_broken, schema=LICENSE_SCHEMA)


def test_load_license():
    """Test that a license loaded from dict are the same as a corresponding python object."""
    license = load_license(test_license_raw, "test_schule")
    assert license.__dict__ == attr.asdict(test_license)


@pytest.mark.parametrize(
    "code,expected", [("abc", "VHT-abc"), ("VHT-abc", "VHT-abc"), ("vHt-ABC", "vHt-ABC")]
)
def test_load_license_missing_provider_in_code(code, expected):
    license_raw = {
        "lizenzcode": code,
        "product_id": "urn:bilo:medium:A0023#48-85-TZ",
        "lizenzanzahl": 25,
        "lizenzgeber": "VHT",
        "kaufreferenz": "2014-04-11T03:28:16 -02:00 4572022",
        "nutzungssysteme": "Antolin",
        "gueltigkeitsbeginn": "",
        "gueltigkeitsende": "14-08-2022",
        "gueltigkeitsdauer": "Ein Jahr",
        "sonderlizenz": "Lehrer",
    }
    """Test that a license loaded from dict has the expected license codes."""
    license = load_license(license_raw, "test_schule")
    assert license.license_code == expected
