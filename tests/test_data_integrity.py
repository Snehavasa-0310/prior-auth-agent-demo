"""Test data integrity for policies and synthetic clinical notes."""

import json
from pathlib import Path

from src.core.phi import PHIGuard


def test_policies_exist_and_valid():
    policies_dir = Path("data/policies")
    assert policies_dir.exists(), "data/policies directory missing"
    policy_files = list(policies_dir.glob("*.json"))
    assert len(policy_files) >= 8, f"Expected at least 8 policies, found {len(policy_files)}"

    for pfile in policy_files:
        with open(pfile, encoding="utf-8") as f:
            data = json.load(f)
        assert "id" in data
        assert "procedure_name" in data
        assert "criteria" in data
        assert len(data["criteria"]) >= 2
        for crit in data["criteria"]:
            assert "id" in crit
            assert "title" in crit
            assert "description" in crit


def test_synthetic_notes_integrity():
    notes_file = Path("data/synthetic_notes.jsonl")
    assert notes_file.exists(), "data/synthetic_notes.jsonl missing"

    phi_guard = PHIGuard()
    cases = []
    with open(notes_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    assert len(cases) >= 100, f"Expected >= 100 cases, got {len(cases)}"

    tricky_count = 0
    for case in cases:
        # Invariant 1: No PHI
        phi_res = phi_guard.scan(case["clinical_note"])
        assert phi_res.is_safe, f"Case {case['case_id']} contains potential PHI: {phi_res.summary}"

        # Invariant 2: Ground truth quotes must be exact substrings if MET
        note = case["clinical_note"]
        for crit_id, crit_data in case["ground_truth_criteria"].items():
            quote = crit_data.get("evidence_quote", "").strip()
            if crit_data["status"] == "MET":
                assert quote, f"Case {case['case_id']}: {crit_id} is MET without quote"
                assert quote in note, f"Case {case['case_id']}: Quote for {crit_id} not an exact substring: '{quote}'"

        if case.get("is_tricky_case"):
            tricky_count += 1

    assert tricky_count >= 20, f"Expected at least 20 tricky cases, got {tricky_count}"
