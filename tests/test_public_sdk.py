from implicit import Implicit
from implicit.adapters.toy import ToyEnvironment, ToyEvaluator
from implicit.demo import benchmark
from implicit.materialization import PagedState
from implicit.models import LogicalExperience, ResourceKey


def agent(experience: LogicalExperience, state: PagedState) -> str:
    item = state.read(ResourceKey("inventory", "item"))
    return state.read(ResourceKey("policies", item["policy_ref"]))["method"]


def test_external_agent_native_verifier_and_durable_rebind(tmp_path):
    database = tmp_path / "sessions.db"
    client = Implicit(database=database)
    session = client.connect(
        agent=agent, environment=ToyEnvironment(), evaluator=ToyEvaluator(), agent_version="public-1"
    )
    result = session.explore(episodes=8, seed=123)
    assert all(ep.verification.passed for ep in result.episodes)
    assert all(ep.materialization.resident_bytes < 1000 for ep in result.episodes)
    sid = session.session_id
    old_events = session.events()
    session.close()
    resumed = Implicit(database=database).resume(
        sid, agent=agent, environment=ToyEnvironment(), evaluator=ToyEvaluator(), agent_version="public-1"
    )
    assert resumed.events()[: len(old_events)] == old_events
    assert resumed.events()[-1].kind == "recovery"
    assert all(ep.verification.passed for ep in resumed.explore(episodes=2, seed=456).episodes)
    resumed.close()


def test_public_benchmark_reproduces_results_and_provenance():
    first, second = benchmark(), benchmark()
    for field in [
        "address",
        "eager_materialized_bytes",
        "implicit_materialized_bytes",
        "reduction",
        "result",
        "provenance_hash",
    ]:
        assert first[field] == second[field]
    assert (
        first["semantic_equivalence"] and first["implicit_resources"] == 2 and first["eager_resources"] == 3
    )
    assert first["implicit_materialized_bytes"] < first["eager_materialized_bytes"]
