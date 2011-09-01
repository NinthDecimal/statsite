"""
Contains tests for utility functions.
"""

import pytest
from tests.base import TestBase

import statsite.util

class TestMerge(TestBase):
    def test_merge(self):
        """
        Tests that dictionary deep merging works properly.
        """
        a = {'a': 1, 'b': {1: 1, 2: 2}, 'd': 6}
        b = {'c': 3, 'b': {2: 7}, 'd': {'z': [1, 2, 3]}}
        result = statsite.util.deep_merge(a, b)
        expected = {'a': 1, 'b': {1: 1, 2: 7}, 'c': 3, 'd': {'z': [1, 2, 3]}}

        assert expected == result

    def test_non_destructive(self):
        """
        Tests that the merging is non-destructive for the source
        dictionary.
        """
        a = {'a': { 'b': False } }
        b = {'a': { 'b': True } }
        result = statsite.util.deep_merge(a, b)

        # Assert that it was not changed
        assert { 'a': { 'b': False } } == a

class TestResolveClassString(TestBase):
    def test_resolve_no_module(self):
        """
        Tests that resolving without a module fails.
        """
        with pytest.raises(ValueError):
            statsite.util.resolve_class_string("Foo")

    def test_resolve_no_class(self):
        """
        Tests that resolving without a class fails.
        """
        with pytest.raises(ValueError):
            statsite.util.resolve_class_string("foo.")

    def test_resolve_nonexistent_class(self):
        """
        Tests that resolving a class which doesn't exist
        fails.
        """
        with pytest.raises(ImportError):
            statsite.util.resolve_class_string("os.getloginn")

    def test_resolve_correct_class(self):
        """
        Tests that resolving an item with valid parameters
        results in a valid result.
        """
        result = statsite.util.resolve_class_string("os.getlogin")
        assert callable(result)
