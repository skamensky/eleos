from __future__ import annotations

import argparse
import json
from pathlib import Path

from eleos.api.app import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate OpenAPI schema JSON from FastAPI app.")
    parser.add_argument(
        "--output",
        default="docs/eleos-openapi.json",
        help="Path to write OpenAPI JSON",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    output_path.write_text(
        json.dumps(schema, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"wrote OpenAPI schema: {output_path}")


if __name__ == "__main__":
    main()
