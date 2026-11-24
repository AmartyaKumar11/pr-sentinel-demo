# PR Sentinel Demo App

Small Python app used as the monitoring target for PR Sentinel demos.

## Usage

Run the tests from the repository root.

- Install pytest if needed: `python -m pip install pytest`
- Run the tests: `pytest`

## Troubleshooting

- **`ModuleNotFoundError: No module named 'pytest'`** — **Cause:** pytest is not installed in the active Python environment. **Fix:** run `python -m pip install pytest`, then retry `pytest`.
- **`ModuleNotFoundError` for the demo app or its tests** — **Cause:** `pytest` was started outside the repository root, so Python cannot resolve local imports. **Fix:** `cd` to the repository root (see Usage), then run `pytest` again.
