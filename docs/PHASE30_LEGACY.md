# Phase 30 — Legacy Windows builds

**Status:** Documented track for **3.2.x**; modern path is production-validated.

| Track | Python | OS target | Build |
|-------|--------|-----------|--------|
| Modern | 3.11+ | Windows 10/11, Server 2016+ | `scripts/build_modern.bat` |
| Legacy | 3.8 | Windows 7 SP1 / Server 2008 R2 | `scripts/build_legacy.bat` (operator-guided) |

## Legacy procedure

1. Install Python 3.8 x64 on a Win7 SP1 test machine.
2. `py -3.8 -m venv .venv-legacy`
3. `.venv-legacy\Scripts\pip install -r requirements\legacy.txt`
4. Resolve any API drift between pydantic v1 and modern `app/` (dedicated branch recommended).
5. PyInstaller spec from `scripts/build_windows.bat` with legacy venv activated.
6. Fill the sign-off table in `docs/WINDOWS_EXE_QA.md` on real hardware before claiming support.

`requirements/legacy.txt` pins indicative versions only — **not validated** until the test log exists.

Modern operators should use `docs/WINDOWS_EXE_QA.md` and `docs/NSSM_SERVICE.md`.
