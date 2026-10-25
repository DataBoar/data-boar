# boar_fast_filter (Rust + PyO3)

High-speed candidate pre-filter for Data Boar Pro+.

Current suspects include:

- CPF-like strings
- email-like strings
- credit card candidates that pass Luhn (13-19 digits)

## Build (dev)

From repository root (`maturin` ships as a dev dependency, so `uv run` finds it in the `.venv` — no separate `pip install`):

```bash
uv run maturin develop --manifest-path rust/boar_fast_filter/Cargo.toml --release
```

This makes `boar_fast_filter` importable in the active Python environment.

Windows helper:

```powershell
.\scripts\build-rust-prefilter.ps1
```

Target override example:

```powershell
.\scripts\build-rust-prefilter.ps1 -Target x86_64-pc-windows-msvc
```

## Quick smoke

```python
from boar_fast_filter import FastFilter
f = FastFilter()
print(f.filter_batch(["clean", "cpf 390.533.447-05", "mail a@example.test"]))
```
