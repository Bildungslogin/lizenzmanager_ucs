# -*- coding: utf-8 -*-
#
# Copyright 2021 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

from __future__ import print_function

import argparse
import configparser
import sys
from typing import List, Optional

from univention.admin.uldap import getAdminConnection
from univention.bildungslogin.handlers import MetaDataHandler
from univention.bildungslogin.media_import import (
    MediaImportError,
    MediaNotFoundError,
    get_all_media_data,
    import_single_media_data,
)


class ScriptError(Exception):
    pass


def import_all_media_data(client_id, client_secret, scope, auth_server, resource_server, product_ids):
    # type: (str, str, str, str, str, str, List[str]) -> None
    raw_media_data = get_all_media_data(
        client_id, client_secret, scope, auth_server, resource_server, product_ids
    )

    not_found_errors = []
    import_errors = []

    lo, po = getAdminConnection()
    mh = MetaDataHandler(lo)
    for raw_data in raw_media_data:
        try:
            import_single_media_data(mh, raw_data)
        except MediaImportError as exc:
            print(raw_data)
            import_errors.append(
                "%s -- %s"
                % (
                    raw_data["query"]["id"],
                    exc,
                )
            )
        except MediaNotFoundError:
            not_found_errors.append(raw_data["query"]["id"])

    err = ""
    if not_found_errors or import_errors:
        err += "Not all media data could be downloadeda:\n"
    if not_found_errors:
        err += "  The following product ids did not yield metadata:\n"
        for e in not_found_errors:
            err += "	%s\n" % (e,)
        err += "\n"
    if import_errors:
        err += "  The media data for the following product ids could not be imported:\n"
        for e in import_errors:
            err += "	%s\n" % (e,)
    if err:
        raise ScriptError(err)


def get_config(args):
    # type: (argparse.Namespace) -> dict
    config = {
        "auth_server": "https://global.telekom.com/gcp-web-api/oauth",
        "resource_server": "https://www.bildungslogin-test.de/api",
    }

    if args.config_file:
        cp = configparser.ConfigParser()
        try:
            with open(args.config_file, "r") as fd:
                cp.read_file(fd)
        except EnvironmentError as exc:
            raise ScriptError(
                "Failed to load config from --config-file (%s): %s"
                % (
                    args.config_file,
                    exc,
                )
            )
        else:
            if cp.has_option("Auth", "ClientId"):
                config["client_id"] = cp["Auth"]["ClientId"]
            if cp.has_option("Auth", "ClientSecret"):
                config["client_secret"] = cp["Auth"]["ClientSecret"]
            if cp.has_option("Auth", "Scope"):
                config["scope"] = cp["Auth"]["Scope"]
            if cp.has_option("APIEndpoint", "AuthServer"):
                config["auth_server"] = cp["APIEndpoint"]["AuthServer"]
            if cp.has_option("APIEndpoint", "ResourceServer"):
                config["resource_server"] = cp["APIEndpoint"]["ResourceServer"]

    if args.client_id:
        config["client_id"] = args.client_id
    if args.client_secret:
        config["client_secret"] = args.client_secret
    if args.scope:
        config["scope"] = args.scope
    if args.auth_server:
        config["auth_server"] = args.auth_server
    if args.resource_server:
        config["resource_server"] = args.resource_server
    has_missing_args = False
    for required_field in ["client_id", "client_secret", "scope"]:
        if not config.get(required_field):
            has_missing_args = True
            print(
                "'%s' is missing. Add it via --config-file or --%s"
                % (required_field, required_field.replace("_", "-"))
            )
    if has_missing_args:
        sys.exit(1)
    return config


def main(args):
    # type: (argparse.Namespace) -> None
    config = get_config(args)
    import_all_media_data(
        config["client_id"],
        config["client_secret"],
        config["scope"],
        config["auth_server"],
        config["resource_server"],
        args.product_ids,
    )


def parse_args(args=None):
    # type: (Optional[List[str]]) -> argparse.Namespace
    parser = argparse.ArgumentParser(description="Import media data for given product ids")
    parser.add_argument(
        "--config-file",
        help="A path to a file which contains all config options for this command. See TODO for example.",
    )
    parser.add_argument("--client-id", help="client id used for authentication against --auth-server")
    parser.add_argument(
        "--client-secret", help="client secret used for authentication against --auth-server"
    )
    parser.add_argument("--scope", help="TODO")
    parser.add_argument("--auth-server", help="")
    parser.add_argument(
        "--resource-server", help="The server from which the media data should be downloaded"
    )
    parser.add_argument(
        "product_ids",
        nargs="+",
        help="One or multiple product ids whose media data should be downloaded",
    )
    return parser.parse_args(args)


if __name__ == "__main__":
    try:
        main(parse_args())
    except ScriptError as err:
        print("Error: %s" % (err,), file=sys.stderr)