"""Tests for data models."""

import pytest

from speckit_update.models import (
    ConfidenceLevel,
    ConflictResult,
    FileAnalysis,
    FileState,
    FingerprintMatch,
    TrackedFile,
    UpdatePlan,
)


class TestFileState:
    """Tests for FileState enum."""

    def test_all_states_defined(self) -> None:
        """All expected file states should be defined."""
        expected = {"ADD", "REMOVE", "UPDATE", "PRESERVE", "MERGE", "SKIP"}
        actual = {state.name for state in FileState}
        assert actual == expected

    def test_state_values(self) -> None:
        """State values should be lowercase strings."""
        assert FileState.ADD.value == "add"
        assert FileState.MERGE.value == "merge"
        assert FileState.SKIP.value == "skip"


class TestConfidenceLevel:
    """Tests for ConfidenceLevel enum."""

    def test_all_levels_defined(self) -> None:
        """All expected confidence levels should be defined."""
        expected = {"HIGH", "MEDIUM", "LOW"}
        actual = {level.name for level in ConfidenceLevel}
        assert actual == expected


class TestTrackedFile:
    """Tests for TrackedFile dataclass."""

    def test_valid_creation(self) -> None:
        """Should create TrackedFile with valid hash."""
        tf = TrackedFile(
            path=".claude/commands/test.md",
            original_hash="sha256:" + "a" * 64,
            customized=False,
            is_official=True,
        )
        assert tf.path == ".claude/commands/test.md"
        assert tf.customized is False

    def test_invalid_hash_raises(self) -> None:
        """Should raise ValueError for invalid hash format."""
        with pytest.raises(ValueError, match="Invalid hash format"):
            TrackedFile(
                path="test.md",
                original_hash="md5:abc123",
                customized=False,
                is_official=False,
            )

    def test_to_dict_roundtrip(self, sample_tracked_file: TrackedFile) -> None:
        """Should serialize and deserialize correctly."""
        data = sample_tracked_file.to_dict()
        restored = TrackedFile.from_dict(data)
        assert restored == sample_tracked_file


class TestConflictResult:
    """Tests for ConflictResult dataclass."""

    def test_clean_merge(self) -> None:
        """Clean merge should have no conflicts."""
        result = ConflictResult.clean_merge("merged content")
        assert result.has_conflicts is False
        assert result.conflict_count == 0
        assert result.merged_content == "merged content"

    def test_with_conflicts(self) -> None:
        """Should track conflict markers."""
        markers = [(10, 20), (30, 40)]
        result = ConflictResult.with_conflicts("content", markers)
        assert result.has_conflicts is True
        assert result.conflict_count == 2
        assert len(result.conflict_markers) == 2


class TestFingerprintMatch:
    """Tests for FingerprintMatch dataclass."""

    def test_no_match(self) -> None:
        """No match should have LOW confidence."""
        match = FingerprintMatch.no_match()
        assert match.confidence == ConfidenceLevel.LOW
        assert match.method == "none"
        assert match.version == ""

    def test_from_signature_high_confidence(self) -> None:
        """95%+ match should be HIGH confidence."""
        match = FingerprintMatch.from_signature("v0.0.79", 100.0)
        assert match.confidence == ConfidenceLevel.HIGH
        assert match.method == "signature"

    def test_from_signature_medium_confidence(self) -> None:
        """70-94% match should be MEDIUM confidence."""
        match = FingerprintMatch.from_signature("v0.0.79", 80.0)
        assert match.confidence == ConfidenceLevel.MEDIUM

    def test_from_signature_low_confidence(self) -> None:
        """<70% match should be LOW confidence."""
        match = FingerprintMatch.from_signature("v0.0.79", 50.0)
        assert match.confidence == ConfidenceLevel.LOW


class TestUpdatePlan:
    """Tests for UpdatePlan dataclass."""

    def test_up_to_date(self) -> None:
        """Up to date plan should have no changes."""
        plan = UpdatePlan.up_to_date("v0.0.79")
        assert plan.is_up_to_date is True
        assert plan.has_changes is False
        assert plan.has_conflicts is False

    def test_has_changes(self, sample_update_plan: UpdatePlan) -> None:
        """Plan with updates should report has_changes."""
        assert sample_update_plan.has_changes is True
        assert sample_update_plan.has_conflicts is True

    def test_total_files_affected(self, sample_update_plan: UpdatePlan) -> None:
        """Should count all affected files."""
        # add: 1, update: 1, merge: 1, remove: 0 = 3
        assert sample_update_plan.total_files_affected == 3


class TestFileAnalysis:
    """Tests for FileAnalysis dataclass."""

    def test_is_customized(self) -> None:
        """Should detect customized files."""
        analysis = FileAnalysis(
            path="test.md",
            state=FileState.PRESERVE,
            current_hash="sha256:" + "a" * 64,
            manifest_hash="sha256:" + "b" * 64,
            upstream_hash=None,
        )
        assert analysis.is_customized is True

    def test_not_customized_when_hashes_match(self) -> None:
        """Should not be customized when hashes match."""
        same_hash = "sha256:" + "a" * 64
        analysis = FileAnalysis(
            path="test.md",
            state=FileState.SKIP,
            current_hash=same_hash,
            manifest_hash=same_hash,
            upstream_hash=same_hash,
        )
        assert analysis.is_customized is False

    def test_requires_action(self) -> None:
        """Should require action for non-skip/preserve states."""
        for state in [FileState.ADD, FileState.UPDATE, FileState.MERGE, FileState.REMOVE]:
            analysis = FileAnalysis(
                path="test.md",
                state=state,
                current_hash=None,
                manifest_hash=None,
                upstream_hash=None,
            )
            assert analysis.requires_action is True

    def test_no_action_for_skip_preserve(self) -> None:
        """Should not require action for SKIP and PRESERVE."""
        for state in [FileState.SKIP, FileState.PRESERVE]:
            analysis = FileAnalysis(
                path="test.md",
                state=state,
                current_hash=None,
                manifest_hash=None,
                upstream_hash=None,
            )
            assert analysis.requires_action is False
