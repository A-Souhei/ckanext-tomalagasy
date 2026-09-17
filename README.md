# ckanext-tomalagasy

Malagasy for CKAN and every installed extension. Enabling the plugin makes
Malagasy (`mg`) the default language, with French and English as the
alternatives (`/fr/…`, `/en/…`).

Where Malagasy has no established word, the translation uses French. Any string
not yet translated falls back to CKAN's French catalog, and only then to
English. Dates — both the server-rendered ones and the JavaScript rewrite into
the viewer's timezone — use CLDR Malagasy.

> The translations were produced with an LLM from a fixed glossary and have
> **not been reviewed by a native speaker yet**. Corrections are very welcome.

## Requirements

| CKAN | Python | Status |
|---|---|---|
| 2.11 | 3.10 | tested with 2.11.6 |
| 2.10, 2.12 | | untested |

## Installation

```sh
pip install -e git+https://github.com/A-Souhei/ckanext-tomalagasy.git#egg=ckanext-tomalagasy
python -m ckanext.tomalagasy.catalog build
```

Install it **editable** (`-e`), like CKAN's Docker images install their own
extensions: a regular wheel lands in `site-packages/ckanext`, which CKAN's
pre-seeded `ckanext` namespace never searches.

Build the catalog **after** installing every other extension: strings are
harvested from whatever is installed at that moment. Then enable the plugin,
before `envvars` so explicit environment overrides still win:

```ini
ckan.plugins = … tomalagasy envvars
```

The plugin sets `ckan.i18n_directory`, `ckan.locale_default = mg`,
`ckan.locales_offered` and `ckan.locale_order` itself, and refuses to start
without a built catalog.

Behind uwsgi, also run `ckan translation js` at startup. CKAN only builds its
JavaScript translations under `ckan run`; without them `/api/i18n/<lang>`
answers `{}` and every string rendered by JavaScript stays English in any
language.

## How it works

CKAN only offers locales that exist as folders in `ckan.i18n_directory`, which
is also where it loads the core `ckan` catalog from. `catalog build` writes such
a folder — a complete `mg` catalog (Malagasy, with French for anything
untranslated) plus the `fr` one — and the plugin points `ckan.i18n_directory`
at it. There is no monkeypatching: Flask-Babel merges every catalog into one
dictionary per request, so a single catalog covers core and extensions alike.

moment.js ships no Malagasy, so the plugin also registers a CLDR-based `mg`
moment locale; otherwise the client-side date rewrite would print English month
names on Malagasy pages.

## Translating

`ckanext/tomalagasy/translations/mg.po` is the only source of truth; the
compiled `i18n/` folder is generated and not committed.

```sh
python -m ckanext.tomalagasy.catalog update           # add strings from new CKAN/extension versions
python -m ckanext.tomalagasy.catalog stats --by-file  # coverage, and where the gaps are
python -m ckanext.tomalagasy.catalog build            # compile; fails on broken placeholders
```

Extensions that ship a `.pot` contribute it; the others are extracted from
their Python, JavaScript and templates. `build` rejects any translation that
adds, drops or reorders a `%(name)s`, `%s` or `{name}` placeholder: those raise
at render time and take the page down.

### Glossary

| English | Used | |
|---|---|---|
| Dataset | angon-drakitra | |
| Resource | ressource | FR |
| Dashboard | tableau de bord | FR |
| Metadata | métadonnées | FR |
| API token | jeton API | FR |
| Data | angona | |
| Organization | fikambanana | |
| Group | vondrona | |
| Member / Editor / Admin | mpikambana / mpanitsy / mpitantana | |
| Sysadmin | mpitantana ny rafitra | |
| Collaborator | mpiara-miasa | |
| User / Username | mpampiasa / anaran'ny mpampiasa | |
| Tag | teny fanalahidy | |
| License | fahazoan-dalana | |
| Format | endrika | |
| View (resource view) | fijery | |
| Data Dictionary | rakibolan'ny angona | |
| Field / Value | saha / sanda | |
| Search / Filter | hitady / sivana | |
| Log in / Log out / Register | hiditra / hivoaka / hisoratra anarana | |
| Password / Email | tenimiafina / mailaka | |
| Private / Public | manokana / ho an'ny rehetra | |
| Draft | drafitra | |

## License

ckanext-tomalagasy — Malagasy translation of CKAN
Copyright (C) 2026 Toavina and contributors

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version — the same license as CKAN itself.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with this program (see [LICENSE](LICENSE)). If not, see
<https://www.gnu.org/licenses/>.
