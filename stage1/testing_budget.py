"""Durable, shared inference budget for Glimmer sampling and its reading judge.

Reserve BEFORE any outbound request and use a stable, unique request_id. A
reservation is permission for one attempt only; duplicate IDs always fail.
Timeouts, crashes, and failed requests keep the full bound. Only provider-known
usage may be settled. This module never opens a network connection or stores
prompts, responses, credentials, or provider error messages.

Caller contract: Glimmer input_tokens is the exact pinned-renderer token count;
judge input_tokens is a conservative bound for the FULL serialized request
(UTF-8 byte count plus 2048 framing tokens). Output caps include reasoning and
protocol tokens. Rates apply only to the approved global Standard text APIs,
without paid tools, regional uplifts, priority processing, or deployments.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sqlite3
import uuid


DEFAULT_CAP_USD = "3.99"
NANODOLLARS = 1_000_000_000
MAX_TOKENS = 131_072
# Integer nanodollars per token; no binary floating-point money arithmetic.
TARIFFS = {"glimmer": (1960, 4880), "judge": (5000, 10000)}
PRICING_VERIFIED = "2026-11-18"
_POLICY = json.dumps({"version": 1, "rates": TARIFFS, "max_tokens": MAX_TOKENS,
                      "judge_output_cap": 3000}, sort_keys=True)
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,511}\Z")


class BudgetError(RuntimeError):
    """A budget failure must prevent an outbound request."""


class BudgetExceeded(BudgetError):
    pass


class DuplicateRequest(BudgetError):
    pass


class UsageExceededReservation(BudgetError):
    pass


def _tokens(value, name):
    if type(value) is not int or not 0 <= value <= MAX_TOKENS:
        raise ValueError(f"{name} must be a nonnegative integer at most {MAX_TOKENS}.")
    return value


def _identifier(value, name):
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{name} must be an opaque identifier, without whitespace.")
    return value


def _money(value):
    return format(Decimal(value) / NANODOLLARS, ".9f")


def _cap(value):
    if isinstance(value, (float, bool)):
        raise ValueError("Budget cap must use an exact decimal string.")
    try:
        amount = Decimal(value)
        units = amount * NANODOLLARS
        if not amount.is_finite() or not 0 < amount <= Decimal(DEFAULT_CAP_USD):
            raise ValueError
        if units != units.to_integral_value():
            raise ValueError
        return int(units)
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError(f"Budget cap must be positive and at most ${DEFAULT_CAP_USD}.") from None


class BudgetLedger:
    """Use ONE persistent path for both generation and evaluation, on every run.

    SQLite BEGIN IMMEDIATE serializes the budget check and reservation across
    processes. FULL synchronous commits survive restarts; there is no expiry or
    automatic refund. Changing an existing ledger's policy/cap fails closed.
    """

    def __init__(self, path, cap_usd=DEFAULT_CAP_USD):
        self.path = Path(path)
        if str(path) == ":memory:":
            raise ValueError("The testing budget requires a persistent ledger path.")
        cap = _cap(cap_usd)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS policy "
                       "(id INTEGER PRIMARY KEY CHECK(id=1), cap INTEGER NOT NULL, "
                       "definition TEXT NOT NULL, blocked INTEGER NOT NULL DEFAULT 0)")
            db.execute("CREATE TABLE IF NOT EXISTS reservations ("
                       "id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE, "
                       "kind TEXT NOT NULL CHECK(kind IN ('glimmer','judge')), "
                       "model TEXT NOT NULL, input_bound INTEGER NOT NULL, "
                       "output_bound INTEGER NOT NULL, bound INTEGER NOT NULL, "
                       "charged INTEGER NOT NULL, state TEXT NOT NULL "
                       "CHECK(state IN ('reserved','failed','settled','overrun')), "
                       "actual_input INTEGER, actual_output INTEGER, created_at TEXT NOT NULL)")
            db.execute("INSERT OR IGNORE INTO policy(id,cap,definition) VALUES (1,?,?)",
                       (cap, _POLICY))
            saved = db.execute("SELECT cap,definition FROM policy WHERE id=1").fetchone()
            if saved != (cap, _POLICY):
                raise BudgetError("Existing testing budget has a different cap or pricing policy.")

    @contextmanager
    def _transaction(self):
        db = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        try:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.execute("COMMIT")
        except BaseException:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
        finally:
            db.close()

    def reserve(self, kind, input_tokens, output_tokens, *, model, request_id):
        """Commit the maximum cost before the caller makes ONE provider attempt.

        Returns a reservation UUID. Duplicate request IDs raise, even after
        failure or settlement; they never return authorization for another call.
        """
        if kind not in TARIFFS:
            raise ValueError("Only glimmer sampling and the reading judge are budgeted.")
        _tokens(input_tokens, "input_tokens")
        _tokens(output_tokens, "output_tokens")
        _identifier(model, "model")
        _identifier(request_id, "request_id")
        if input_tokens + output_tokens > MAX_TOKENS:
            raise ValueError("Request exceeds the approved short-context token bound.")
        if kind == "judge" and (model != "gpt-6.1-sol" or output_tokens > 3000):
            raise ValueError("Reading judge must use gpt-6.1-sol with at most 3000 output tokens.")
        input_rate, output_rate = TARIFFS[kind]
        bound = input_tokens * input_rate + output_tokens * output_rate
        reservation_id = str(uuid.uuid4())
        with self._transaction() as db:
            if db.execute("SELECT 1 FROM reservations WHERE request_id=?", (request_id,)).fetchone():
                raise DuplicateRequest("This testing request was already reserved; retries are disabled.")
            cap, blocked = db.execute("SELECT cap,blocked FROM policy WHERE id=1").fetchone()
            if blocked:
                raise BudgetExceeded("Testing budget is blocked after usage exceeded a reserved bound.")
            used = db.execute("SELECT COALESCE(SUM(charged),0) FROM reservations").fetchone()[0]
            if bound > cap - used:
                raise BudgetExceeded(f"Testing budget exhausted: ${_money(max(0, cap-used))} remains; "
                                     f"this request needs ${_money(bound)}.")
            db.execute("INSERT INTO reservations VALUES (?,?,?,?,?,?,?,?,'reserved',NULL,NULL,?)",
                       (reservation_id, request_id, kind, model, input_tokens, output_tokens,
                        bound, bound, datetime.now(timezone.utc).isoformat()))
        return reservation_id

    def fail(self, reservation_id):
        """Mark an uncertain/failed attempt without releasing any reservation."""
        with self._transaction() as db:
            row = db.execute("SELECT state FROM reservations WHERE id=?", (reservation_id,)).fetchone()
            if row is None:
                raise ValueError("Unknown testing budget reservation.")
            if row[0] == "reserved":
                db.execute("UPDATE reservations SET state='failed' WHERE id=?", (reservation_id,))

    def settle(self, reservation_id, *, input_tokens, output_tokens):
        """Settle only known complete usage, counting every generated token.

        Cached input still uses the conservative input tariff. A usage overrun
        retains at least the full reservation, records any higher actual cost,
        and durably blocks new calls. Settlement cannot silently release it.
        """
        # Provider overrun can exceed the approved request limits; still account
        # for it, using a large safe integer bound that cannot overflow SQLite.
        for value in (input_tokens, output_tokens):
            if type(value) is not int or not 0 <= value <= 1_000_000_000:
                raise ValueError("Known usage must be nonnegative integer token counts.")
        overrun = False
        with self._transaction() as db:
            row = db.execute("SELECT kind,input_bound,output_bound,bound,state,actual_input,actual_output "
                             "FROM reservations WHERE id=?", (reservation_id,)).fetchone()
            if row is None:
                raise ValueError("Unknown testing budget reservation.")
            kind, in_bound, out_bound, bound, state, actual_in, actual_out = row
            if state in ("settled", "overrun"):
                if (actual_in, actual_out) != (input_tokens, output_tokens):
                    raise BudgetError("Testing usage was already recorded; conflicting settlement refused.")
                overrun = state == "overrun"
            else:
                in_rate, out_rate = TARIFFS[kind]
                charge = input_tokens * in_rate + output_tokens * out_rate
                overrun = input_tokens > in_bound or output_tokens > out_bound
                if overrun:
                    charge = max(bound, charge)
                    db.execute("UPDATE policy SET blocked=1 WHERE id=1")
                db.execute("UPDATE reservations SET charged=?,state=?,actual_input=?,actual_output=? WHERE id=?",
                           (charge, "overrun" if overrun else "settled", input_tokens,
                            output_tokens, reservation_id))
        if overrun:
            raise UsageExceededReservation("Provider usage exceeded its reserved token bound; "
                                           "testing budget is blocked for review.")
        return self.status()

    def status(self):
        """Return only aggregate costs/counts, suitable for the testing UI."""
        with self._transaction() as db:
            cap, blocked = db.execute("SELECT cap,blocked FROM policy WHERE id=1").fetchone()
            spent, reserved, count, failed = db.execute(
                "SELECT COALESCE(SUM(CASE WHEN state='settled' THEN charged ELSE 0 END),0),"
                "COALESCE(SUM(CASE WHEN state!='settled' THEN charged ELSE 0 END),0),"
                "COUNT(*),COALESCE(SUM(CASE WHEN state='failed' THEN 1 ELSE 0 END),0) "
                "FROM reservations").fetchone()
        return {"cap_usd": _money(cap), "spent_usd": _money(spent),
                "reserved_usd": _money(reserved), "committed_usd": _money(spent+reserved),
                "remaining_usd": _money(max(0, cap-spent-reserved)),
                "reservation_count": count, "failed_count": failed, "blocked": bool(blocked)}
