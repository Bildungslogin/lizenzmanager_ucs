# -*- coding: utf-8 -*-
import asyncio
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter

from ucsschool.apis.models import Plugin
from ucsschool.apis.plugins.auth.shared import ldap_auth
from ucsschool.apis.utils import auth_manager, LDAPCredentials, LDAPSettings, LDAPAccess

from . import __version__
from .backend import DbBackend
from .routes.v1 import users as users_routes_v1

# the name of the plugin which will also determine the name of the resource
PLUGIN_NAME: str = "bildungslogin"
# the plugins current version. Not used for anything in the ucsschool-apis app
PLUGIN_VERSION: str = __version__
# the plugins tags:
PLUGIN_TAGS: List[str] = [PLUGIN_NAME]
# the router that will be mounted as the resource under the plugins name:
router: APIRouter = APIRouter()

SETTINGS_FILE = Path(f"/etc/ucsschool/apis/{PLUGIN_NAME}/settings.json")

logger = logging.getLogger()


def setup():
    logger.info("Setup of %r with version %r...", PLUGIN_NAME, PLUGIN_VERSION)
    backend = create_db_backend()
    setup_db_backend(backend)
    auth_manager.tags[PLUGIN_NAME] = "Tag for the Bildungslogin API endpoints"


def create_db_backend() -> DbBackend:
    from .backend_udm_rest_api import UdmRestApiBackend

    ldap_settings = LDAPSettings()
    ldap_credentials = LDAPCredentials(ldap_settings)
    ldap_access = LDAPAccess(ldap_settings, ldap_credentials)

    return UdmRestApiBackend(
        ldap_auth=ldap_access,
        username=ldap_access.credentials.cn_admin,
        password=ldap_access.credentials.cn_admin_password,
        url=f"https://{ldap_access.settings.master_fqdn}/univention/udm",
        verify_ssl=False
    )


def setup_db_backend(backend: DbBackend) -> None:
    # setup() is not async, so setup_db_backend() isn't either.
    # We use the event loop created by FastAPI.
    loop = asyncio.get_running_loop()
    loop.create_task(backend.connection_test())
    logger.info("Connection using %r successfully tested.", backend.__class__.__name__)
    users_routes_v1.set_backend(backend)


router.include_router(users_routes_v1.router, prefix="/v1")

# This is the object that is referenced in the pyproject.toml as the plugin object:
BildungsloginPlugin = Plugin(PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_TAGS, router, setup)
