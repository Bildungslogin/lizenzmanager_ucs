#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium-pytest
# -*- coding: utf-8 -*-
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
## desc: test bildungslogin UMC modules
## exposure: dangerous
## tags: [bildungslogin]
## roles: [domaincontroller_master, domaincontroller_backup, domaincontroller_slave]
## packages: [python-bildungslogin, udm-bildungslogin-encoders]

import random
from datetime import datetime, timedelta

import pytest
from selenium.common.exceptions import NoSuchElementException

import univention.testing.strings as uts
import univention.testing.ucsschool.ucs_test_school as utu
from univention.admin.syntax import iso8601Date
from univention.bildungslogin.handlers import AssignmentHandler
from univention.testing import selenium as sel
from univention.testing.selenium.utils import expand_path


def scramble_case(text):
    return "".join(random.choice((str.lower, str.upper))(t) for t in text)


@pytest.fixture
def selenium():
    with sel.UMCSeleniumTest() as s:
        yield s


@pytest.fixture
def schoolenv():
    with utu.UCSTestSchool() as _schoolenv:
        yield _schoolenv


def check_cell(selenium, cell_name, content, is_there=True):
    selenium.wait_until_standby_animation_appears_and_disappears(appear_timeout=1)
    xpath = expand_path(
        '//*[@containsClass="field-{}"]/descendant-or-self::*[contains(text(), "{}")]'.format(
            cell_name, content
        )
    )
    if is_there:
        selenium.driver.find_element_by_xpath(xpath)
    else:
        with pytest.raises(NoSuchElementException):
            selenium.driver.find_element_by_xpath(xpath)


def check_substr_search(selenium, input_name, cell_name, prop):
    selenium.enter_input(input_name, prop)
    check_cell(selenium, cell_name, prop)
    start = random.randint(1, len(prop) / 2)
    end = random.randrange(start + 1, len(prop))
    selenium.enter_input(input_name, scramble_case(prop[start:end]))
    selenium.submit_input(input_name)
    check_cell(selenium, cell_name, prop)


def select_school(selenium, ou):
    selenium.wait_for_text("Please select a school")
    selenium.enter_input_combobox("school", ou)
    selenium.click_button("Next")
    selenium.wait_until_standby_animation_appears_and_disappears()
    selenium.wait_for_text("for {}".format(ou))


def test_licenses_module_school_selection(selenium, schoolenv, create_license):
    school1_ou = uts.random_name()
    school2_ou = uts.random_name()
    while school1_ou == school2_ou:
        school2_ou = uts.random_name()
    schoolenv.create_ou(school1_ou)
    schoolenv.create_ou(school2_ou)
    try:
        license_school1 = create_license(school=school1_ou)
        license_school2 = create_license(school=school2_ou)

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school1_ou)
        check_cell(selenium, "licenseCode", license_school1.props.code)
        check_cell(selenium, "licenseCode", license_school2.props.code, False)

        selenium.click_button("Change school")

        select_school(selenium, school2_ou)
        check_cell(selenium, "licenseCode", license_school1.props.code, False)
        check_cell(selenium, "licenseCode", license_school2.props.code)
    finally:
        schoolenv.cleanup_ou(school1_ou)
        schoolenv.cleanup_ou(school2_ou)


