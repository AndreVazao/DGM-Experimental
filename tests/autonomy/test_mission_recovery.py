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
