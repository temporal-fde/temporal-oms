# OMS Python

`Fulfillments` concerns will be extended and implemented here.

## Setup

### Prerequisites

- [`buf`](https://buf.build/docs/installation) — protobuf toolchain used for code generation
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager

### uv Environment

Run from the `python/` directory:

```bash
cd python
uv venv
uv add protobuf-to-pydantic
uv add --dev mypy-protobuf
```

`protobuf-to-pydantic` installs the `protoc-gen-protobuf-to-pydantic` binary into `python/.venv/bin/`. The root `buf.gen.yaml` references it by relative path so no PATH manipulation is needed when generating.

### Generating Protobuf/Pydantic Types

From the **repository root**:

```bash
buf generate
```

Generated files are written to:

- `python/generated/` — standard protobuf Python stubs (`.py` / `.pyi`)
- `python/generated/pydantic/` — Pydantic models derived from `.proto` definitions
