"""Tests for src/dispatcher.py — _wrap, DOMAIN_MAP completeness."""
import importlib

import pytest
from dispatcher import _wrap, DOMAIN_MAP


class TestWrap:
    def test_sync_handler_called_with_kwargs(self):
        calls = []

        def handler(x, y):
            calls.append((x, y))
            return "ok"

        wrapped = _wrap("test", handler)
        result = wrapped(x=1, y=2)
        assert result == "ok"
        assert calls == [(1, 2)]

    def test_wrapped_preserves_name(self):
        def my_handler():
            pass

        wrapped = _wrap("d", my_handler)
        assert wrapped.__name__ == "my_handler"

    @pytest.mark.asyncio
    async def test_async_handler_awaited(self):
        async def async_handler(x):
            return x * 2

        wrapped = _wrap("d", async_handler)
        result = await wrapped(x=5)
        assert result == 10


class TestDomainMap:
    def test_all_modules_importable(self):
        for domain, (module_path, _) in DOMAIN_MAP.items():
            mod = importlib.import_module(module_path)
            assert mod is not None, f"Could not import {module_path}"

    def test_all_handlers_exist(self):
        for domain, (module_path, actions) in DOMAIN_MAP.items():
            mod = importlib.import_module(module_path)
            for action in actions:
                assert hasattr(mod, f"handle_{action}"), f"Missing handle_{action} in {module_path}"
