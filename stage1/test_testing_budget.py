"""Offline tests of durable pre-call budget protection; no provider requests."""
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
import multiprocessing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from testing_budget import (BudgetError, BudgetExceeded, BudgetLedger,
                            DuplicateRequest, UsageExceededReservation)


def _concurrent_reserve(args):
    path, request_id = args
    ledger = BudgetLedger(path, "0.01")
    try:
        ledger.reserve("judge", 1000, 100, model="gpt-6.1-sol", request_id=request_id)
        return True
    except BudgetExceeded:
        return False


class TestingBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "budget.sqlite3"
        self.ledger = BudgetLedger(self.path)

    def reserve(self, request_id="request1", kind="glimmer", inputs=1000, outputs=128):
        return self.ledger.reserve(kind, inputs, outputs,
                                   model="gpt-6.1-sol" if kind == "judge" else "glimmer-sampler-v1",
                                   request_id=request_id)

    def test_default_cap_including_contingency_strictly_below_five(self):
        status = self.ledger.status()
        self.assertEqual(status["cap_usd"], "3.990000000")
        self.assertLess(Decimal(status["cap_usd"]) * Decimal("1.25"), Decimal(5))
        self.assertEqual(status["spent_usd"], "0.000000000")

    def test_exact_tariffs_shared_budget_and_restart(self):
        self.reserve()
        self.reserve("judge1", "judge", 1000, 3000)
        status = BudgetLedger(self.path).status()
        self.assertEqual(status["reserved_usd"], "0.037584640")
        self.assertEqual(status["committed_usd"], status["reserved_usd"])
        self.assertEqual(status["reservation_count"], 2)
        self.assertEqual(status["remaining_usd"], "3.952415360")

    def test_failed_and_abandoned_requests_never_expire_or_refund(self):
        first = self.reserve()
        self.reserve("abandoned")
        before = self.ledger.status()["reserved_usd"]
        self.ledger.fail(first)
        self.ledger.fail(first)
        status = BudgetLedger(self.path).status()
        self.assertEqual(status["reserved_usd"], before)
        self.assertEqual(status["failed_count"], 1)
        self.assertEqual(status["spent_usd"], "0.000000000")

    def test_known_usage_only_releases_unused_bound_and_is_idempotent(self):
        first = self.reserve()
        status = self.ledger.settle(first, input_tokens=100, output_tokens=20)
        self.assertEqual(status["spent_usd"], "0.000293600")
        self.assertEqual(status["reserved_usd"], "0.000000000")
        self.assertEqual(self.ledger.settle(first, input_tokens=100, output_tokens=20), status)
        with self.assertRaises(BudgetError):
            self.ledger.settle(first, input_tokens=0, output_tokens=0)
        self.assertEqual(self.ledger.status(), status)

    def test_failed_call_can_be_reconciled_with_known_complete_usage(self):
        first = self.reserve()
        self.ledger.fail(first)
        self.ledger.settle(first, input_tokens=100, output_tokens=20)
        self.assertEqual(self.ledger.status()["spent_usd"], "0.000293600")

    def test_duplicate_request_never_authorizes_another_attempt(self):
        first = self.reserve()
        for action in (lambda: None, lambda: self.ledger.fail(first),
                       lambda: self.ledger.settle(first, input_tokens=10, output_tokens=10)):
            action()
            with self.assertRaises(DuplicateRequest):
                self.reserve()
        self.assertEqual(BudgetLedger(self.path).status()["reservation_count"], 1)

    def test_overrun_holds_charge_and_blocks_after_restart(self):
        first = self.reserve()
        before = self.ledger.status()["reserved_usd"]
        with self.assertRaises(UsageExceededReservation):
            # A per-dimension overrun must block even if total cost is lower.
            self.ledger.settle(first, input_tokens=1001, output_tokens=0)
        self.assertEqual(self.ledger.status()["reserved_usd"], before)
        self.assertTrue(BudgetLedger(self.path).status()["blocked"])
        with self.assertRaises(BudgetExceeded):
            self.reserve("after-overrun")
        self.ledger.fail(first)
        with self.assertRaises(UsageExceededReservation):
            self.ledger.settle(first, input_tokens=1001, output_tokens=0)

    def test_cost_overrun_is_recorded_without_truncation(self):
        first = self.reserve()
        with self.assertRaises(UsageExceededReservation):
            self.ledger.settle(first, input_tokens=100_000, output_tokens=100_000)
        self.assertEqual(self.ledger.status()["reserved_usd"], "0.684000000")

    def test_different_cap_or_policy_fails_closed(self):
        with self.assertRaises(BudgetError):
            BudgetLedger(self.path, "3.98")
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE policy SET definition='old policy'")
        with self.assertRaises(BudgetError):
            BudgetLedger(self.path)

    def test_exact_cap_allowed_next_positive_cost_refused(self):
        path = Path(self.temp.name) / "tiny.sqlite3"
        ledger = BudgetLedger(path, "0.000001960")
        ledger.reserve("glimmer", 1, 0, model="glimmer", request_id="one")
        with self.assertRaises(BudgetExceeded) as error:
            ledger.reserve("glimmer", 1, 0, model="glimmer", request_id="two")
        self.assertIn("$0.000000000 remains", str(error.exception))
        self.assertEqual(ledger.status()["remaining_usd"], "0.000000000")

    def test_invalid_bounds_tariffs_and_models_are_refused_without_write(self):
        for token in (-1, 1.1, True, "100", 131_073):
            with self.subTest(token=token), self.assertRaises(ValueError):
                self.reserve(inputs=token)
        for kind, model, inputs, outputs in (("openai", "x", 1, 1),
                                              ("judge", "gpt-6.2-sol", 1, 100),
                                              ("judge", "gpt-6.1-sol", 1, 3001),
                                              ("glimmer", "glimmer", 131072, 1)):
            with self.subTest(kind=kind, model=model), self.assertRaises(ValueError):
                self.ledger.reserve(kind, inputs, outputs, model=model, request_id="invalid")
        self.assertEqual(self.ledger.status()["reservation_count"], 0)

    def test_invalid_cap_and_in_memory_database_rejected(self):
        for cap in ("5", "4", "-1", "0", "NaN", "Infinity", 3.99, True, "0.0000000001"):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                BudgetLedger(self.path, cap)
        with self.assertRaises(ValueError):
            BudgetLedger(":memory:")

    def test_invalid_or_conflicting_usage_cannot_release_reservation(self):
        first = self.reserve()
        before = self.ledger.status()
        for token in (None, -1, 1.1, True, "10"):
            with self.subTest(token=token), self.assertRaises(ValueError):
                self.ledger.settle(first, input_tokens=token, output_tokens=0)
        with self.assertRaises(ValueError):
            self.ledger.settle("unknown", input_tokens=0, output_tokens=0)
        with self.assertRaises(ValueError):
            self.ledger.fail("unknown")
        self.assertEqual(self.ledger.status(), before)

    def test_status_has_only_aggregates_and_opaque_metadata_contract(self):
        self.reserve("private-request-id")
        self.assertNotIn("private-request-id", str(self.ledger.status()))
        self.assertNotIn("glimmer-sampler-v1", str(self.ledger.status()))
        with self.assertRaises(ValueError):
            self.reserve("a prompt or secret should not be an identifier")

    def test_multiprocess_reservations_atomically_share_the_cap(self):
        path = str(Path(self.temp.name) / "concurrent.sqlite3")
        # Each reservation costs $0.006; only one fits in a $0.01 ledger.
        with ProcessPoolExecutor(max_workers=4, mp_context=multiprocessing.get_context("spawn")) as pool:
            results = list(pool.map(_concurrent_reserve, [(path, f"request-{i}") for i in range(20)]))
        self.assertEqual(sum(results), 1)
        status = BudgetLedger(path, "0.01").status()
        self.assertEqual(status["committed_usd"], "0.006000000")
        self.assertEqual(status["reservation_count"], 1)


if __name__ == "__main__":
    unittest.main()
