"""Transparent timing wrappers around the Neo4j driver.

Every query that flows through `get_driver()` is timed end-to-end (from
`run()` through result consumption) and emitted as a structured JSON
line to a dedicated logger. Aggregate the resulting JSONL with
`tools/neo4j_query_stats.py` to find slow endpoints.

The wrappers intercept three call shapes:
  - `session.run(cypher, **params).data()/.single()/iter`
  - `session.execute_read(lambda tx: tx.run(...).data())`
  - `session.execute_write(...)` (same shape)

Wrapping is transparent: every method/attribute not explicitly handled
falls through via `__getattr__`, so callers see no behavior change.
"""

import hashlib
import json
import logging
import os
import time
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Attribution: each query records the request endpoint that triggered
# it. FastAPI middleware sets this; pipeline/CLI usage leaves it empty
# (which itself is a useful signal — "no request_ctx" means
# ingestion-time work).
_request_ctx: ContextVar[str] = ContextVar("neo4j_request_ctx", default="")


def set_request_context(name: str) -> None:
    _request_ctx.set(name)


# Slow-query thresholds (ms). Tuned so steady-state read endpoints
# don't spam WARN, but anything genuinely sluggish is visible at a
# glance in the main app log even without aggregating the JSONL.
_SLOW_WARN_MS = 100.0
_SLOW_ERROR_MS = 500.0


def _log_path() -> Path:
    override = os.environ.get("NEO4J_QUERY_LOG")
    if override:
        return Path(override)
    backend_dir = Path(__file__).resolve().parent.parent
    return backend_dir / "logs" / "neo4j_queries.jsonl"


def _build_query_logger() -> logging.Logger:
    log = logging.getLogger("neo4j.queries")
    log.setLevel(logging.INFO)
    log.propagate = False
    if log.handlers:
        return log

    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # 50 MB per file, keep 5 — bounds disk usage at ~250 MB even if
    # we forget about it.
    handler = RotatingFileHandler(path, maxBytes=50 * 1024 * 1024, backupCount=5)
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
    return log


_query_logger = _build_query_logger()
_app_logger = logging.getLogger("neo4j.timing")


def _normalize_cypher(cypher: str) -> str:
    return " ".join(cypher.split())


def _fingerprint(cypher: str) -> str:
    """Stable 12-char hash of normalized cypher for grouping in stats."""
    return hashlib.sha1(_normalize_cypher(cypher).encode()).hexdigest()[:12]


def _emit(
    cypher: str,
    params: dict,
    duration_ms: float,
    *,
    consumer: str,
    result_count: int | None,
    kind: str = "query",
) -> None:
    normalized = _normalize_cypher(cypher)
    event = {
        "ts": time.time(),
        "kind": kind,
        "fingerprint": _fingerprint(cypher),
        "duration_ms": round(duration_ms, 2),
        "consumer": consumer,
        "result_count": result_count,
        "request_ctx": _request_ctx.get(),
        "param_keys": sorted(params.keys()) if params else [],
        "cypher": normalized[:1000],
    }
    _query_logger.info(json.dumps(event, default=str))

    if duration_ms >= _SLOW_ERROR_MS:
        _app_logger.error(
            "neo4j slow query %.0fms ctx=%s fp=%s :: %s",
            duration_ms,
            event["request_ctx"] or "-",
            event["fingerprint"],
            normalized[:200],
        )
    elif duration_ms >= _SLOW_WARN_MS:
        _app_logger.warning(
            "neo4j slow query %.0fms ctx=%s fp=%s :: %s",
            duration_ms,
            event["request_ctx"] or "-",
            event["fingerprint"],
            normalized[:200],
        )


class TimedResult:
    """Wraps a `Result` so duration is measured at consumption time.

    Neo4j's Python driver streams rows back lazily. A user's wall-clock
    cost is run() + consumption, so we don't log until the caller pulls
    the data out (.data() / .single() / iteration).
    """

    def __init__(self, result, cypher: str, params: dict, start_ns: int):
        self._result = result
        self._cypher = cypher
        self._params = params
        self._start_ns = start_ns
        self._logged = False

    def _finish(self, consumer: str, count):
        if self._logged:
            return
        self._logged = True
        duration_ms = (time.monotonic_ns() - self._start_ns) / 1_000_000
        _emit(
            self._cypher,
            self._params,
            duration_ms,
            consumer=consumer,
            result_count=count,
        )

    def data(self):
        try:
            rows = self._result.data()
            self._finish("data", len(rows))
            return rows
        except Exception:
            self._finish("data_error", None)
            raise

    def single(self):
        try:
            row = self._result.single()
            self._finish("single", 1 if row else 0)
            return row
        except Exception:
            self._finish("single_error", None)
            raise

    def __iter__(self):
        count = 0
        try:
            for record in self._result:
                count += 1
                yield record
        finally:
            self._finish("iter", count)

    def consume(self):
        try:
            summary = self._result.consume()
            self._finish("consume", None)
            return summary
        except Exception:
            self._finish("consume_error", None)
            raise

    def __del__(self):
        # Fire-and-forget writes (`session.run("MERGE ...")` with no
        # consumption) get their result GC'd on the next run() or
        # session close. Catch those so write-path latency still shows
        # up in the log; consumed Results have _logged=True so this is
        # a no-op for them.
        if not self._logged:
            try:
                self._finish("gc", None)
            except Exception:
                pass

    def __getattr__(self, name):
        return getattr(self._result, name)


class TimedTransaction:
    def __init__(self, tx):
        self._tx = tx

    def run(self, cypher, parameters=None, **kwargs):
        params = dict(parameters or {}, **kwargs)
        start = time.monotonic_ns()
        result = self._tx.run(cypher, **params)
        return TimedResult(result, cypher, params, start)

    def __getattr__(self, name):
        return getattr(self._tx, name)


class TimedSession:
    def __init__(self, session):
        self._session = session

    def run(self, cypher, parameters=None, **kwargs):
        params = dict(parameters or {}, **kwargs)
        start = time.monotonic_ns()
        result = self._session.run(cypher, **params)
        return TimedResult(result, cypher, params, start)

    def execute_read(self, transaction_function, *args, **kwargs):
        return self._execute_managed("read", transaction_function, *args, **kwargs)

    def execute_write(self, transaction_function, *args, **kwargs):
        return self._execute_managed("write", transaction_function, *args, **kwargs)

    def _execute_managed(self, mode: str, fn, *args, **kwargs):
        wrapped = lambda tx, *a, **k: fn(TimedTransaction(tx), *a, **k)
        method = (
            self._session.execute_read
            if mode == "read"
            else self._session.execute_write
        )
        return method(wrapped, *args, **kwargs)

    def begin_transaction(self, *args, **kwargs):
        return TimedTransaction(self._session.begin_transaction(*args, **kwargs))

    def __enter__(self):
        self._session.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self._session.__exit__(exc_type, exc, tb)

    def close(self):
        self._session.close()

    def __getattr__(self, name):
        return getattr(self._session, name)


class TimedDriver:
    def __init__(self, driver):
        self._driver = driver

    def session(self, *args, **kwargs):
        return TimedSession(self._driver.session(*args, **kwargs))

    def close(self):
        self._driver.close()

    def __getattr__(self, name):
        return getattr(self._driver, name)
