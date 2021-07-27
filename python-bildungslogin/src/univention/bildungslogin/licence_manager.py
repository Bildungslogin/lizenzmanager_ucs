# WIP, not tests (!)


from time import time
from uuid import uuid4

from ldap.filter import filter_format
from typing import List
from univention.udm import UDM
from univention.udm.exceptions import CreateError

from license import License
from utils import Status, Assignment


class LicenseAssignmentHandler:
    def __init__(self, lo):
        self.lo = lo
        udm = UDM(lo).version(1)
        self._licenses_mod = udm.get("vbm/licenses")
        self._assignments_mod = udm.get("vbm/assignments")
        self._users_mod = udm.get("users/user")

    def get_all(self, filter_s=None):  # type: (str) -> List[Assignment]
        assignments = self._assignments_mod.search(filter_s=filter_s)
        return [Assignment.from_udm_obj(a) for a in assignments]

    def get_all_assignments_for_user(self, username):  # type: (str) -> List[Assignment]
        filter_s = filter_format("(vbmAssignmentAssignee=%s)", [username])
        assignments = self._assignments_mod.search(filter_s)
        return [Assignment.from_udm_obj(a) for a in assignments]

    def get_assignments_for_product_id_for_user(
        self, username, product_id
    ):  # type: (str, str) -> List[Assignment]
        # do we need this?
        filter_s = filter_format("(vbmProductId=%s)", [product_id])
        udm_licenses = self._licenses_mod.search(filter_s)
        assignments = []
        for udm_license in udm_licenses:
            filter_s = filter_format("(vbmAssignmentAssignee=%s)", [username])
            udm_assignment = self._assignments_mod.search(
                base=udm_license.dn, filter_s=filter_s
            )
            assignments.append(Assignment.from_udm_obj(udm_assignment))
        return [Assignment.from_udm_obj(a) for a in assignments]

    def assign_to_license(self, license, username):  # type: (License, str) -> bool
        filter_s = filter_format("(vbmLicenseCode=%s)", [license])
        udm_license = [o for o in self._licenses_mod.search(filter_s)][0]
        # can i do this better? i only have the uid...
        filter_s = filter_format("(uid=%s)", [username])
        users = [u for u in self._users_mod.search(filter_s)]
        if not users:
            raise ValueError("Not user with username {}".format(username))
        if udm_license.props.vbmLicenseSchool not in users[0].props.school:
            raise ValueError(
                "License can't be assigned to user in school {}".format(
                    users[0].props.school
                )
            )

        try:
            assignment = self._assignments_mod.new()
            assignment.props.cn = uuid4()
            assignment.position = udm_license.dn
            assignment.props.vbmAssignmentAssignee = username
            assignment.props.vbmAssignmentTimeOfAssignment = time()  # todo
            assignment.props.vbmAssignmentStatus = Status.ASSIGNED
            assignment.save()
        except CreateError as e:
            print(
                "Error while assigning {} to {}: {}".format(
                    license.license_code, username, e
                )
            )
            return False
        return True

    def assign_users_to_licenses(
        self, licenses, usernames
    ):  # type: (List[str], List[str]) -> None
        """Eine Lizenz kann nur zugewiesen werden,
        wenn die Menge an Lizenzen ausreicht, um allen Benutzern eine Lizenz zuzuweisen.
        """
        if len(licenses) >= len(usernames):
            raise ValueError(
                "The number of licenses must be >= the users the license codes!"
            )
        for username, license in zip(usernames, licenses):
            # todo ...
            self.assign_to_license(license, username)

    def change_license_status(
        self, license, username, status
    ):  # type: (str, str, str) -> bool
        # can change from available to assigned if a username is provided
        # or from available to provisioned
        # todo matrix
        # username has to be present except if license expired (or valid-date)
        """search for license with license id and user with username and change the status
        -> if a user has more than one license, do we simply change the first? what if that's
        not possible?
        -> we take any license
        """
        if status not in [s.value for s in Status]:
            raise ValueError("Invalid status {}:".format(status))
        filter_s = filter_format("(vbmLicenseCode)", [license])
        try:
            license = [o for o in self._licenses_mod.search(filter_s)][0]
        except KeyError:
            print("No license with code {} was found!".format(license))
            return False
        filter_s = filter_format("(vbmAssignmentAssignee)", [username])
        try:
            assignment = [
                a
                for a in self._assignments_mod.search(
                    base=license.dn, filter_s=filter_s
                )
            ][0]
        except KeyError:
            print("No assignment {} -> {} was found!".format(license, username))
            return False
        assignment.props.vbmAssignmentStatus = status
        assignment.save()
        return True
