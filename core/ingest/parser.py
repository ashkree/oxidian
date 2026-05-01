from pathlib import Path
from typing import Any

import frontmatter

from core.models import ParsedNote, VaultFile


def parseNote(note: VaultFile) -> ParsedNote:

    post = frontmatter.load(note.path)

    __import__("pprint").pprint(post.metadata)

    parsed_note = ParsedNote(title=note.path.stem)

    return parsed_note


def extractTags(metatags: dict[str, Any], content: str):

    return


if __name__ == "__main__":
    path = Path("~/Documents/Projects/oxidian/data/sample/Compositor.md").expanduser()
    vault_file = VaultFile(
        path=path,
        mtime=path.stat().st_mtime,
    )

    parseNote(vault_file)
