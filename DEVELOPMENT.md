# Development

The project uses a modern `pyproject.toml` build and installs its runtime dependencies
from there. To work on it locally:

```
$ python -m venv .venv
$ source .venv/bin/activate
$ python -m pip install -e ".[dev]"
$ pre-commit install
```

Build a source distribution and wheel with:

```
$ python -m build
```

## Publishing

Publishing to PyPI is automated by `.github/workflows/publish.yml`. Pushing a tag such
as `v1.2.0` builds the distributions, runs `twine check`, and uploads them with PyPI
trusted publishing. The GitHub `Release` environment must be configured for trusted
publishing before the first release.

### Set up trusted publishing

1. In the GitHub repository, open **Settings -> Environments**, create an environment
   named exactly `Release`, and save it. No environment secrets are needed because
   trusted publishing uses OIDC instead of a PyPI token.

2. On PyPI, sign in to the account that owns the `dl_coursera` project, open
   **Publishing**, and add a new trusted publisher with these values:

   * Owner: `FLZ101`
   * Repository name: `dl_coursera`
   * Workflow name: `publish.yml`
   * Environment name: `Release`

3. Trigger a release by pushing a version tag:

   ```
   git tag v1.2.0
   git push origin v1.2.0
   ```

   You can also run **Actions -> Publish to PyPI -> Run workflow** manually.

To test the release pipeline without touching the real project, add the same trusted
publisher on TestPyPI and temporarily point the publish action at
`https://test.pypi.org/legacy/`.

### Publish locally

Install the build and upload tools in the active virtual environment:

```
$ python -m pip install --upgrade build twine
```

Clean any previous build output and create fresh distributions:

```
$ rm -rf build dist dl_coursera.egg-info
$ python -m build
$ twine check --strict dist/*
```

Upload to TestPyPI first to verify the package metadata and contents:

```
$ python -m twine upload --repository testpypi dist/*
```

When the test upload looks good, publish to PyPI:

```
$ python -m twine upload dist/*
```

For local publishing you need a PyPI API token or account credentials for the
`dl_coursera` project. With an API token, use `__token__` as the username and the
token as the password:

```
$ TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-... python -m twine upload dist/*
```

You can configure `twine` repositories and credentials in `~/.pypirc` instead of
passing them on every command.
