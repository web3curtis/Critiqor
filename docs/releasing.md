# Publishing Critiqor

The source tree currently declares version `0.2.19`; PyPI must be checked
separately before calling a release published. PyPI does not allow replacing a
distribution file with the same filename after upload.

1. Update the version in `pyproject.toml`, `critiqor/__init__.py`, and
   `critiqor/core_engine_dashboard/package.json` together. Add a changelog entry.
2. Build the dashboard if its source changed, then sanitize its output using
   the dashboard `build` script.
3. Run the checks below from a clean checkout:

   ```bash
   python3 -m pip install --upgrade build
   python3 -m unittest discover -s tests -p 'test_*.py' -q
   python3 -m build
   python3 scripts/verify_release_artifacts.py dist/*.whl dist/*.tar.gz
   python3 scripts/audit_release_artifacts.py dist/*.whl dist/*.tar.gz
   ```

4. Install the built wheel in a fresh environment and check `critiqor help`
   and `critiqor doctor`. Publish only after the release checks pass.

The `0.2.19` tree includes the `0.2.7` through `0.2.18` public CLI, memory,
dashboard, and WebMCP work. It is **not** a complete replacement for every
historical release: the `0.1.0` `Critiqor` wrapper, `CritiqorResult`, benchmark,
tracer, and platform APIs are absent. Keep older distributions available for
users of those APIs until a compatibility decision is made. Version history is
also useful for reproducible installations.

## Version organization

Keep every published PyPI version available. A normal unpinned
`pip install critiqor` resolves to the current release, while the retained
history protects reproducible and legacy installations.

Create one annotated Git tag for each published version, using the exact
version (for example, `v0.2.18`) and pointing to the source commit used for its
artifacts. Do not use one Git tag for multiple versions: a tag identifies one
commit. Group related patch releases under a single series heading in
`CHANGELOG.md` instead.
