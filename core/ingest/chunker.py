from pathlib import Path

from core.models import Chunk, ParsedNote


def chunk_note(
    note: ParsedNote,
    chunk_size: int = 512,
    overlap: int = 64,
) -> list[Chunk]:

    chunks: list[Chunk] = []
    content = note.content
    headings = note.headings  # already sorted by char_pos from the parser

    __import__("pprint").pprint(content)
    __import__("pprint").pprint(headings)
    return chunks


if __name__ == "__main__":
    path = Path(
        "~/Documents/obsidian/knowledge/01 Notes/Lecture 2 - Client Server Architecture and the World Wide Web.md"
    ).expanduser()
    vault_file = VaultFile(
        path=path,
        mtime=path.stat().st_mtime,
    )

    import pprint

    note = parseNote(
        vault_file, load_config("~/Documents/projects/oxidian/config.example.toml")
    )

    pprint.pprint(note)
