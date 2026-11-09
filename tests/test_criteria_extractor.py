"""Tests for Criteria Extractor."""

from pathlib import Path

from src.policy.extractor import CriteriaExtractor
from src.policy.loader import load_policies_from_dir


def test_criteria_extractor_and_caching(tmp_path):
    policies_dir = Path("data/policies")
    policies = load_policies_from_dir(policies_dir)
    lumbar_policy = next(p for p in policies if "LUMBAR" in p.id)

    extractor = CriteriaExtractor(cache_dir=tmp_path / "criteria_cache")
    result = extractor.extract(lumbar_policy)

    assert result.policy_id == lumbar_policy.id
    assert len(result.criteria) >= 3
    for crit in result.criteria:
        assert crit.id.startswith("CRIT-")
        assert crit.title
        assert crit.description

    # Verify cache file was written
    cache_file = tmp_path / "criteria_cache" / f"{lumbar_policy.id}.json"
    assert cache_file.exists()

    # Second extract call should load from cache
    cached_result = extractor.extract(lumbar_policy)
    assert cached_result.policy_id == result.policy_id
    assert len(cached_result.criteria) == len(result.criteria)
