from pathlib import Path

from core.models import VaultFile

EXCLUDED_DIRS = {".obsidian", ".trash", ".git"}


def walk_vault(vault_path: str | Path) -> list[VaultFile]:
    if not vault_path:
        raise ValueError("vault_path cannot be None or empty")

    root = Path(vault_path)

    if not root.exists():
        raise ValueError(f"Vault path does not exist: {root}")

    return [
        VaultFile(
            path=p,
            mtime=p.stat().st_mtime,
            links=[],
        )
        for p in root.rglob("*.md")
        if not any(part in EXCLUDED_DIRS for part in p.parts)
    ]
