#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# -*- coding: utf-8 -*-
#
# Copyright 2021 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import datetime
import json
import random
import string
import uuid

import ldap
import pytest

import univention.testing.strings as uts
from univention.admin.uldap import getAdminConnection
from univention.bildungslogin.handlers import AssignmentHandler, LicenseHandler, MetaDataHandler
from univention.bildungslogin.models import License, MetaData
from univention.testing.ucr import UCSTestConfigRegistry


def iso_format_date(my_date):
    return my_date.strftime("%Y-%m-%d")


def random_string(n):  # type: (int) -> str
    return "".join([random.choice(string.ascii_uppercase + string.digits) for _ in range(n)])


def product_id():
    return "urn:bilo:medium:{}#{}-{}-{}".format(
        random_string(5), random_string(2), random_string(2), random_string(2)
    )


def get_license():
    today = datetime.datetime.now()
    start = today + datetime.timedelta(days=random.randint(0, 365))
    duration = random.randint(1, 365)
    end = start + datetime.timedelta(duration)
    provider = uts.random_username()
    return License(
        license_code="{}-{}".format(provider, str(uuid.uuid4())),
        product_id=product_id(),
        license_quantity=random.randint(10, 50),
        license_provider=provider,
        # todo this is not exactly equal to this format: "2014-04-11T03:28:16 -02:00 4572022",
        purchasing_reference=today.isoformat(),
        utilization_systems=uts.random_username(),
        validity_start_date=iso_format_date(start),
        validity_end_date=iso_format_date(end),
        validity_duration=str(duration),
        # as default, set 'Lehrer' in test or create a new fixture for that
        license_special_type="",
        ignored_for_display=random.choice(["0", "1"]),
        delivery_date=iso_format_date(today),
        license_school=uts.random_name(),
    )


def get_expired_license():
    """ "the end_date + duration < today"""
    today = datetime.datetime.now()
    duration = random.randint(1, 365)
    start = today - datetime.timedelta(duration)
    license = get_license()
    license.validity_start_date = start
    license.validity_end_date = today - datetime.timedelta(1)
    license.validity_duration = duration
    return license


@pytest.fixture(scope="function")
def expired_license():
    return get_expired_license()


@pytest.fixture(scope="function")
def n_expired_licenses():
    n = random.randint(1, 10)
    return [expired_license() for _ in range(n)]


@pytest.fixture(scope="function")
def license():
    return get_license()


@pytest.fixture(scope="function")
def n_licenses():
    n = random.randint(1, 10)
    return [get_license() for _ in range(n)]


def get_meta_data():
    return MetaData(
        product_id=uts.random_name(),
        title=uts.random_name(),
        description="some description",
        author=uts.random_name(),
        publisher=uts.random_name(),
        cover=uts.random_name(),
        cover_small=uts.random_name(),
        modified=datetime.datetime.now().strftime("%Y-%m-%d"),
    )


@pytest.fixture(scope="function")
def meta_data():
    return get_meta_data()


@pytest.fixture(scope="function")
def n_meta_data():
    n = random.randint(1, 10)
    return [get_meta_data() for _ in range(n)]


@pytest.fixture()
def lo():
    """this is to simplify some of our tests with the simple udm api,
    so we do not have to use the ucs-test school env all the time."""

    def add_temp(_dn, *args, **kwargs):
        lo.add_orig(_dn, *args, **kwargs)
        created_objs.append(_dn)

    created_objs = []
    lo, po = getAdminConnection()
    lo.add_orig = lo.add
    lo.add = add_temp
    yield lo
    # we need to sort the dns to first delete the child-nodes
    created_objs.sort(key=lambda _dn: len(ldap.explode_dn(_dn)), reverse=True)
    for dn in created_objs:
        lo.delete(dn)


@pytest.fixture()
def license_handler(lo):
    return LicenseHandler(lo)


@pytest.fixture()
def assignment_handler(lo):
    return AssignmentHandler(lo)


@pytest.fixture()
def meta_data_handler(lo):
    return MetaDataHandler(lo)


@pytest.fixture(scope="module")
def license_file(tmpdir_factory):
    test_licenses_raw = [
        {
            "lizenzcode": "UNI-{}".format(uuid.uuid4()),
            "product_id": "urn:bilo:medium:Test1",
            "lizenzanzahl": 25,
            "lizenzgeber": "UNI",
            "kaufreferenz": "2014-04-11T03:28:16 -02:00 4572022",
            "nutzungssysteme": "Antolin",
            "gueltigkeitsbeginn": "15-08-2021",
            "gueltigkeitsende": "14-08-2022",
            "gueltigkeitsdauer": "365",
            "sonderlizenz": "Lehrer",
        },
        {
            "lizenzcode": "UNI-{}".format(uuid.uuid4()),
            "product_id": "urn:bilo:medium:Test2",
            "lizenzanzahl": 1,
            "lizenzgeber": "UNI",
            "kaufreferenz": "2014-04-11T03:28:16 -02:00 4572022",
            "nutzungssysteme": "Antolin",
            "gueltigkeitsbeginn": "15-08-2021",
            "gueltigkeitsende": "14-08-2022",
            "gueltigkeitsdauer": "365",
            "sonderlizenz": "",
        },
    ]
    fn = tmpdir_factory.mktemp("data").join("license.json")
    with open(str(fn), "w") as license_fd:
        json.dump(test_licenses_raw, license_fd)
    return fn


@pytest.fixture
def ucr():
    with UCSTestConfigRegistry() as ucr_test:
        return ucr_test


@pytest.fixture
def ldap_base(ucr):
    return ucr["ldap/base"]