def test_licenses_module_simple_search(selenium, schoolenv, create_license, create_metadata):

    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        metadata = create_metadata()
        license = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school_ou)

        for cell_name, content in [
            ("licenseCode", license.props.code),
            ("productId", license.props.product_id),
            ("productName", metadata.props.title),
            ("publisher", metadata.props.publisher),
            ("licenseTypeLabel", "Single license" if license.props.quantity == 1 else "Volume license"),
            ("countAquired", str(license.props.quantity)),
            ("countAssigned", str(license.props.num_assigned)),
            ("countExpired", str(license.props.num_expired)),
            ("countAvailable", str(license.props.num_available)),
            ("importDate", iso8601Date.from_datetime(license.props.delivery_date)),
        ]:
            check_cell(selenium, cell_name, content)

        check_substr_search(selenium, "pattern", "licenseCode", license.props.code)
        check_substr_search(selenium, "pattern", "productId", license.props.product_id)
        check_substr_search(selenium, "pattern", "productName", metadata.props.title)
        check_substr_search(selenium, "pattern", "publisher", metadata.props.publisher)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_licenses_module_advanced_search_time(selenium, schoolenv, create_license, create_metadata):
    def _d(date):
        return "{month}/{day}/{year}".format(month=date.month, day=date.day, year=date.year)

    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        date1 = datetime(2021, 1, 1).date()
        metadata = create_metadata()
        license = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
            delivery_date=date1,
        )

        license_before = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
            delivery_date=date1 - timedelta(days=2),
        )

        license_after = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
            delivery_date=date1 + timedelta(days=2),
        )

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_element('//*[@title="Advanced search"]')

        # test only timeFrom
        selenium.enter_input_date("timeFrom", _d(date1))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code, False)
        check_cell(selenium, "licenseCode", license_after.props.code)
        date1_before = date1 - timedelta(days=1)
        selenium.enter_input_date("timeFrom", _d(date1_before))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code, False)
        check_cell(selenium, "licenseCode", license_after.props.code)
        date1_after = date1 + timedelta(days=1)
        selenium.enter_input_date("timeFrom", _d(date1_after))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code, False)
        check_cell(selenium, "licenseCode", license_before.props.code, False)
        check_cell(selenium, "licenseCode", license_after.props.code)
        selenium.enter_input_date("timeFrom", "")

        # test only timeTo
        selenium.enter_input_date("timeTo", _d(date1))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code)
        check_cell(selenium, "licenseCode", license_after.props.code, False)
        date1_before = date1 - timedelta(days=1)
        selenium.enter_input_date("timeTo", _d(date1_before))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code, False)
        check_cell(selenium, "licenseCode", license_before.props.code)
        check_cell(selenium, "licenseCode", license_after.props.code, False)
        date1_after = date1 + timedelta(days=1)
        selenium.enter_input_date("timeTo", _d(date1_after))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code)
        check_cell(selenium, "licenseCode", license_after.props.code, False)

        # test both timeFrom and timeTo
        selenium.enter_input_date("timeFrom", _d(date1 - timedelta(days=3)))
        selenium.enter_input_date("timeTo", _d(date1 + timedelta(days=3)))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code)
        check_cell(selenium, "licenseCode", license_after.props.code)

        selenium.enter_input_date("timeFrom", _d(date1 - timedelta(days=2)))
        selenium.enter_input_date("timeTo", _d(date1 + timedelta(days=3)))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code)
        check_cell(selenium, "licenseCode", license_after.props.code)

        selenium.enter_input_date("timeFrom", _d(date1 - timedelta(days=1)))
        selenium.enter_input_date("timeTo", _d(date1 + timedelta(days=3)))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code, False)
        check_cell(selenium, "licenseCode", license_after.props.code)

        selenium.enter_input_date("timeFrom", _d(date1 - timedelta(days=0)))
        selenium.enter_input_date("timeTo", _d(date1 + timedelta(days=3)))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code, False)
        check_cell(selenium, "licenseCode", license_after.props.code)

        selenium.enter_input_date("timeFrom", _d(date1 - timedelta(days=3)))
        selenium.enter_input_date("timeTo", _d(date1 + timedelta(days=2)))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code)
        check_cell(selenium, "licenseCode", license_after.props.code)

        selenium.enter_input_date("timeFrom", _d(date1 - timedelta(days=3)))
        selenium.enter_input_date("timeTo", _d(date1 + timedelta(days=1)))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code)
        check_cell(selenium, "licenseCode", license_after.props.code, False)

        selenium.enter_input_date("timeFrom", _d(date1 - timedelta(days=3)))
        selenium.enter_input_date("timeTo", _d(date1 + timedelta(days=0)))
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_before.props.code)
        check_cell(selenium, "licenseCode", license_after.props.code, False)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_licenses_module_advanced_search_ignored_for_display(
    selenium, schoolenv, create_license, create_metadata
):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        metadata = create_metadata()
        license_ignored = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
            ignored=True,
        )
        license_not_ignored_with_quantity = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
            ignored=False,
            quantity=2,
        )
        license_not_ignored_without_quantity = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
            ignored=False,
            validity_end_date=datetime.now().date() - timedelta(days=1),
        )

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_element('//*[@title="Advanced search"]')
        check_cell(selenium, "licenseCode", license_ignored.props.code)
        check_cell(selenium, "licenseCode", license_not_ignored_with_quantity.props.code)
        check_cell(selenium, "licenseCode", license_not_ignored_without_quantity.props.code)
        selenium.driver.find_element_by_name("onlyAvailableLicenses").click()
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license_ignored.props.code, False)
        check_cell(selenium, "licenseCode", license_not_ignored_with_quantity.props.code)
        check_cell(selenium, "licenseCode", license_not_ignored_without_quantity.props.code, False)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_licenses_module_advanced_search_publisher(selenium, schoolenv, create_license, create_metadata):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        metadata = create_metadata()
        metadata2 = create_metadata()
        license = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )
        license2 = create_license(
            school=school_ou,
            product_id=metadata2.props.product_id,
        )

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_element('//*[@title="Advanced search"]')
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license2.props.code)
        selenium.enter_input_combobox("publisher", metadata.props.publisher)
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license2.props.code, False)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_licenses_module_advanced_search_license_type(
    selenium, schoolenv, create_license, create_metadata
):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        metadata = create_metadata()
        license_single = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
            quantity=1,
        )
        license_volume = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
            quantity=2,
        )

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_element('//*[@title="Advanced search"]')
        check_cell(selenium, "licenseCode", license_single.props.code)
        check_cell(selenium, "licenseCode", license_volume.props.code)
        selenium.enter_input_combobox("licenseType", "Single license")
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license_single.props.code)
        check_cell(selenium, "licenseCode", license_volume.props.code, False)
        selenium.enter_input_combobox("licenseType", "Volume license")
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license_single.props.code, False)
        check_cell(selenium, "licenseCode", license_volume.props.code)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_licenses_module_advanced_search_user_ident(
    selenium, schoolenv, create_license, create_metadata, lo
):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    username, _ = schoolenv.create_student(school_ou)
    try:
        metadata = create_metadata()
        license = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )
        ah = AssignmentHandler(lo)
        ah.assign_users_to_licenses([license.props.code], [username])

        license_without_user = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_element('//*[@title="Advanced search"]')
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_without_user.props.code)
        selenium.enter_input("userPattern", username)
        selenium.submit_input("licenseCode")
        check_cell(selenium, "licenseCode", license.props.code)
        check_cell(selenium, "licenseCode", license_without_user.props.code, False)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_licenses_module_advanced_search(selenium, schoolenv, create_license, create_metadata):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    username, _ = schoolenv.create_student(school_ou)
    try:
        metadata = create_metadata()
        license = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_element('//*[@title="Advanced search"]')
        check_cell(selenium, "licenseCode", license.props.code)
        check_substr_search(selenium, "productId", "productId", license.props.product_id)
        check_substr_search(selenium, "product", "productName", metadata.props.title)
        check_substr_search(selenium, "licenseCode", "licenseCode", license.props.code)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_licenses_module_save_ignore(selenium, schoolenv, create_license, create_metadata):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        metadata = create_metadata()
        license = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_grid_entry(license.props.code)
        selenium.wait_until_standby_animation_appears_and_disappears()
        checkbox = selenium.driver.find_element_by_xpath(
            '//*[contains(text(), "Ignore")]/following-sibling::*//input'
        )
        assert checkbox.get_attribute("aria-checked") == "false"
        assert license.props.ignored is False
        checkbox.click()
        selenium.click_button("Save")
        selenium.wait_until_standby_animation_appears_and_disappears()
        selenium.click_grid_entry(license.props.code)
        selenium.wait_until_standby_animation_appears_and_disappears()
        checkbox = selenium.driver.find_element_by_xpath(
            '//*[contains(text(), "Ignore")]/following-sibling::*//input'
        )
        assert checkbox.get_attribute("aria-checked") == "true"
        license.reload()
        assert license.props.ignored is True
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_licenses_module_remove_license(selenium, schoolenv, create_license, create_metadata, lo):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    username, _ = schoolenv.create_student(school_ou)
    try:
        metadata = create_metadata()
        license = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )
        ah = AssignmentHandler(lo)
        ah.assign_users_to_licenses([license.props.code], [username])

        selenium.do_login()
        selenium.open_module("View media licenses", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_grid_entry(license.props.code)
        check_cell(selenium, "username", username)
        selenium.click_grid_entry(username)
        selenium.click_button("Remove assignment")
        selenium.wait_until_standby_animation_appears_and_disappears()
        check_cell(selenium, "username", username, False)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_products_module_school_selection(selenium, schoolenv, create_license, create_metadata):
    school1_ou = uts.random_name()
    school2_ou = uts.random_name()
    while school1_ou == school2_ou:
        school2_ou = uts.random_name()
    schoolenv.create_ou(school1_ou)
    schoolenv.create_ou(school2_ou)
    try:
        product_school1 = create_metadata()
        product_school2 = create_metadata()
        create_license(school=school1_ou, product_id=product_school1.props.product_id)
        create_license(school=school2_ou, product_id=product_school2.props.product_id)

        selenium.do_login()
        selenium.open_module("Licensed media", do_reload=False)

        select_school(selenium, school1_ou)
        check_cell(selenium, "productId", product_school1.props.product_id)
        check_cell(selenium, "productId", product_school2.props.product_id, False)

        selenium.click_button("Change school")

        select_school(selenium, school2_ou)
        check_cell(selenium, "productId", product_school1.props.product_id, False)
        check_cell(selenium, "productId", product_school2.props.product_id)
    finally:
        schoolenv.cleanup_ou(school1_ou)
        schoolenv.cleanup_ou(school2_ou)


def test_products_module_search(selenium, schoolenv, create_license, create_metadata):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        metadata = create_metadata()
        license1 = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )
        license2 = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )
        licenses = [license1, license2]
        sum_quantity = sum(lic_udm.props.quantity for lic_udm in licenses)
        sum_num_assigned = sum(lic_udm.props.num_assigned for lic_udm in licenses)
        sum_num_expired = sum(lic_udm.props.num_expired for lic_udm in licenses)
        sum_num_available = sum(lic_udm.props.num_available for lic_udm in licenses)

        selenium.do_login()
        selenium.open_module("Licensed media", do_reload=False)

        select_school(selenium, school_ou)

        for cell_name, content in [
            ("productId", metadata.props.product_id),
            ("title", metadata.props.title),
            ("publisher", metadata.props.publisher),
            ("publisher", metadata.props.publisher),
            ("countAquired", sum_quantity),
            ("countAssigned", sum_num_assigned),
            ("countExpired", sum_num_expired),
            ("countAvailable", sum_num_available),
            #  ('latestDeliveryDate',),
        ]:
            check_cell(selenium, cell_name, content)

        check_substr_search(selenium, "pattern", "productId", metadata.props.product_id)
        check_substr_search(selenium, "pattern", "title", metadata.props.title)
        check_substr_search(selenium, "pattern", "publisher", metadata.props.publisher)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_products_module_detail_page(selenium, schoolenv, create_license, create_metadata):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        metadata = create_metadata()
        license1 = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )
        license2 = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )

        selenium.do_login()
        selenium.open_module("Licensed media", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_grid_entry(metadata.props.product_id)
        selenium.wait_until_standby_animation_appears_and_disappears()
        check_cell(selenium, "licenseCode", license1.props.code)
        check_cell(selenium, "licenseCode", license2.props.code)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_assignment_module_user_search(selenium, schoolenv, create_license, create_metadata):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        username, userdn = schoolenv.create_student(school_ou)
        username2, _ = schoolenv.create_student(school_ou)
        classname, classdn = schoolenv.create_school_class(school_ou, users=[userdn])
        classname_combobox = classname[len(school_ou) + 1 :]
        groupname, groupdn = schoolenv.create_workgroup(school_ou, users=[userdn])
        groupname_combobox = groupname[len(school_ou) + 1 :]

        selenium.do_login()
        selenium.open_module("Assign media licenses", do_reload=False)

        select_school(selenium, school_ou)

        check_cell(selenium, "username", username)
        check_cell(selenium, "username", username2)

        selenium.enter_input_combobox("class", classname_combobox)
        selenium.submit_input("pattern")
        check_cell(selenium, "username", username)
        check_cell(selenium, "username", username2, False)
        start = random.randint(1, len(classname_combobox) / 2)
        end = random.randrange(start + 1, len(classname_combobox))
        selenium.enter_input_combobox(
            "class", scramble_case(classname_combobox[start:end]), with_click=False
        )
        selenium.submit_input("pattern")
        check_cell(selenium, "username", username)
        check_cell(selenium, "username", username2, False)
        selenium.enter_input_combobox("class", "", with_click=False)

        selenium.enter_input_combobox("workgroup", groupname_combobox)
        selenium.submit_input("pattern")
        check_cell(selenium, "username", username)
        check_cell(selenium, "username", username2, False)
        selenium.enter_input_combobox("workgroup", "", with_click=False)

        check_substr_search(selenium, "pattern", "username", username)
        check_cell(selenium, "username", username2, False)
    finally:
        schoolenv.cleanup_ou(school_ou)


def test_assignment_module_assignment(selenium, schoolenv, create_license, create_metadata):
    school_ou = uts.random_name()
    schoolenv.create_ou(school_ou)
    try:
        metadata = create_metadata()
        metadata2 = create_metadata()
        license1 = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
            quantity=2,
        )
        license2 = create_license(
            school=school_ou,
            product_id=metadata.props.product_id,
        )
        license3 = create_license(
            school=school_ou,
            product_id=metadata2.props.product_id,
        )
        license4 = create_license(
            school=school_ou,
            product_id=metadata2.props.product_id,
        )
        username, _ = schoolenv.create_student(school_ou)
        username2, _ = schoolenv.create_student(school_ou)

        selenium.do_login()
        selenium.open_module("Assign media licenses", do_reload=False)

        select_school(selenium, school_ou)

        selenium.click_checkbox_of_grid_entry(username)
        selenium.click_checkbox_of_grid_entry(username2)

        selenium.click_button("Assign licenses")

        check_cell(selenium, "productId", metadata.props.product_id)
        check_cell(selenium, "productId", metadata2.props.product_id)

        selenium.click_grid_entry(metadata.props.product_id)

        check_cell(selenium, "licenseCode", license1.props.code)
        check_cell(selenium, "licenseCode", license2.props.code)
        check_cell(selenium, "licenseCode", license3.props.code, False)
        check_cell(selenium, "licenseCode", license4.props.code, False)

        selenium.click_checkbox_of_grid_entry(license1.props.code)

        selenium.click_button("Assign licenses")

        selenium.wait_for_text("Licenses were successfully assigned to all 2 selected users.")
        selenium.click_button("Ok")
        selenium.click_button("Change user selection")
        selenium.click_button("Close")

        selenium.open_module("View media licenses", do_reload=False)
        select_school(selenium, school_ou)
        selenium.wait_until_standby_animation_appears_and_disappears()
        selenium.click_grid_entry(license1.props.code)
        check_cell(selenium, "username", username)
        check_cell(selenium, "username", username2)
    finally:
        schoolenv.cleanup_ou(school_ou)
