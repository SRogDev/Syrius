"""Tests: tool registry — all 71 definitions present, statuses honest,
CartPole-relevant tools run for real."""

import pytest
from syrius_api import tools
from syrius_api.models import Project


def test_registry_has_all_departments() -> None:
    definitions = tools.list_definitions()
    assert len(definitions) == 71
    by_dept: dict[str, int] = {}
    for d in definitions:
        by_dept[d["department"]] = by_dept.get(d["department"], 0) + 1
    assert by_dept["rl_architect"] == 12
    assert by_dept["environment_factory"] == 18
    assert by_dept["experiment_factory"] == 17
    assert by_dept["evaluation_qa"] == 14
    assert by_dept["deployment_factory"] == 10
    names = {d["name"] for d in definitions}
    assert "ValidateEnvironment" in names
    assert "TrainPolicy" in names
    assert "PackagePolicy" in names


def test_not_implemented_tools_are_honest() -> None:
    not_impl = [d for d in tools.list_definitions() if d["status"] == "not_implemented"]
    assert {d["name"] for d in not_impl} == {
        "PublishEnvironment",
        "DeprecateEnvironment",
        "PublishEvaluationReport",
        "PublishPolicy",
        "RollbackPolicy",
        "SignDeliveryPackage",
    }
    for d in not_impl:
        assert d["not_implemented_reason"]


def test_unknown_tool_raises(session) -> None:
    with pytest.raises(ValueError, match="unknown tool"):
        tools.run_tool(session, "NoSuchTool", {})


def test_analyze_and_select_approach(session) -> None:
    analysis = tools.run_tool(
        session,
        "AnalyzeRLProblem",
        {"problem_text": "balance the pole upright with left and right moves"},
    )
    assert analysis["analysis"]["mentions_balance"] is True
    approach = tools.run_tool(session, "SelectRLApproach", {"gym_id": "CartPole-v1"})
    assert approach["approach"] == "PPO"


def test_search_registry_and_validate(session) -> None:
    found = tools.run_tool(session, "SearchEnvironmentRegistry", {"query": "cartpole"})
    assert any(r["gym_id"] == "CartPole-v1" for r in found["results"])
    validated = tools.run_tool(session, "ValidateEnvironment", {"gym_id": "CartPole-v1"})
    assert validated["valid"] is True


def test_generate_and_version_environment(session) -> None:
    project = Project(name="p")
    session.add(project)
    session.commit()
    created = tools.run_tool(
        session, "GenerateEnvironment", {"project_id": project.id, "gym_id": "CartPole-v1"}
    )
    assert created["status"] == "validated"
    versioned = tools.run_tool(
        session, "VersionEnvironment", {"environment_id": created["environment_id"]}
    )
    assert versioned["version"] == 2
    compared = tools.run_tool(
        session,
        "CompareEnvironmentVersions",
        {
            "environment_id_a": created["environment_id"],
            "environment_id_b": versioned["environment_id"],
        },
    )
    assert compared["diff"] == {}


def test_record_and_replay_episode(session, storage_dir) -> None:
    project = Project(name="p")
    session.add(project)
    session.commit()
    env = tools.run_tool(
        session, "GenerateEnvironment", {"project_id": project.id, "gym_id": "CartPole-v1"}
    )
    recorded = tools.run_tool(
        session, "RecordEpisode", {"environment_id": env["environment_id"], "seed": 7}
    )
    assert recorded["length"] > 0
    assert recorded["trace_artifact_id"]
    replayed = tools.run_tool(session, "ReplayEpisode", {"episode_id": recorded["episode_id"]})
    assert len(replayed["steps"]) == recorded["length"]
    assert replayed["steps"][0]["step"] == 1


def test_seed_tool_definitions(session) -> None:
    count = tools.seed_tool_definitions(session)
    assert count == 71
    assert tools.seed_tool_definitions(session) == 71  # idempotent upsert
