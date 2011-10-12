"""
Contains tests for the key/value metric class.
"""

import time
from statsite.metrics import KeyValue

class TestKeyValue(object):
    def test_fold_basic(self):
        """Tests folding over a normal metric returns the key/value
        using the flag as the timestamp."""
        metrics = [KeyValue("k", 27, 123456)]
        assert [("kv.k", 27, 123456)] == KeyValue.fold(metrics, 0)

    def test_defaults_flag_to_now(self, monkeypatch):
        """Tests that the flag is defaulted to the time of instantiation
        if no flag is given."""
        now = 27
        monkeypatch.setattr(time, 'time', lambda: now)
        metrics = [KeyValue("k", 27)]
        assert [("kv.k", 27, now)] == KeyValue.fold(metrics, 0)
