# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

import logging
from importlib import import_module

import requests
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.validation import BaseDatabaseValidation
from rest_models.backend.connexion import ApiConnexion

from rest_models.backend.exceptions import FakeDatabaseDbAPI2
from .client import DatabaseClient
from .creation import DatabaseCreation
from .features import DatabaseFeatures
from .introspection import DatabaseIntrospection
from .operations import DatabaseOperations
from .schema import DatabaseSchemaEditor

logger = logging.getLogger(__name__)


def import_class(path):
    """
    import a component of a module by his path.
    ie module.submodule.ClassName return the class ClassName
    don't work for nested item. the class must be on the root of the module
    :param str path: the path to import
    :return: the class
    :rtype: type
    """
    lpath = path.split(".")
    module = import_module(".".join(lpath[:-1]))
    obj = getattr(module, lpath[-1])
    return obj


class FakeCursor(object):
    def execute(self, sql):
        raise NotImplementedError("this is not a SQL database, so no cursor is available")

    def close(self):
        pass


class DatabaseWrapper(BaseDatabaseWrapper):

    Database = FakeDatabaseDbAPI2
    vendor = 'rest_api'
    SchemaEditorClass = DatabaseSchemaEditor

    def __init__(self, *args, **kwargs):
        self.connection = None  # type: ApiConnexion

        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = BaseDatabaseValidation(self)

    def get_connection_params(self):
        authpath = self.settings_dict.get('AUTH', 'rest_models.backend.auth.BasicAuth')
        auth = import_class(authpath)(self.settings_dict)

        params = {
            'url': self.settings_dict['NAME'],
            'auth': auth,
        }
        return params

    def get_new_connection(self, conn_params):
        return ApiConnexion(**conn_params)

    def init_connection_state(self):
        c = self.connection
        self.autocommit = True
        r = c.head('', timeout=4)
        if r.status_code == 403:
            raise FakeDatabaseDbAPI2.OperationalError("bad credentials for database %s on %s" %
                                                      (self.alias, self.settings_dict['NAME']))

    def create_cursor(self):
        return FakeCursor()

    def close(self):
        # do nothing
        pass

    def _start_transaction_under_autocommit(self):
        pass

    def is_usable(self):
        c = self.connection  # type: requests.Session
        try:
            c.head('', timeout=4)
            return True
        except requests.RequestException:
            return False

    def _set_autocommit(self, autocommit):
        pass