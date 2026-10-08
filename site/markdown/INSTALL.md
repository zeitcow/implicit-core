# Installation

Implicit Core 1.0.0rc2 is an initial public preview. Python 3.11+ is required; Core needs no runtime dependencies. Locally rehearsed Python/OS versions are recorded in the audit; a CI configuration does not establish completed platform validation.

From the public source root:

```console
python -m pip install hatchling
python -m hatchling build
python -m pip install --no-index dist/implicit_ai-1.0.0rc2-py3-none-any.whl
implicit --version
implicit --help
implicit-mcp --help
```

Or install the supplied wheel with `python -m pip install --no-index PATH_TO_WHEEL`. Extract the sdist in a fresh directory and run `python -m hatchling build` to build from it. Rehearsals use noneditable installation.

The PyPI command is `python -m pip install --pre implicit-ai` when 1.0.0rc2 is listed on PyPI. The [GitHub Release](https://github.com/zeitcow/implicit-core/releases/tag/v1.0.0rc2) supplies the canonical wheel and sdist independently of PyPI. The module is implicit; avoid the unrelated implicit distribution in the same environment because namespaces may collide. Use a dedicated virtual environment.

Development checks require the dev extra. Package builds need Hatchling; neither is a Core runtime dependency. Research dependencies are absent from public metadata. Uninstalling does not erase journals or content; see SECURITY.md.
