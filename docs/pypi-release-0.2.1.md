# Publish Critiqor 0.2.1 to PyPI

This release publishes the multi-agent commands and configuration UX:

- `critiqor agents`
- `critiqor config`
- `critiqor monitor openclaw`
- `critiqor monitor cc`
- `critiqor monitor codex`
- `critiqor monitor <custom-framework>`

PyPI versions cannot be replaced or reused. Confirm that `0.2.1` has not already been published before continuing.

## 1. Prepare a clean environment

From the repository root:

```bash
python3 -m venv .venv-release
source .venv-release/bin/activate
python3 -m pip install --upgrade build twine
```

On Windows PowerShell, activate the environment with:

```powershell
.venv-release\Scripts\Activate.ps1
```

## 2. Run the tests

```bash
python3 -m unittest discover -s tests -v
```

All tests must pass before uploading.

## 3. Build only version 0.2.1

Remove locally generated packages from earlier builds, then create fresh artifacts:

```bash
rm -rf build dist critiqor.egg-info
python3 -m build
```

Windows PowerShell equivalent:

```powershell
Remove-Item -Recurse -Force build, dist, critiqor.egg-info -ErrorAction SilentlyContinue
python -m build
```

The build must create:

```text
dist/critiqor-0.2.1-py3-none-any.whl
dist/critiqor-0.2.1.tar.gz
```

## 4. Validate the artifacts

```bash
python3 -m twine check dist/critiqor-0.2.1*
```

Both artifacts should report `PASSED`.

## 5. Configure a PyPI API token

In PyPI, open **Account settings → API tokens**, create a token scoped to the `critiqor` project, and keep it private.

The safest interactive upload is:

```bash
python3 -m twine upload \
  dist/critiqor-0.2.1.tar.gz \
  dist/critiqor-0.2.1-py3-none-any.whl
```

When prompted, enter:

```text
Username: __token__
Password: <the complete token beginning with pypi->
```

Do not commit the token, place it in command history, or paste it into an issue or chat.

## 6. Verify the public release

Wait briefly for PyPI's index to update, then install into a clean environment:

```bash
python3 -m venv /tmp/critiqor-0.2.1-check
source /tmp/critiqor-0.2.1-check/bin/activate
python3 -m pip install --no-cache-dir critiqor==0.2.1
critiqor help
```

Confirm that the help output lists `agents`, `config`, and `monitor <framework>`. Then run:

```bash
critiqor agents
```

Confirm that OpenClaw, Claude Code, Codex CLI, and custom framework configuration are available.

The public release page is:

```text
https://pypi.org/project/critiqor/0.2.1/
```

## 7. Record the Git release

After PyPI verification succeeds:

```bash
git tag -a v0.2.1 -m "Critiqor 0.2.1"
git push origin v0.2.1
```

Do not create the tag until the PyPI upload has succeeded.
