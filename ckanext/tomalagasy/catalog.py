"""Maintain and compile the Malagasy catalog.

    python -m ckanext.tomalagasy.catalog update   add new strings to translations/mg.po
    python -m ckanext.tomalagasy.catalog build    compile i18n/ for CKAN
    python -m ckanext.tomalagasy.catalog stats    coverage, optionally --by-file

Needs no CKAN config, so it runs at image build time. Strings come from CKAN core
and from every installed extension: its own .pot when it ships one, otherwise
extracted from its source the way `pybabel extract` would.
"""
from __future__ import annotations

import argparse
import collections
import re
import shutil
import sys
from importlib.metadata import entry_points
from importlib.util import find_spec
from pathlib import Path
from typing import Iterable, Optional

import ckan
from babel.messages.catalog import Catalog, Message
from babel.messages.extract import extract_from_dir
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po, write_po

HERE = Path(__file__).parent
SOURCE_PO = HERE / "translations" / "mg.po"
OUTPUT_DIR = HERE / "i18n"
CORE_I18N = Path(ckan.__file__).parent / "i18n"
CORE_EXTENSIONS = Path(ckan.__file__).parent.parent / "ckanext"
DOMAIN = "ckan"
FALLBACK_LOCALE = "fr"

EXTRACTORS = [
    ("**/tests/**", "ignore"),
    ("**.py", "python"),
    ("**.js", "javascript"),
    ("**/templates/**.html", "ckan"),
]

NAMED = re.compile(r"%\((\w+)\)[#0\- +]*\d*(?:\.\d+)?[a-zA-Z]")
POSITIONAL = re.compile(r"%[#0\- +]*\d*(?:\.\d+)?[diouxXeEfFgGcrs]")
BRACE = re.compile(r"\{[^{}]*\}")


def _read(path: Path, locale: Optional[str] = None) -> Catalog:
    with path.open("rb") as f:
        return read_po(f, locale=locale)


def _write_po(path: Path, catalog: Catalog) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        # Line numbers churn on every CKAN upgrade; file names are enough context.
        write_po(f, catalog, width=0, include_lineno=False)


def _write_mo(path: Path, catalog: Catalog) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        write_mo(f, catalog)


def _is_translated(message: Message) -> bool:
    if not message.id or message.fuzzy:
        return False
    if isinstance(message.string, str):
        return bool(message.string)
    return bool(message.string) and all(message.string)


def extension_dirs() -> list[Path]:
    """Package directories of installed third-party CKAN extensions."""
    found: dict[Path, None] = {}
    for ep in entry_points(group="ckan.plugins"):
        module = ep.value.split(":")[0]
        try:
            spec = find_spec(module)
        except Exception:
            continue
        if spec is None or not spec.origin:
            continue
        parts = Path(spec.origin).parts
        if "ckanext" not in parts or "tests" in parts:
            continue
        root = parts.index("ckanext")
        package = Path(*parts[: root + 2])
        if package == HERE or CORE_EXTENSIONS in package.parents:
            continue
        found[package] = None
    return list(found)


def template() -> Catalog:
    """Every string CKAN core and the installed extensions can show."""
    tpl = Catalog(domain=DOMAIN, fuzzy=False)
    _add_all(tpl, _read(CORE_I18N / "ckan.pot"))
    for package in extension_dirs():
        pots = sorted((package / "i18n").glob("*.pot"))
        if pots:
            for pot in pots:
                _add_all(tpl, _read(pot))
            continue
        prefix = "/".join(package.parts[-2:])
        for filename, lineno, msgid, comments, context in extract_from_dir(package, EXTRACTORS):
            tpl.add(msgid, locations=[(f"{prefix}/{filename}", lineno)],
                    auto_comments=comments, context=context)
    return tpl


def _add_all(target: Catalog, source: Iterable[Message]) -> None:
    for message in source:
        if message.id:
            target[message.id] = Message(
                message.id, "", locations=message.locations, flags=message.flags,
                auto_comments=message.auto_comments, context=message.context)


def fallback() -> Catalog:
    """French strings from core and extensions; an extension's own wins over core."""
    paths = [CORE_I18N / FALLBACK_LOCALE / "LC_MESSAGES" / "ckan.po"]
    for package in extension_dirs():
        paths += sorted((package / "i18n" / FALLBACK_LOCALE / "LC_MESSAGES").glob("*.po"))
    merged = Catalog(locale=FALLBACK_LOCALE, domain=DOMAIN)
    for path in paths:
        if path.is_file():
            for message in _read(path, locale=FALLBACK_LOCALE):
                if _is_translated(message):
                    merged[message.id] = message
    return merged


def _placeholders(text: str) -> tuple[list[str], list[str], list[str]]:
    text = text.replace("%%", "")
    named = sorted(NAMED.findall(text))
    positional = POSITIONAL.findall(NAMED.sub("", text))
    return named, positional, sorted(BRACE.findall(text))


