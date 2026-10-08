"""Offline stdio client rehearsal; install with pip install implicit-ai; run without PYTHONPATH."""
import json
import subprocess
import sys
from time import perf_counter


def run():
    start = perf_counter()
    proc = subprocess.Popen(
        [sys.executable, "-I", "-m", "implicit.mcp"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8",
    )
    counter = 0

    def send(method, params, notification=False):
        nonlocal counter
        counter += 1
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notification:
            msg["id"] = counter
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()
        if notification:
            return None
        response = json.loads(proc.stdout.readline())
        assert response["id"] == counter and "error" not in response, response
        return response["result"]

    def call(name, args):
        result = send("tools/call", {"name": "implicit_" + name, "arguments": args})
        assert not result["isError"], result
        return json.loads(result["content"][0]["text"])

    try:
        init = send("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "public-rehearsal", "version": "1"}})
        send("notifications/initialized", {}, True)
        tools = send("tools/list", {})["tools"]
        assert len(tools) == 8
        uid = call("create_universe", {"count": 1000000})["universe_id"]
        call("inspect_universe", {"universe_id": uid})
        args = {"universe_id": uid, "coordinate": 7}
        addressed = call("address_experience", args)
        assert addressed["materialized_resources"] == 0
        inventory = call("materialize", {**args, "resource": "inventory"})
        policy = call("materialize", {**args, "resource": "policy"})
        assert inventory["value"]["kind"] == "fragile" and policy["value"]["method"] == "padded"
        state = call("inspect_state", args)
        provenance = call("get_provenance", args)
        assert len(state["snapshot"]["resources"]) == 2
        assert provenance["provenance_hash"] == addressed["provenance_hash"]
        result = call("benchmark", {})
        assert result["semantic_equivalence"]
        assert call("validate_adapter", {})["passed"]
        bad = send("tools/call", {"name": "implicit_materialize", "arguments": {**args, "resource": "../../secret"}})
        assert bad["isError"] and "../../secret" not in json.dumps(bad)
        print(json.dumps({"status": "PASS", "tool_count": 8, "tool_names": [t["name"] for t in tools], "server_version": init["serverInfo"]["version"], "benchmark": result, "provenance_hash": provenance["provenance_hash"], "seconds": perf_counter()-start, "manual_interventions": 0, "core_edits": 0, "scope": "deterministic client, not a model-driven tool-selection score"}))
    finally:
        proc.stdin.close()
        proc.wait(timeout=10)
        stderr = proc.stderr.read()
        assert proc.returncode == 0 and not stderr, stderr


if __name__ == "__main__":
    run()
