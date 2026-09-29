"""list_events results are cached briefly; writes and errors never leave stale entries (task adf83977)."""
import pytest

from src.tools import calendar as cal

EV = [{"title": "x"}]


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    cal._list_cache.clear()
    calls = []

    def fake(op, **kw):
        calls.append(op)
        return {"list_events": EV, "add_event": "ok", "delete_event": "ok"}[op]
    monkeypatch.setattr(cal, "_run_isolated", fake)
    return calls


def test_second_read_is_served_from_cache(_fresh):
    cal.handle_list_events("2026-10-01", "2026-10-02", "market-watch")
    cal.handle_list_events("2026-10-01", "2026-10-02", "market-watch")
    assert _fresh == ["list_events"]


def test_different_key_is_a_miss(_fresh):
    cal.handle_list_events("2026-10-01", "2026-10-02", "market-watch")
    cal.handle_list_events("2026-10-01", "2026-10-03", "market-watch")
    assert _fresh == ["list_events", "list_events"]


def test_ttl_expiry_refetches(_fresh, monkeypatch):
    t = [1000.0]
    monkeypatch.setattr(cal.time, "monotonic", lambda: t[0])
    cal.handle_list_events("a", "b")
    t[0] += cal._CACHE_TTL_S + 1
    cal.handle_list_events("a", "b")
    assert _fresh == ["list_events", "list_events"]


@pytest.mark.parametrize("write", [lambda: cal.handle_add_event("t", "2026-10-01"),
                                   lambda: cal.handle_delete_event("t")])
def test_writes_clear_cache(_fresh, write):
    cal.handle_list_events("a", "b")
    write()
    cal.handle_list_events("a", "b")
    assert _fresh.count("list_events") == 2


def test_failed_write_still_clears_cache(monkeypatch):
    cal.handle_list_events("a", "b")
    monkeypatch.setattr(cal, "_run_isolated", lambda op, **kw: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        cal.handle_add_event("t", "2026-10-01")
    assert cal._list_cache == {}


def test_empty_result_is_not_cached(monkeypatch):
    seen = []
    monkeypatch.setattr(cal, "_run_isolated", lambda op, **kw: seen.append(op) or [])
    cal.handle_list_events("a", "b")
    cal.handle_list_events("a", "b")
    assert seen == ["list_events", "list_events"]


def test_error_is_not_cached(monkeypatch):
    def boom(op, **kw):
        raise ValueError("Calendar not found: q")
    monkeypatch.setattr(cal, "_run_isolated", boom)
    with pytest.raises(ValueError):
        cal.handle_list_events("a", "b", "q")
    assert cal._list_cache == {}


def test_caller_mutation_does_not_corrupt_cache(_fresh):
    first = cal.handle_list_events("a", "b")
    first[0]["title"] = "mutated"
    assert cal.handle_list_events("a", "b")[0]["title"] == "x"
