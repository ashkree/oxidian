# tests/test_walker.py
from pathlib import Path

import pytest

from core.ingest.walker import walk_vault

SAMPLE_VAULT = Path("data/sample")


@pytest.fixture(scope="session")
def vault_files():
    return walk_vault(SAMPLE_VAULT)


# --- happy path ---


def test_finds_md_files(vault_files):
    assert len(vault_files) > 0


def test_all_files_are_md(vault_files):
    assert all(f.path.suffix == ".md" for f in vault_files)


def test_all_files_have_mtime(vault_files):
    assert all(f.mtime > 0 for f in vault_files)


def test_all_links_start_empty(vault_files):
    assert all(f.links == [] for f in vault_files)


def test_all_files_exist(vault_files):
    assert all(f.path.exists() for f in vault_files)


# --- exclusions ---


def test_excludes_hidden_dirs(vault_files):
    assert not any(
        any(part.startswith(".") for part in f.path.parts) for f in vault_files
    )


# --- bad paths ---


@pytest.mark.parametrize(
    "bad_path",
    [
        "fake/path",
        "/tmp/nonexistent",
    ],
)
def test_bad_path_raises(bad_path):
    with pytest.raises(ValueError):
        walk_vault(Path(bad_path))
