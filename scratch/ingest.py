import marimo

__generated_with = "0.23.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from core.config import load_config
    config = load_config("./tests/test_config.toml")
    return (config,)


@app.cell
def _():
    # cell 2 — vault file
    from pathlib import Path
    from core.models import VaultFile

    path = Path("./tests/test_note.md")
    vault_note = VaultFile(path=path, mtime=path.stat().st_mtime)
    return (vault_note,)


@app.cell
def _(config, vault_note):
    # cell 3 — parser
    from core.ingest.parser import parse_note
    parsed_note = parse_note(vault_note, config)
    parsed_note
    return (parsed_note,)


@app.cell
def _(parsed_note):
    # cell 4 — chunker
    from core.ingest.chunker import chunk_note
    chunks = chunk_note(parsed_note)

    for chunk in chunks:
        __import__("pprint").pprint(chunk)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
