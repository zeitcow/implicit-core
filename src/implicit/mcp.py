"""Bounded local MCP over the public procedural adapter; no path or code inputs."""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from importlib.metadata import version
from typing import Any, BinaryIO, TextIO

from .accounting import Accounting
from .adapters.toy import ToyEnvironment
from .demo import benchmark
from .materialization import PagedState
from .models import Address, Region, ResourceKey
from .residency import ResidencyCache
from .serialization import content_hash, json_value

PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
MAX_LINE = 65536
ID = {"type": "string", "maxLength": 6, "pattern": "^u[1-9][0-9]?$"}
COORD = {"type": "integer", "minimum": 0, "maximum": 999999}
KEYS = {"inventory": ResourceKey("inventory", "item"), "policy": ResourceKey("policies", "shipping")}


def tool(
    name: str, description: str, properties: dict[str, Any], required: list[str], readonly: bool
) -> dict[str, Any]:
    return {
        "name": "implicit_" + name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": readonly,
            "destructiveHint": False,
            "idempotentHint": readonly,
            "openWorldHint": False,
        },
    }


TOOLS = [
    tool(
        "create_universe",
        "Create a process-local synthetic warehouse universe. Mutates memory only; max 16 universes. Returns handle/version; no files or external execution.",
        {"count": {"type": "integer", "minimum": 1, "maximum": 1000000}},
        ["count"],
        False,
    ),
    tool(
        "inspect_universe",
        "Read a known universe handle, version, count and addressed count. Unknown handles fail; no materialization.",
        {"universe_id": ID},
        ["universe_id"],
        True,
    ),
    tool(
        "address_experience",
        "Address a coordinate in a known synthetic universe, without loading state. Mutates memory (max 64 addresses/server); returns immutable address/provenance.",
        {"universe_id": ID, "coordinate": COORD},
        ["universe_id", "coordinate"],
        False,
    ),
    tool(
        "materialize",
        "Load inventory or policy for a previously addressed experience using Core paging. Mutates bounded memory; returns value, serialized bytes and content hash; no execution.",
        {"universe_id": ID, "coordinate": COORD, "resource": {"type": "string", "enum": list(KEYS)}},
        ["universe_id", "coordinate", "resource"],
        False,
    ),
    tool(
        "inspect_state",
        "Read materialized resource metadata for an addressed experience. Does not load missing resources. Returns retained serialized bytes, never RAM.",
        {"universe_id": ID, "coordinate": COORD},
        ["universe_id", "coordinate"],
        True,
    ),
    tool(
        "get_provenance",
        "Read immutable address/source version/hash and materialization hashes for an addressed experience. Does not execute an agent or load state.",
        {"universe_id": ID, "coordinate": COORD},
        ["universe_id", "coordinate"],
        True,
    ),
    tool(
        "benchmark",
        "Run the fixed offline eager versus Implicit public toy benchmark. Ephemeral memory only; reports equivalence/serialized bytes/timing and limited scope, no RC reproduction.",
        {},
        [],
        True,
    ),
    tool(
        "validate_adapter",
        "Validate the built-in warehouse adapter's public plan/source/address/materialization contract with fixed fixtures. Does not import user code; custom adapters require SDK tests.",
        {},
        [],
        True,
    ),
]


def validate(schema: dict[str, Any], value: Any) -> None:
    kind = schema["type"]
    if kind == "object":
        if (
            not isinstance(value, dict)
            or set(value) - set(schema["properties"])
            or set(schema["required"]) - set(value)
        ):
            raise ValueError("invalid arguments")
        for key, item in value.items():
            validate(schema["properties"][key], item)
    elif kind == "integer":
        if type(value) is not int or not schema["minimum"] <= value <= schema["maximum"]:
            raise ValueError("integer out of bounds")
    elif kind == "string":
        if not isinstance(value, str) or len(value) > schema.get("maxLength", 64):
            raise ValueError("invalid string")
        if "enum" in schema and value not in schema["enum"]:
            raise ValueError("invalid choice")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise ValueError("invalid handle")
    else:
        raise ValueError("unsupported schema")


