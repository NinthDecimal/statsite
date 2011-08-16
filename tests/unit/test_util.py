"""
Contains tests for utility functions.
"""

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
