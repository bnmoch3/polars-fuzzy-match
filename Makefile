.SILENT:
.DEFAULT_GOAL:=dev

.PHONY: dev build-dev clean format lint test

dev: build-dev
	uv run python examples/usage.py

build-dev: .build-dev

.build-dev: $(wildcard src/*.rs) $(wildcard Cargo.toml) $(wildcard Cargo.lock)
	uv run maturin develop
	touch .build-dev

format:
	uv run ruff format polars_fuzzy_match/ examples/ tests/ README.md
	command -v cargo >/dev/null 2>&1 && cargo fmt --all || echo "⚠ cargo not in PATH; skipping rustfmt"

lint:
	uv run ruff check polars_fuzzy_match/ examples/ tests/
	command -v cargo >/dev/null 2>&1 && cargo clippy --all-targets -- -D warnings || echo "⚠ cargo not in PATH; skipping clippy"

test: build-dev
	uv run pytest tests/

clean:
	rm -f .build-dev
	command -v cargo >/dev/null 2>&1 && cargo clean || true
