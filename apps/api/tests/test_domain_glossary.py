"""Tests for P00-02 Domain Glossary."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure contracts package is importable.
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from app.main import app
from contracts.domain_glossary import (
    CANONICAL_ENTITIES,
    FORBIDDEN_SYNONYMS,
    is_canonical,
    lookup_canonical,
    validate_term,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Contract module tests
# ---------------------------------------------------------------------------

class TestCanonicalEntities:
    """Verify the canonical entity registry."""

    def test_entity_count_matches_glossary(self) -> None:
        # The DOMAIN_GLOSSARY.yml has exactly 36 entities.
        assert len(CANONICAL_ENTITIES) == 36

    def test_all_entities_have_non_empty_definitions(self) -> None:
        for term, definition in CANONICAL_ENTITIES.items():
            assert isinstance(definition, str) and len(definition) > 0, (
                f"Entity '{term}' has an empty or non-string definition"
            )

    def test_key_entities_present(self) -> None:
        required = [
            "tenant", "branch", "user", "patient", "order",
            "sample", "result", "report", "invoice", "payment",
            "donor", "blood_unit", "analyzer", "license", "backup",
        ]
        for term in required:
            assert term in CANONICAL_ENTITIES, f"Missing canonical entity: {term}"


class TestForbiddenSynonyms:
    """Verify the forbidden synonyms registry."""

    def test_every_canonical_entity_has_forbidden_synonyms(self) -> None:
        for term in CANONICAL_ENTITIES:
            assert term in FORBIDDEN_SYNONYMS, (
                f"Canonical entity '{term}' has no forbidden synonyms defined"
            )

    def test_forbidden_synonym_keys_match_canonical(self) -> None:
        """No orphan synonym entries for non-existent canonical terms."""
        for term in FORBIDDEN_SYNONYMS:
            assert term in CANONICAL_ENTITIES, (
                f"Forbidden synonym key '{term}' is not a canonical entity"
            )

    def test_no_canonical_term_in_its_own_forbidden_list(self) -> None:
        for term, synonyms in FORBIDDEN_SYNONYMS.items():
            assert term not in synonyms, (
                f"Canonical term '{term}' must not appear in its own forbidden list"
            )

    def test_all_synonym_lists_non_empty(self) -> None:
        for term, synonyms in FORBIDDEN_SYNONYMS.items():
            assert len(synonyms) >= 1, (
                f"Entity '{term}' should have at least one forbidden synonym"
            )

    def test_synonyms_are_lowercase_identifiers(self) -> None:
        """Forbidden synonyms should be valid lowercase identifiers."""
        for term, synonyms in FORBIDDEN_SYNONYMS.items():
            for syn in synonyms:
                assert syn == syn.lower(), (
                    f"Synonym '{syn}' for '{term}' is not lowercase"
                )
                assert syn.replace("_", "").isalnum(), (
                    f"Synonym '{syn}' for '{term}' is not a valid identifier"
                )


class TestHelperFunctions:
    """Verify glossary helper functions."""

    def test_is_canonical_true_for_known_terms(self) -> None:
        assert is_canonical("patient") is True
        assert is_canonical("tenant") is True

    def test_is_canonical_false_for_synonyms(self) -> None:
        assert is_canonical("specimen") is False
        assert is_canonical("org") is False

    def test_lookup_canonical_returns_correct_term(self) -> None:
        assert lookup_canonical("specimen") == "sample"
        assert lookup_canonical("org") == "tenant"
        assert lookup_canonical("bag") == "blood_unit"

    def test_lookup_canonical_returns_none_for_unknown(self) -> None:
        assert lookup_canonical("foobar_xyz") is None

    def test_validate_term_canonical(self) -> None:
        ok, suggestion = validate_term("patient")
        assert ok is True
        assert suggestion is None

    def test_validate_term_forbidden(self) -> None:
        ok, suggestion = validate_term("specimen")
        assert ok is False
        assert suggestion == "sample"

    def test_validate_term_unknown(self) -> None:
        ok, suggestion = validate_term("completely_unknown_word")
        assert ok is True
        assert suggestion is None


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestDomainGlossaryEndpoint:
    """Verify the /domain-glossary API endpoint."""

    def test_returns_200(self) -> None:
        r = client.get("/domain-glossary")
        assert r.status_code == 200

    def test_response_has_entity_count(self) -> None:
        data = client.get("/domain-glossary").json()
        assert data["entity_count"] == 36

    def test_response_has_entities_dict(self) -> None:
        data = client.get("/domain-glossary").json()
        assert isinstance(data["entities"], dict)
        assert "patient" in data["entities"]

    def test_response_has_forbidden_synonyms(self) -> None:
        data = client.get("/domain-glossary").json()
        assert isinstance(data["forbidden_synonyms"], dict)
        assert "patient" in data["forbidden_synonyms"]

    def test_entities_and_synonyms_keys_match(self) -> None:
        data = client.get("/domain-glossary").json()
        assert set(data["entities"].keys()) == set(data["forbidden_synonyms"].keys())

    def test_specimen_is_forbidden_for_sample(self) -> None:
        data = client.get("/domain-glossary").json()
        assert "specimen" in data["forbidden_synonyms"]["sample"]

    def test_org_is_forbidden_for_tenant(self) -> None:
        data = client.get("/domain-glossary").json()
        assert "org" in data["forbidden_synonyms"]["tenant"]
