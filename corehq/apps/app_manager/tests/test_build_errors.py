import json
from django.test import TestCase
import os
from corehq.apps.app_manager.models import Application


class BuildErrorsTest(TestCase):
    def test_subcase_errors(self):
        with open(os.path.join(os.path.dirname(__file__), 'data', 'subcase-details.json')) as f:
            source = json.load(f)

        app = Application.wrap(source)
        errors = app.validate_app()
        update_path_error = {
            'type': 'path error',
            'path': '/data/parent_age',
            'form_type': 'module_form',
            'module': {'name': {'en': "Parent"}, 'id': 0},
            'form': {'id': 0, 'name': {'en': "Register"}},
        }
        subcase_path_error = {
            'type': 'path error',
            'path': '/data/child_age',
            'form_type': 'module_form',
            'module': {'name': {'en': "Parent"}, 'id': 0},
            'form': {'id': 0, 'name': {'en': "Register"}},
        }
        self.assertIn(update_path_error, errors)
        self.assertIn(subcase_path_error, errors)

        form = app.get_module(0).get_form(0)
        errors = form.validate_for_build()
        self.assertIn(update_path_error, errors)
        self.assertIn(subcase_path_error, errors)

        with open(os.path.join(os.path.dirname(__file__), 'data', 'subcase-details2.json')) as f:
            source2 = json.load(f)

        app2 = Application.wrap(source2)
        errors2 = app2.validate_app()
        print "\n\nHERE BE ERRORS"
        print errors
        print errors2
        case_type_error = {'message': u'Case type (nonexistent) for form (Register) does not exist', 'type': 'error'}
        self.assertIn(case_type_error, errors2)

