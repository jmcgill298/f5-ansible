# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_ssl_certificate import ArgumentSpec
    from library.bigip_ssl_certificate import ApiParameters
    from library.bigip_ssl_certificate import ModuleParameters
    from library.bigip_ssl_certificate import ModuleManager
    from library.bigip_ssl_certificate import HAS_F5SDK
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_ssl_certificate import ArgumentSpec
        from ansible.modules.network.f5.bigip_ssl_certificate import ApiParameters
        from ansible.modules.network.f5.bigip_ssl_certificate import ModuleParameters
        from ansible.modules.network.f5.bigip_ssl_certificate import ModuleManager
        from ansible.modules.network.f5.bigip_ssl_certificate import HAS_F5SDK
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters_cert(self):
        cert_content = load_fixture('create_insecure_cert1.crt')
        args = dict(
            content=cert_content,
            name="cert1",
            partition="Common",
            state="present",
            password='password',
            server='localhost',
            user='admin'
        )
        p = ModuleParameters(args)
        assert p.name == 'cert1'
        assert p.filename == 'cert1.crt'
        assert 'Signature Algorithm' in p.content
        assert '-----BEGIN CERTIFICATE-----' in p.content
        assert '-----END CERTIFICATE-----' in p.content
        assert p.checksum == '1e55aa57ee166a380e756b5aa4a835c5849490fe'
        assert p.state == 'present'
        assert p.user == 'admin'
        assert p.server == 'localhost'
        assert p.password == 'password'
        assert p.partition == 'Common'

    def test_module_issuer_cert_key(self):
        args = dict(
            issuer_cert='foo',
            partition="Common",
        )
        p = ModuleParameters(args)
        assert p.issuer_cert == '/Common/foo.crt'

    def test_api_issuer_cert_key(self):
        args = load_fixture('load_sys_file_ssl_cert_with_issuer_cert.json')
        p = ApiParameters(args)
        assert p.issuer_cert == '/Common/intermediate.crt'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestCertificateManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_import_certificate_and_key_no_key_passphrase(self, *args):
        set_module_args(dict(
            name='foo',
            content=load_fixture('cert1.crt'),
            state='present',
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_import_certificate_chain(self, *args):
        set_module_args(dict(
            name='foo',
            content=load_fixture('chain1.crt'),
            state='present',
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
