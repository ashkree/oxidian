from pathlib import Path

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