class Server:
    def __init__(self) -> None:
        self.initialized = False
        self.ready = False
        self.universes: dict[str, int] = {}
        self.states: dict[tuple[str, int], PagedState] = {}

    def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        definition = next((t for t in TOOLS if t["name"] == name), None)
        if definition is None:
            raise ValueError("unknown tool")
        validate(definition["inputSchema"], args)
        if name == "implicit_benchmark":
            return benchmark()
        if name == "implicit_validate_adapter":
            env = ToyEnvironment()
            addr = Address("warehouse", "1", "0", Region("warehouse", "standard", "fulfillment"))
            exp = env.universe.probe(addr).experience
            plan, source = env.plan(exp), env.source(exp)
            pager = PagedState(plan, source, ResidencyCache(0), Accounting(), lambda *a: None)
            pager.initialize()
            policy = pager.read(KEYS["policy"])
            return {
                "adapter": "builtin-warehouse",
                "passed": plan.experience.address == addr
                and source.version == plan.source_version
                and policy == {"method": "ground"},
                "checks": [
                    "address identity",
                    "source version",
                    "initial state",
                    "progressive page",
                    "finite JSON",
                ],
                "custom_adapter_validated": False,
            }
        if name == "implicit_create_universe":
            if len(self.universes) >= 16:
                raise ValueError("universe capacity reached; restart to reset")
            uid = f"u{len(self.universes) + 1}"
            self.universes[uid] = args["count"]
            return {
                "universe_id": uid,
                "version": "1",
                "count": args["count"],
                "persistence": "process memory",
            }
        uid = args["universe_id"]
        if uid not in self.universes:
            raise ValueError("unknown universe")
        if name == "implicit_inspect_universe":
            return {
                "universe_id": uid,
                "count": self.universes[uid],
                "version": "1",
                "addressed": sum(k[0] == uid for k in self.states),
            }
        coord = args["coordinate"]
        if coord >= self.universes[uid]:
            raise ValueError("coordinate outside universe")
        key = (uid, coord)
        if name == "implicit_address_experience":
            if key not in self.states:
                if len(self.states) >= 64:
                    raise ValueError("address capacity reached; restart to reset")
                env = ToyEnvironment()
                region = Region("warehouse", ("standard", "fragile", "regulated")[coord % 3], "fulfillment")
                # Handles alias the same immutable warehouse model; they are not user-supplied sources.
                exp = env.universe.probe(Address("warehouse", "1", str(coord), region)).experience
                self.states[key] = PagedState(
                    env.plan(exp), env.source(exp), ResidencyCache(0), Accounting(), lambda *a: None
                )
            state = self.states[key]
            return {
                "address": state.plan.experience.address.uri,
                "provenance_hash": content_hash(state.plan.experience),
                "materialized_resources": len(state.snapshot().resources),
            }
        if key not in self.states:
            raise ValueError("address experience first")
        state = self.states[key]
        if name == "implicit_materialize":
            value = state.read(KEYS[args["resource"]])
            return {
                "value": value,
                "value_hash": content_hash(value),
                "snapshot": json_value(state.snapshot()),
                "scope": "retained serialized/materialized bytes; not RAM",
            }
        snapshot = json_value(state.snapshot())
        if name == "implicit_inspect_state":
            return {"snapshot": snapshot, "scope": "retained serialized/materialized bytes; not RAM"}
        return {
            "address": state.plan.experience.address.uri,
            "source_version": state.plan.source_version,
            "provenance_hash": content_hash(state.plan.experience),
            "materialization": snapshot,
        }

    def dispatch(self, request: Any) -> dict[str, Any] | None:
        rid = request.get("id") if isinstance(request, dict) else None

        def error(code: int, message: str) -> dict[str, Any]:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}

        if (
            not isinstance(request, dict)
            or request.get("jsonrpc") != "2.0"
            or not isinstance(request.get("method"), str)
        ):
            return error(-32600, "Invalid Request")
        if "id" in request and (type(rid) not in (int, str) or isinstance(rid, str) and len(rid) > 128):
            rid = None
            return error(-32600, "Invalid request id")
        method, params = request["method"], request.get("params", {})
        if not isinstance(params, dict):
            return None if "id" not in request else error(-32602, "Invalid params")
        if "id" not in request:
            if method == "notifications/initialized" and self.initialized:
                self.ready = True
            return None
        if method == "initialize":
            if self.initialized:
                return error(-32600, "Already initialized")
            if (
                not isinstance(params.get("protocolVersion"), str)
                or not isinstance(params.get("capabilities"), dict)
                or not isinstance(params.get("clientInfo"), dict)
            ):
                return error(-32602, "Invalid initialize params")
            self.initialized = True
            proposed = params["protocolVersion"]
            result: dict[str, Any] = {
                "protocolVersion": proposed if proposed in PROTOCOLS else PROTOCOLS[0],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "implicit-core", "version": version("implicit-ai")},
            }
        elif method == "ping":
            result = {}
        elif not self.ready:
            return error(-32600, "Initialize and send notifications/initialized first")
        elif method == "tools/list":
            if set(params) - {"_meta"} or ("_meta" in params and not isinstance(params["_meta"], dict)):
                return error(-32602, "No pagination supported")
            result = {"tools": TOOLS}
        elif method == "tools/call":
            if (
                set(params) - {"name", "arguments", "_meta"}
                or not isinstance(params.get("name"), str)
                or not isinstance(params.get("arguments", {}), dict)
            ):
                return error(-32602, "Invalid tool params")
            if not any(t["name"] == params["name"] for t in TOOLS):
                return error(-32602, "Unknown tool")
            try:
                data = self.call(params["name"], params.get("arguments", {}))
                result = {
                    "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
                    "structuredContent": data,
                    "isError": False,
                }
            except (ValueError, KeyError, TypeError):
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": "Invalid tool input, unknown handle, missing address, or capacity exceeded. See MCP.md.",
                        }
                    ],
                    "isError": True,
                }
        else:
            return error(-32601, "Method not found")
        return {"jsonrpc": "2.0", "id": rid, "result": result}


def serve(stream: BinaryIO, output: TextIO) -> None:
    server = Server()
    while line := stream.readline(MAX_LINE + 1):
        if len(line) > MAX_LINE:
            # Exit on oversized frames, avoiding unbounded draining of an untrusted pipe.
            output.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32600, "message": "Frame exceeds 65536 bytes"},
                    }
                )
                + "\n"
            )
            output.flush()
            return
        try:
            decoded = line.decode("utf-8")
            depth, quoted, escaped = 0, False, False
            for char in decoded:
                if quoted:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        quoted = False
                elif char == '"':
                    quoted = True
                elif char in "[{":
                    depth += 1
                    if depth > 32:
                        raise ValueError("JSON nesting exceeds limit")
                elif char in "]}":
                    depth -= 1
            request = json.loads(decoded, parse_constant=lambda s: (_ for _ in ()).throw(ValueError()))
            response = server.dispatch(request)
        except (ValueError, UnicodeError, RecursionError):
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        if response is not None:
            output.write(json.dumps(response, ensure_ascii=False, allow_nan=False) + "\n")
            output.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local stdio Implicit MCP; bounded synthetic state only")
    parser.add_argument("--version", action="version", version=version("implicit-ai"))
    parser.parse_args()
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    serve(sys.stdin.buffer, sys.stdout)


if __name__ == "__main__":
    main()
