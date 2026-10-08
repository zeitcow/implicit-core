import io
import json

import pytest

from implicit.mcp import MAX_LINE, TOOLS, Server, serve


def ready():
    server = Server()
    response = server.dispatch(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        }
    )
    assert response["result"]["serverInfo"]["name"] == "implicit-core"
    assert server.dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    return server


def test_workflow_is_lazy_and_readonly_inspection_does_not_load():
    server = ready()
    uid = server.call("implicit_create_universe", {"count": 1000000})["universe_id"]
    args = {"universe_id": uid, "coordinate": 999999}
    first = server.call("implicit_address_experience", args)
    assert first["materialized_resources"] == 0
    assert server.call("implicit_inspect_state", args)["snapshot"]["resident_bytes"] == 0
    assert server.call("implicit_get_provenance", args)["provenance_hash"] == first["provenance_hash"]
    result = server.call("implicit_materialize", {**args, "resource": "policy"})
    assert result["value"] == {"method": "ground"}
    assert len(result["snapshot"]["resources"]) == 1
    again = server.call("implicit_materialize", {**args, "resource": "policy"})
    assert len(again["snapshot"]["resources"]) == 1


@pytest.mark.parametrize(
    "args",
    [
        {"count": True},
        {"count": 0},
        {"count": 1000001},
        {"count": "10"},
        {"count": 1, "path": "private"},
        {},
        {"count": 1.0},
    ],
)
def test_create_schemas_are_enforced(args):
    with pytest.raises(ValueError):
        ready().call("implicit_create_universe", args)


@pytest.mark.parametrize(
    "args",
    [
        {"universe_id": "../x", "coordinate": 0},
        {"universe_id": "u1", "coordinate": False},
        {"universe_id": "u1", "coordinate": -1},
        {"universe_id": "u1", "coordinate": 1000000},
        {"universe_id": "u99", "coordinate": 0},
    ],
)
def test_invalid_address_inputs(args):
    server = ready()
    server.call("implicit_create_universe", {"count": 5})
    with pytest.raises(ValueError):
        server.call("implicit_address_experience", args)


def test_capacity_and_no_implicit_addressing():
    server = ready()
    for _ in range(16):
        server.call("implicit_create_universe", {"count": 100})
    with pytest.raises(ValueError):
        server.call("implicit_create_universe", {"count": 1})
    args = {"universe_id": "u1", "coordinate": 0}
    with pytest.raises(ValueError):
        server.call("implicit_materialize", {**args, "resource": "inventory"})
    for coord in range(64):
        server.call("implicit_address_experience", {**args, "coordinate": coord})
    with pytest.raises(ValueError):
        server.call("implicit_address_experience", {**args, "coordinate": 64})
    server.call("implicit_address_experience", args)  # existing address still available


def test_error_redaction_unknown_methods_and_handshake():
    server = Server()
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    assert server.dispatch(msg)["error"]["code"] == -32600
    server = ready()
    assert server.dispatch({**msg, "method": "shell/execute"})["error"]["code"] == -32601
    result = server.dispatch(
        {
            **msg,
            "method": "tools/call",
            "params": {"name": "implicit_materialize", "arguments": {"path": "DO_NOT_LOG_THIS"}},
        }
    )
    assert result["result"]["isError"] and "DO_NOT_LOG_THIS" not in json.dumps(result)
    assert server.dispatch({"jsonrpc": "2.0", "method": "unknown"}) is None
    assert server.dispatch([])["error"]["code"] == -32600


@pytest.mark.parametrize(
    "payload",
    [b"no json\n", b"\xff\n", b'{"x":NaN}\n', b"[" * 2000 + b"]" * 2000 + b"\n"],
    ids=["invalid-json", "invalid-utf8", "nonfinite", "deep-json"],
)
def test_bad_frames_fail_safely(payload):
    out = io.StringIO()
    serve(io.BytesIO(payload), out)
    assert json.loads(out.getvalue())["error"]["code"] == -32700


def test_oversized_frame_closes_without_processing_tail():
    out = io.StringIO()
    serve(io.BytesIO(b"x" * (MAX_LINE + 1) + b"\n{}\n"), out)
    assert len(out.getvalue().splitlines()) == 1
    assert json.loads(out.getvalue())["error"]["code"] == -32600


def test_fixed_tools_are_offline_and_schemas_exclude_paths():
    server = ready()
    assert server.call("implicit_benchmark", {})["semantic_equivalence"]
    assert server.call("implicit_validate_adapter", {})["passed"]
    assert len(TOOLS) == 8
    for tool in TOOLS:
        schema = tool["inputSchema"]
        assert schema["additionalProperties"] is False
        assert not {"path", "command", "code", "url", "module"} & set(schema["properties"])


def test_tool_discovery_accepts_protocol_metadata():
    server = ready()
    message = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {"_meta": {"progressToken": "discovery"}},
    }
    assert len(server.dispatch(message)["result"]["tools"]) == 8
    message["params"] = {"_meta": "invalid"}
    assert server.dispatch(message)["error"]["code"] == -32602


def test_unknown_tool_is_a_protocol_error_without_input_echo():
    response = ready().dispatch(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "not-a-tool-private-value", "arguments": {}},
        }
    )
    assert response["error"]["code"] == -32602
    assert "not-a-tool-private-value" not in json.dumps(response)
