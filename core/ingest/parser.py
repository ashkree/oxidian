import re
from typing import Any

import frontmatter

from core.models import Heading, ParsedNote, VaultFile

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_note(note: VaultFile, config: dict[str, Any]) -> ParsedNote:
    post = frontmatter.load(str(note.path))

    tags = extract_tags(post.metadata)
    note_type = extract_note_type(tags)
    wikilinks = extract_wikilinks(post.content)
    content = clean_content(post.content)
    headings = extract_headings(content)

    frontmatter_blacklist = config.get("parser", {}).get("frontmatter_blacklist", [])

    return ParsedNote(
        title=note.path.stem,
        note_type=note_type,
        tags=tags,
        wikilinks=wikilinks,
        content=content,
        frontmatter=extract_frontmatter(post.metadata, frontmatter_blacklist),
        source_path=note.path,
        headings=headings,
    )


# ---------------------------------------------------------------------------
# Extraction — run on raw content before cleaning
# ---------------------------------------------------------------------------


def extract_frontmatter(
    metadata: dict[str, Any], blacklist: list[str]
) -> dict[str, Any]:
    """Filter frontmatter metadata, removing any keys in the blacklist.

    Blacklist is configured via [parser] frontmatter_blacklist in config.toml.
    """
    return {k: v for k, v in metadata.items() if k not in blacklist}


def extract_tags(metadata: dict[str, Any]) -> set[str]:
    """Pull tags from frontmatter. Normalizes to a flat set of strings."""
    raw: list[str] = metadata.get("tags") or []
    return {tag.strip().lstrip("#") for tag in raw if tag}


def extract_note_type(tags: set[str]) -> str | None:
    """Derive note type from tags ending in '_note' (e.g. 'literature_note')."""
    return next((tag for tag in tags if tag.endswith("_note")), None)


def extract_wikilinks(raw_content: str) -> set[str]:
    """
    Extract all wikilink targets from raw markdown before cleaning.

    [[Note Name]]        → "Note Name"
    [[Note Name|Alias]]  → "Note Name"  (target, not alias)
    ![[image.png]]       → ignored
    """
    # Aliased links — capture the target (left side)
    aliased = re.findall(r"(?<!!)\[\[([^\]|]+)\|[^\]]*\]\]", raw_content)
    # Plain links
    plain = re.findall(r"(?<!!)\[\[([^\]|]+)\]\]", raw_content)
    return {link.strip() for link in aliased + plain}


def extract_headings(cleaned_content: str) -> list[Heading]:
    """
    Extract headings (H1-H6) from cleaned content with their char positions.

    Must run after cleanContent so char_pos values are accurate for chunking.
    Headings are intentionally left untouched by cleanContent for this reason.
    """
    headings: list[Heading] = []
    for match in re.finditer(r"^(#{1,6})\s+(.+)$", cleaned_content, re.MULTILINE):
        headings.append(
            Heading(
                level=len(match.group(1)),
                text=match.group(2).strip(),
                char_pos=match.start(),
            )
        )
    return headings


# ---------------------------------------------------------------------------
# Cleaning — transforms raw markdown into plain text for embedding
# Headings are intentionally preserved so the chunker can use them.
# ---------------------------------------------------------------------------


def clean_content(content: str) -> str:
    content = strip_dataview_blocks(content)
    content = transform_wikilinks(content)
    content = transform_callouts(content)
    content = strip_markdown_syntax(content)
    content = normalize_whitespace(content)
    return content


def strip_dataview_blocks(content: str) -> str:
    """Remove ```dataview ... ``` code blocks."""
    return re.sub(r"```dataview\b.*?```", "", content, flags=re.DOTALL | re.IGNORECASE)


def transform_wikilinks(content: str) -> str:
    """
    ![[image.png]]      → (removed)
    [[Note|Alias]]      → Alias
    [[Note]]            → Note
    """
    content = re.sub(r"!\[\[.*?\]\]", "", content)
    content = re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", content)
    content = re.sub(r"\[\[(.*?)\]\]", r"\1", content)
    return content


def transform_callouts(content: str) -> str:
    """
    Convert Obsidian callouts to plain prefixed text.

    > [!WARNING] optional title    →    Warning: optional title
    > body text                         body text
    """
    return re.sub(
        r"^>\s*\[!([^\]]+)\][^\S\n]*(.*)\n((?:^>.*\n?)*)",
        lambda m: (
            (
                f"{m.group(1).strip().capitalize()}: {m.group(2).strip()}\n"
                if m.group(2).strip()
                else f"{m.group(1).strip().capitalize()}:\n"
            )
            + re.sub(r"^>\s?", "", m.group(3), flags=re.MULTILINE).strip()
        ),
        content,
        flags=re.MULTILINE,
    )


def strip_markdown_syntax(content: str) -> str:
    """Strip remaining markdown syntax, preserving underlying text."""
    # Bold / italic / strikethrough
    content = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", content)
    content = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", content)
    content = re.sub(r"~~(.+?)~~", r"\1", content)

    # Inline code
    content = re.sub(r"`(.+?)`", r"\1", content)

    # Markdown links → label only
    content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)
    # Bare URLs
    content = re.sub(r"https?://\S+", "", content)
    # Inline HTML
    content = re.sub(r"<[^>]+>", "", content)
    # Horizontal rules
    content = re.sub(r"^[-*_]{3,}\s*$", "", content, flags=re.MULTILINE)
    # Remaining blockquote markers (non-callout)
    content = re.sub(r"^>\s?", "", content, flags=re.MULTILINE)
    # List markers (-, *, +, 1.)
    content = re.sub(r"^[\s]*[-*+]\s+", "", content, flags=re.MULTILINE)
    content = re.sub(r"^[\s]*\d+\.\s+", "", content, flags=re.MULTILINE)
    # Checkboxes
    content = re.sub(r"\[[ xX]\]\s*", "", content)
    return content


def normalize_whitespace(content: str) -> str:
    """
    - Normalize line endings to \\n
    - Strip trailing whitespace per line
    - Collapse inline runs of spaces/tabs to a single space
    - Collapse 3+ consecutive blank lines to one blank line
    """
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in content.split("\n")]
    content = "\n".join(lines)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()
