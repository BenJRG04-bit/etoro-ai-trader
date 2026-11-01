import unittest
from provenance_readiness_gate import verify_provenance_readiness

def readiness(missing=True):
    return {"status": "MORE_EVIDENCE_REQUIRED",
            "issues": ["MISSING_OR_INVALID_INPUTS"] if missing else ["HISTORY_COVERAGE_NOT_READY", "FORWARD_COVERAGE_NOT_READY"],
            "research_only": True, "orders_allowed": False, "live_trading_approved": False,
            **({} if missing else {"checks": {"history": component(), "forward": component()}})}

def component():
    return {"status": "NEEDS_MORE_EVIDENCE", "research_only": True,
            "orders_allowed": False, "live_trading_approved": False}

def provenance(missing=True):
    labels = ("history", "forward_audit", "forward_quality")
    return {"status": "INPUTS_INCOMPLETE" if missing else "INPUTS_PRESENT",
            "inputs": {label: {"status": "MISSING" if missing else "VALID_SAFE_JSON"} for label in labels},
            "blockers": list(labels) if missing else [],
            "research_only": True, "orders_allowed": False, "live_trading_approved": False}

class ProvenanceReadinessGateTests(unittest.TestCase):
    def test_missing_inputs_with_explicit_failure(self):
        self.assertEqual(verify_provenance_readiness(provenance(), readiness())["status"], "PROVENANCE_CONSISTENT")

    def test_present_inputs_with_coverage_shortfall(self):
        self.assertEqual(verify_provenance_readiness(provenance(False), readiness(False))["status"], "PROVENANCE_CONSISTENT")

    def test_missing_inputs_not_disclosed(self):
        with self.assertRaises(ValueError):
            verify_provenance_readiness(provenance(), readiness(False))

    def test_fabricated_missing_inputs_claim(self):
        with self.assertRaises(ValueError):
            verify_provenance_readiness(provenance(False), readiness())

    def test_provenance_status_contradiction(self):
        p = provenance()
        p["status"] = "INPUTS_PRESENT"
        with self.assertRaises(ValueError):
            verify_provenance_readiness(p, readiness())

    def test_unsafe_provenance(self):
        p = provenance()
        p["orders_allowed"] = True
        with self.assertRaises(ValueError):
            verify_provenance_readiness(p, readiness())

if __name__ == "__main__":
    unittest.main()
