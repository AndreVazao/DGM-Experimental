from datetime import datetime, timedelta

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus


def _stale_mission(engine, mission_id, action_id, now):
    old = now - timedelta(minutes=5)
    mission = Mission(
        mission_id=mission_id,
        goal="Recovery regression test",
        description="test only",
        status=MissionStatus.RUNNING,
        metadata={"action_id": action_id, "execution_started_at": old.isoformat()},
        created_at=old,
        updated_at=old,
    )
    engine.active_missions[mission_id] = mission
    engine.save_mission(mission)
    return mission


def test_stale_running_mission_with_unapproved_action_returns_to_queue(tmp_path):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    now = datetime.now()
    mission_id = "recovery-unapproved-test"
    action_id = engine.action_queue.enqueue("MISSION_EXECUTION", {"mission_id": mission_id, "goal": "Recovery regression test"})
    mission = _stale_mission(engine, mission_id, action_id, now)

    report = engine.recover_interrupted_missions(now=now)

    assert report["requeued_unapproved"] == 1
    assert mission.status is MissionStatus.QUEUED
    assert mission.metadata["recovery"]["automatic_replay"] is False
    assert engine.action_queue.get_action(action_id)["status"] == "QUEUED"
    assert engine.action_queue.get_action(action_id)["is_approved"] is False


def test_stale_running_mission_with_explicitly_approved_action_is_not_rewritten(tmp_path):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    now = datetime.now()
    mission_id = "recovery-approved-test"
    action_id = engine.action_queue.enqueue("MISSION_EXECUTION", {"mission_id": mission_id, "goal": "Recovery regression test"})
    engine.action_queue.approve(action_id, operator="recovery-regression-test")
    mission = _stale_mission(engine, mission_id, action_id, now)

    report = engine.recover_interrupted_missions(now=now)

    assert report["awaiting_approved_action"] == 1
    assert mission.status is MissionStatus.RUNNING
    assert engine.action_queue.get_action(action_id)["status"] == "APPROVED"
    assert engine.action_queue.get_action(action_id)["is_approved"] is True


def test_queued_and_approval_pending_missions_do_not_timeout_from_creation_time(tmp_path, monkeypatch):
    import pytest

    engine = MissionEngine()
    engine.missions_path = tmp_path
    engine.active_missions = {}
    old = datetime.now() - timedelta(minutes=10)

    for status in (MissionStatus.QUEUED, MissionStatus.APPROVAL_PENDING):
        mission_id = f"waiting-{status.value.lower()}-timeout-regression"
        mission = Mission(
            mission_id=mission_id,
            goal="Waiting mission timeout regression",
            description="Must wait for worker or approval without timing out",
            status=status,
            created_at=old,
            updated_at=old,
        )
        engine.active_missions[mission_id] = mission

    monkeypatch.setattr(
        engine,
        "_timeout_mission",
        lambda mission, reason: pytest.fail(f"waiting mission timed out: {mission.mission_id}"),
    )

    engine.process_missions()

    assert engine.active_missions["waiting-queued-timeout-regression"].status is MissionStatus.QUEUED
    assert engine.active_missions["waiting-approval_pending-timeout-regression"].status is MissionStatus.APPROVAL_PENDING
