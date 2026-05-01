from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator


class VaultFile(BaseModel):
    path: Path
    mtime: float
    links: list[str] = []

    @field_validator("path")
    @classmethod
    def path_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Path does not exist: {v}")
        return v

    model_config = {"frozen": True}


class Heading(BaseModel):
    level: int  # 1, 2, or 3
    text: str
    char_pos: int


class ParsedNote(BaseModel):
    title: str
    note_type: str | None
    tags: set[str]
    wikilinks: set[str]
    content: str
    frontmatter: dict[str, Any]
    source_path: Path
    headings: list[Heading]
