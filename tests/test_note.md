---
tags:
  - literature_note
  - python
  - testing
author: Test Author
date: 2024-01-01
secret: this should be blacklisted
---

This is intro text before any heading. It should appear in its own chunk with no heading annotation.

Another intro paragraph. It references [[Some Other Note]] and [[Note With Alias|Alias]] as wikilinks.

## Background

This is the background section. It has a few paragraphs of plain prose.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Here is some **bold text** and some *italic text* and some ~~strikethrough~~ and some `inline code` that should all be cleaned.

A line with a [markdown link](https://example.com) and a bare URL https://example.com that should both be stripped.

## Code Examples

Here is some prose before the code block.

```python
def hello(name: str) -> str:
    return f"Hello, {name}"

# This is a comment
x = hello("world")
print(x)
```

Here is some prose after the code block.

```bash
pip install oxidian
python main.py
```

## Tables

Here is a table that should be kept whole.

| Column A | Column B | Column C |
|----------|----------|----------|
| Row 1A   | Row 1B   | Row 1C   |
| Row 2A   | Row 2B   | Row 2C   |
| Row 3A   | Row 3B   | Row 3C   |

Some prose after the table.

Here is a second table.

| Name   | Age | Role     |
|--------|-----|----------|
| Alice  | 30  | Engineer |
| Bob    | 25  | Designer |

## Callouts

> [!NOTE] This is a note callout
> The body of the note callout goes here.
> It can span multiple lines.

> [!WARNING] Watch out
> This is a warning callout body.

> [!TIP]
> A tip with no title text.

## Lists

Here is an unordered list:

- First item
- Second item
- Third item with **bold**

Here is an ordered list:

1. First ordered item
2. Second ordered item
3. Third ordered item

Here is a task list:

- [x] Completed task
- [ ] Incomplete task
- [x] Another completed task

## Wikilinks and Embeds

A paragraph with [[Plain Wikilink]] and [[Target Note|Display Alias]] and an embed ![[image.png]] that should be removed.

Another paragraph with multiple links: [[Note One]], [[Note Two]], [[Note Three|Alias Three]].

## Nested Headings

### Sub-section One

This is content under a level-three heading. It should carry heading_level=3 and heading="Sub-section One".

Some more prose here to give it some body.

### Sub-section Two

Another level-three section with its own content.

```javascript
const greet = (name) => `Hello, ${name}`;
console.log(greet("world"));
```

#### Deep Heading

This is under a level-four heading. Deeper nesting to test heading level propagation.

## Blockquotes

A regular blockquote that is not a callout:

> This is a regular blockquote.
> It spans multiple lines.
> It should have the > markers stripped.

## Mixed Content

A section that mixes prose, a code block, a table, and a callout all together.

Some opening prose in a mixed section.

```sql
SELECT *
FROM chunks
WHERE heading = 'Mixed Content'
ORDER BY char_start ASC;
```

| Key     | Value       |
|---------|-------------|
| model   | cl100k_base |
| size    | 512         |
| overlap | 64          |

> [!INFO] Summary
> This section intentionally mixes content types to stress-test segmentation.

Closing prose for the mixed section.
