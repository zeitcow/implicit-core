# Installation

Implicit Core 1.0.0 is the stable initial release, licensed under Apache-2.0. Python 3.11+ is required; Core needs no runtime dependencies. Use a dedicated virtual environment:

```console
pip install implicit-ai
implicit --version
implicit --help
implicit-mcp --help
```

The distribution is `implicit-ai`; the import is `implicit`. Avoid the unrelated `implicit` distribution in the same environment because namespaces may collide.

## Manual artifact or source installation

The [GitHub Release](https://github.com/zeitcow/implicit-core/releases/tag/v1.0.0) supplies verified wheel and sdist assets. Install a downloaded wheel with `python -m pip install --no-index PATH_TO_WHEEL`. From the public source root or an extracted sdist:

```console
python -m pip install hatchling
python -m hatchling build
python -m pip install --no-index dist/implicit_ai-1.0.0-py3-none-any.whl
```

Development checks require the dev extra (`python -m pip install ".[dev]"`). Package builds need Hatchling; neither is a Core runtime dependency. Research dependencies are absent from public metadata. Uninstalling does not erase journals or content; see SECURITY.md. Completed platform validation is recorded in release evidence; a CI configuration alone does not establish a completed run.
