"""Tests for src/tools/arg_types.py — date arguments rejected on the MCP path before a handler runs."""
import functools

import pytest
from mcp.server.fastmcp.utilities.func_metadata import func_metadata
from pydantic import ValidationError

from dispatcher import _wrap, resolve
from tools.arg_types import DATE_FORMAT, DATETIME_FORMAT, arg_format, check_date, check_datetime

# (domain, action, required args, date parameter, its format)
DATE_PARAMS = [
    ("calendar", "list_events", {"start_date": "2026-10-01", "end_date": "2026-10-31"}, "start_date", DATETIME_FORMAT),
    ("calendar", "add_event", {"title": "t", "start_date": "2026-10-27"}, "end_date", DATETIME_FORMAT),
    ("calendar", "get_events_by_date", {}, "date", DATE_FORMAT),
    ("calendar", "get_upcoming_events", {}, "from_date", DATE_FORMAT),
    ("calendar", "get_noise_summary", {}, "date", DATE_FORMAT),
    ("reminders", "create", {"title": "t"}, "due_date", DATETIME_FORMAT),
    ("reminders", "update", {"id": "x"}, "due_date", DATETIME_FORMAT),
]


@functools.cache
def _arg_model(domain, action):
    return func_metadata(_wrap(domain, action, resolve(domain, action))).arg_model


@pytest.mark.parametrize("domain,action,base,param,fmt", DATE_PARAMS)
def test_schema_carries_the_format(domain, action, base, param, fmt):
    schema = _arg_model(domain, action).model_json_schema()["properties"][param]
    assert [s["format"] for s in schema.get("anyOf", [schema]) if "format" in s] == [fmt]


@pytest.mark.parametrize("domain,action,base,param,fmt", DATE_PARAMS)
def test_bad_date_fails_validation(domain, action, base, param, fmt):
    """Shows the annotation is wired up; test_check_datetime covers the bad-value range."""
    with pytest.raises(ValidationError):
        _arg_model(domain, action).model_validate({**base, param: "2026-02-30"})


@pytest.mark.parametrize("domain,action,base,param,fmt", DATE_PARAMS)
def test_good_dates_pass_unchanged(domain, action, base, param, fmt):
    good = "2026-10-27" if fmt == DATE_FORMAT else "2026-10-27T09:00:00"
    args = _arg_model(domain, action).model_validate({**base, param: good})
    assert getattr(args, param) == good


@pytest.mark.parametrize("value,ok", [
    ("2026-10-27", True), ("2026-10-27T09:00", True), ("2026-10-27T09:00:00Z", True),
    ("2026-10-27 09:00", False), ("2026-10-27T25:00", False), ("2026-W44-2", False),
])
def test_check_datetime(value, ok):
    if ok:
        assert check_datetime(value) == value
    else:
        with pytest.raises(ValueError):
            check_datetime(value)


def test_check_date_rejects_a_datetime():
    with pytest.raises(ValueError):
        check_date("2026-10-27T09:00")


def test_arg_format():
    from tools.arg_types import IsoDate, IsoDateTime
    assert arg_format(IsoDate) == DATE_FORMAT
    assert arg_format(IsoDateTime) == DATETIME_FORMAT
    assert arg_format(str) is None
