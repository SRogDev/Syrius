"""Generate the TypeScript API client types from the live OpenAPI schema.

Usage:
    uv run --project apps/api python scripts/gen_api_client.py

Reads ``syrius_api.main:app``'s OpenAPI document (no server needed)
and writes ``packages/api-client/src/types.ts`` — real generated
types, not hand-written guesses — plus a minimal package manifest.
Re-running overwrites the generated file (header says so).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "packages" / "api-client" / "src"
OUT_FILE = OUT_DIR / "types.ts"


def ts_type(schema: dict, schemas: dict) -> str:
    """Map one OpenAPI schema object to a TypeScript type string."""
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "anyOf" in schema:
        parts = [ts_type(s, schemas) for s in schema["anyOf"]]
        parts = [p for p in parts if p != "unknown"] or parts
        return " | ".join(parts)
    if "oneOf" in schema:
        parts = [ts_type(s, schemas) for s in schema["oneOf"]]
        parts = [p for p in parts if p != "unknown"] or parts
        return " | ".join(parts)
    if "enum" in schema:
        return " | ".join(json.dumps(v) for v in schema["enum"])
    kind = schema.get("type")
    if kind == "null":
        return "null"
    if kind == "string":
        return "string"
    if kind == "integer" or kind == "number":
        return "number"
    if kind == "boolean":
        return "boolean"
    if kind == "array":
        return f"{ts_type(schema.get('items', {}), schemas)}[]"
    if kind == "object":
        props = schema.get("properties", {})
        if not props:
            if schema.get("additionalProperties") is True:
                return "Record<string, unknown>"
            if isinstance(schema.get("additionalProperties"), dict):
                return f"Record<string, {ts_type(schema['additionalProperties'], schemas)}>"
            return "Record<string, unknown>"
        required = set(schema.get("required", []))
        fields = []
        for name, sub in props.items():
            optional = "" if name in required else "?"
            fields.append(f"  {name}{optional}: {ts_type(sub, schemas)};")
        return "{\n" + "\n".join(fields) + "\n}"
    return "unknown"


def generate(openapi: dict) -> str:
    schemas = openapi.get("components", {}).get("schemas", {})
    lines = [
        "// GENERATED — do not edit by hand.",
        "// Source: the Syrius API OpenAPI schema (scripts/gen_api_client.py).",
        "// Regenerate with: uv run --project apps/api python scripts/gen_api_client.py",
        "",
    ]
    for name in sorted(schemas):
        schema = schemas[name]
        if schema.get("type") == "object" or "properties" in schema:
            lines.append(f"export interface {name} {ts_type(schema, schemas)}")
        else:
            lines.append(f"export type {name} = {ts_type(schema, schemas)};")
        lines.append("")
    lines.append("// Operation map (method + path -> response type).")
    lines.append("export interface ApiOperations {")
    for path in sorted(openapi.get("paths", {})):
        for method, operation in sorted(openapi["paths"][path].items()):
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            op_id = operation.get("operationId", f"{method}_{path}")
            responses = operation.get("responses", {})
            ok = responses.get("200") or responses.get("201") or responses.get("202") or {}
            content = ok.get("content", {})
            app_json = content.get("application/json", {})
            resp_schema = app_json.get("schema", {})
            resp_type = ts_type(resp_schema, schemas) if resp_schema else "unknown"
            lines.append(f'  "{op_id}": {{ method: "{method}"; path: "{path}"; response: {resp_type} }};')
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    import sys

    sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
    from syrius_api.main import app

    openapi = app.openapi()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(generate(openapi))
    (ROOT / "packages" / "api-client" / "package.json").write_text(
        json.dumps(
            {
                "name": "syrius-api-client",
                "version": "0.1.0",
                "private": True,
                "description": "Generated TypeScript types for the Syrius API (from OpenAPI).",
                "types": "./src/types.ts",
            },
            indent=2,
        )
        + "\n"
    )
    print(f"wrote {OUT_FILE} ({len(openapi.get('paths', {}))} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