def placeholder_problems(message: Message) -> list[str]:
    """Placeholders a translation adds, drops or reorders.

    Any of these fails at render time — an unknown %(name)s or {name} raises
    KeyError, a different number of %s raises TypeError — so the build refuses
    them instead of shipping a catalog that crashes pages.
    """
    ids = [message.id] if isinstance(message.id, str) else list(message.id)
    strings = [message.string] if isinstance(message.string, str) else list(message.string)
    expected = [_placeholders(i) for i in ids]
    problems = []
    for index, string in enumerate(strings):
        named, positional, braces = _placeholders(string)
        if len(ids) == 1:
            want_named, want_positional, want_braces = expected[0]
            ok = (named == want_named and positional == want_positional
                  and braces == want_braces)
        else:
            # A singular form may leave the count out; it must not invent one.
            allowed_named = set(expected[0][0]) | set(expected[1][0])
            allowed_braces = set(expected[0][2]) | set(expected[1][2])
            ok = (set(named) <= allowed_named and set(braces) <= allowed_braces
                  and positional in (expected[0][1], expected[1][1]))
        if not ok:
            problems.append(f"msgstr[{index}] {string!r} does not match the placeholders of {ids[0]!r}")
    return problems


def update() -> None:
    tpl = template()
    catalog = (_read(SOURCE_PO, locale="mg") if SOURCE_PO.exists()
               else Catalog(locale="mg", domain=DOMAIN, project="ckanext-tomalagasy",
                            version="0.1.0", copyright_holder="Sahan'Aina",
                            language_team="Malagasy", fuzzy=False,
                            header_comment="# Malagasy translation of CKAN and its extensions.\n"
                                           "# French is used where Malagasy has no established word;\n"
                                           "# untranslated strings fall back to CKAN's French catalog."))
    catalog.update(tpl, no_fuzzy_matching=True, update_creation_date=False)
    _write_po(SOURCE_PO, catalog)
    print(f"updated {SOURCE_PO}")
    stats(tpl, catalog)


def build() -> None:
    tpl, source, fr = template(), _read(SOURCE_PO, locale="mg"), fallback()

    problems = [p for m in source if _is_translated(m) for p in placeholder_problems(m)]
    if problems:
        print(f"{len(problems)} broken translation(s) in {SOURCE_PO}:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    mg = Catalog(locale="mg", domain=DOMAIN, fuzzy=False)
    for entry in tpl:
        if not entry.id:
            continue
        for candidate in (source.get(entry.id, entry.context), fr.get(entry.id, entry.context)):
            if candidate is not None and _is_translated(candidate):
                mg[entry.id] = Message(entry.id, candidate.string, flags=entry.flags,
                                       context=entry.context)
                break

    french = Catalog(locale=FALLBACK_LOCALE, domain=DOMAIN, fuzzy=False)
    for message in fr:
        if message.id:
            french[message.id] = Message(message.id, message.string, flags=message.flags,
                                         context=message.context)

    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    # CKAN's JS translation builder reads the .pot to learn which strings the
    # JavaScript uses, and the per-locale .po files for their text.
    _write_po(OUTPUT_DIR / f"{DOMAIN}.pot", tpl)
    for catalog in (mg, french):
        base = OUTPUT_DIR / str(catalog.locale) / "LC_MESSAGES" / DOMAIN
        _write_po(base.with_suffix(".po"), catalog)
        _write_mo(base.with_suffix(".mo"), catalog)
    print(f"built {OUTPUT_DIR}")
    stats(tpl, source, fr)


def stats(tpl: Optional[Catalog] = None, source: Optional[Catalog] = None,
          fr: Optional[Catalog] = None, by_file: bool = False) -> None:
    tpl = tpl if tpl is not None else template()
    source = source if source is not None else _read(SOURCE_PO, locale="mg")
    fr = fr if fr is not None else fallback()

    counts = collections.Counter()
    todo_by_file: collections.Counter = collections.Counter()
    for entry in tpl:
        if not entry.id:
            continue
        counts["total"] += 1
        mg = source.get(entry.id, entry.context)
        if mg is not None and _is_translated(mg):
            counts["mg"] += 1
            continue
        french = fr.get(entry.id, entry.context)
        counts["fr" if french is not None and _is_translated(french) else "en"] += 1
        for filename, _ in entry.locations[:1]:
            todo_by_file[filename] += 1

    total = counts["total"] or 1
    print(f"{counts['total']} strings: "
          f"{counts['mg']} Malagasy ({100 * counts['mg'] / total:.1f}%), "
          f"{counts['fr']} French fallback, {counts['en']} still English")
    if by_file:
        for filename, n in todo_by_file.most_common(40):
            print(f"  {n:4d}  {filename}")


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m ckanext.tomalagasy.catalog")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("update", help="add new strings to translations/mg.po")
    commands.add_parser("build", help="compile i18n/ for CKAN")
    stats_parser = commands.add_parser("stats", help="translation coverage")
    stats_parser.add_argument("--by-file", action="store_true",
                              help="untranslated strings per file (by first location)")
    args = parser.parse_args(argv)

    if args.command == "update":
        update()
    elif args.command == "build":
        build()
    else:
        stats(by_file=args.by_file)


if __name__ == "__main__":
    main()
