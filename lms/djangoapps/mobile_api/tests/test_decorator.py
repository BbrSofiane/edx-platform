# -*- coding: utf-8 -*-
"""
Tests for mobile API utilities.
"""


import ddt
from django.test import TestCase

from ..decorators import mobile_course_access, mobile_view


@ddt.ddt
class TestMobileAPIDecorators(TestCase):
    """
    Basic tests for mobile api decorators to ensure they retain the docstrings.
    """

    @ddt.data(mobile_view, mobile_course_access)
    def test_function_decorator(self, decorator):
        @decorator()
        def decorated_func():
            """
            Test docstring of decorated function.
            """
            pass  # lint-amnesty, pylint: disable=unnecessary-pass

        self.assertIn("Test docstring of decorated function.", decorated_func.__doc__)
        self.assertEqual(decorated_func.__name__, "decorated_func")
        self.assertTrue(decorated_func.__module__.endswith("test_decorator"))
