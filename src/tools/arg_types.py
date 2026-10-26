"""Annotated argument types for handler signatures.

FastMCP builds each tool's pydantic argument model from the handler signature,
so these validators run on the MCP path and their `format` lands in the tool's
JSON schema. The `mac` CLI does not go through pydantic: cli-graph's
tools/gen_groups.py reads the `format` below and gives the argparse argument
a matching type, so both paths reject the same values before the handler runs.
"""
import re
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, Field

DATE_FORMAT = "date"
DATETIME_FORMAT = "date-or-datetime"
_YMD = re.compile(r"\d{4}-\d{2}-\d{2}")


def check_date(value: str) -> str:
    # fromisoformat alone also takes 20261027 and 2026-W44-2
    if not _YMD.fullmatch(value):
        raise ValueError(f"not a YYYY-MM-DD date: {value!r}")
    try:
        date.fromisoformat(value)
    except ValueError as exc:  # pydantic reports it as a validation error
        raise ValueError(f"not a valid YYYY-MM-DD date: {value!r} ({exc})") from None
    return value


def check_datetime(value: str) -> str:
    """A YYYY-MM-DD date or an ISO-8601 date-time joined with 'T'.

    The handlers treat a value without 'T' as a bare date (calendar._iso
    appends T00:00:00Z), so "2026-10-27 15:00" would be misread, not rejected.
    """
    if len(value) == 10:
        return check_date(value)
    if value[10:11] == " ":
        raise ValueError(f"join date and time with 'T', e.g. 2026-10-27T15:00:00: {value!r}")
    if value[10:11] != "T":
        raise ValueError(f"not a YYYY-MM-DD date or ISO-8601 date-time: {value!r}")
    check_date(value[:10])
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"not a valid ISO-8601 date-time: {value!r} ({exc})") from None
    return value


IsoDate = Annotated[str, AfterValidator(check_date), Field(
    json_schema_extra={"format": DATE_FORMAT},
    description="YYYY-MM-DD")]

IsoDateTime = Annotated[str, AfterValidator(check_datetime), Field(
    json_schema_extra={"format": DATETIME_FORMAT},
    description="YYYY-MM-DD or ISO-8601 date-time, e.g. 2026-10-27T15:00:00")]


def arg_format(annotation) -> str | None:
    """The format of an IsoDate / IsoDateTime annotation, else None. The caller unwraps `| None`."""
    for meta in getattr(annotation, "__metadata__", ()):
        extra = getattr(meta, "json_schema_extra", None)
        if isinstance(extra, dict) and "format" in extra:
            return extra["format"]
    return None
