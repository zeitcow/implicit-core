"""Three independent offline adapters using only the documented Core protocols."""

from implicit import Address, Implicit, Region
from implicit.models import Execution, LogicalExperience, MaterializationPlan, ProbeResult, ResourceKey, VerificationResult


class World:
    version = "1"
    def __init__(self, identity, count=1000000): self.identity, self.count = identity, count
    def propose(self, *, regions, seed, limit, excluded):
        for offset in range(limit):
            address = Address(self.identity, self.version, str((seed + offset) % self.count), Region(self.identity, "all"))
            if address.uri not in excluded: yield address
    def probe(self, address): return ProbeResult(LogicalExperience(address, "Read the addressed value"), cost_usd=0)


class KeyValue:
    def __init__(self): self.universe = World("key-value")
    def plan(self, exp): return MaterializationPlan(exp, (), "1")
    def source(self, exp):
        class Source:
            version = "1"
            def load(self, key):
                if key != ResourceKey("value", "current"): raise KeyError(key)
                return {"value": int(exp.address.coordinate)}
            def dependencies(self, key, value): return ()
        return Source()
    def execute(self, agent, exp, state):
        return Execution(exp.address, {"value": state.read(ResourceKey("value", "current"))["value"]}, cost_usd=0)


class Relational:
    def __init__(self): self.universe = World("relational")
    def plan(self, exp): return MaterializationPlan(exp, (ResourceKey("orders", exp.address.coordinate),), "1")
    def source(self, exp):
        class Source:
            version = "1"
            def load(self, key):
                if key.namespace == "orders": return {"customer": key.key, "units": 2}
                if key.namespace == "customers": return {"value": int(key.key), "name": "public fixture"}
                raise KeyError(key)
            def dependencies(self, key, value):
                return (ResourceKey("customers", value["customer"]),) if key.namespace == "orders" else ()
        return Source()
    def execute(self, agent, exp, state):
        order = state.read(ResourceKey("orders", exp.address.coordinate))
        customer = state.read(ResourceKey("customers", order["customer"]))
        state.write(ResourceKey("receipt", "current"), {"units": order["units"]})
        return Execution(exp.address, {"value": customer["value"]}, cost_usd=0)


class Graph:
    def __init__(self): self.universe = World("graph")
    def plan(self, exp): return MaterializationPlan(exp, (), "1")
    def source(self, exp):
        class Source:
            version = "1"
            def load(self, key):
                if key.namespace != "nodes": raise KeyError(key)
                if key.key == "root": return {"edges": [exp.address.coordinate], "metadata": {"kind": "root"}}
                return {"edges": [], "value": int(key.key), "metadata": {"kind": "leaf"}}
            def dependencies(self, key, value): return tuple(ResourceKey("nodes", edge) for edge in value["edges"])
        return Source()
    def execute(self, agent, exp, state):
        root = state.read(ResourceKey("nodes", "root"))
        leaf = state.read(ResourceKey("nodes", root["edges"][0]))
        return Execution(exp.address, {"value": leaf["value"]}, cost_usd=0)


class Evaluator:
    def verify(self, exp, execution, state):
        passed = execution.outcome["value"] == int(exp.address.coordinate)
        return VerificationResult(float(passed), passed, "independent addressed-value fixture", cost_usd=0)


def run():
    import json
    from time import perf_counter
    rows = []
    for environment in (KeyValue(), Relational(), Graph()):
        start = perf_counter()
        session = Implicit().connect(agent=object(), environment=environment, evaluator=Evaluator())
        result = session.explore(episodes=3, seed=123)
        assert all(ep.verification.passed for ep in result.episodes)
        rows.append({"adapter": environment.universe.identity, "resources": result.metrics["resources_materialized"], "seconds": perf_counter() - start, "core_changes": 0, "files": 1, "configuration_steps": 0})
        session.close()
    print(json.dumps(rows))


if __name__ == "__main__": run()
