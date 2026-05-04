from core.models import Chunk, Heading, ParsedNote


def chunk_note(
    note: ParsedNote,
) -> list[Chunk]:

    chunks: list[Chunk] = []
    content = note.content
    headings = note.headings  # already sorted by char_pos from the parser

    starts = [0] + [h.char_pos for h in headings]
    ends = [h.char_pos for h in headings] + [len(content)]
    heading_refs = [None] + list(headings)

    for start, end, heading in zip(starts, ends, heading_refs):
        text = content[start:end].strip()

        if text:
            chunks.append(generate_chunk(note, start, end, heading, text))

    return chunks


def segment_chunk(text: str) -> list[str]:

    segments: list[str] = []

    return segments


def generate_chunk(
    note: ParsedNote, start: int, end: int, heading: Heading | None, text: str
) -> Chunk:

    return Chunk(
        source_path=note.source_path,
        heading=heading.text if heading else None,
        heading_level=heading.level if heading else None,
        tags=note.tags,
        text=text,
        wikilinks=note.wikilinks,
        char_start=start,
        char_end=end,
    )


if __name__ == "__main__":
    from pathlib import Path

    from core.config import load_config
    from core.ingest.parser import parse_note
    from core.models import VaultFile

    path = Path(
        "~/Documents/obsidian/knowledge/01 Notes/Lecture 2 - Client Server Architecture and the World Wide Web.md"
    ).expanduser()

    vault_file = VaultFile(
        path=path,
        mtime=path.stat().st_mtime,
    )

    note = parse_note(
        vault_file, load_config("~/Documents/projects/oxidian/config.example.toml")
    )

    chunked_note = chunk_note(note)

    __import__("pprint").pprint(chunked_note)
