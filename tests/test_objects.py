from pathlib import Path
from typing import Any

from core.config import load_config
from core.ingest.parser import parse_note
from core.models import ParsedNote, VaultFile

test_note = Path("./tests/test_note.md")
test_config: dict[str, Any] = load_config("./tests/test_config.toml")
vault_note: VaultFile = VaultFile(path=test_note, mtime=test_note.stat().st_mtime)
parsed_note: ParsedNote = parse_note(vault_note, test_config)
