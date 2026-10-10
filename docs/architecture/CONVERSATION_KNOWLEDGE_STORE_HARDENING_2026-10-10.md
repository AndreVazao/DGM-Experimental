# DGM-MAT — Incremental Conversation Memory Hardening Checkpoint
Date: 2026-10-10

## Scope and safety
Continues PR #71 on `feat/conversation-turn-semantics-v1`. Work remains in progress; do not merge prematurely or restart the live Core. No source history was modified remotely, no recovered script was executed, and no credentials were recorded.

## Repository and PR
- DGM-MAT local repository: `C:\\ProgramasGodMode\\DGM-MAT`.
- Feature branch: `feat/conversation-turn-semantics-v1`.
- Latest synchronized local/remote commit: `9987ece2328c39bf8ae496e4e429f141a3008f0c`.
- PR #71 remains open: https://github.com/AndreVazao/DGM-MAT/pull/71.
- GitHub returned no PR workflow runs and no combined status checks for the latest checked commit. Remote CI is **unverified**, not passed.

## Implemented changes

### 1. Preserve accepted proposal provenance
In `core/conversation_intelligence/knowledge_store.py`, explicitly accepted/rejected proposals protect `source_message_id` and `decision_id` as well as decision state, statement and source conversation.
- Regression: `test_accepted_proposal_preserves_message_and_decision_provenance`.

### 2. Reuse unchanged completed export snapshots
In `progress_store.py` and `pipeline.py`:
- Additive SQLite table `source_conversations` stores source fingerprint and ordered conversation membership.
- A completed source with an unchanged SHA-256 fingerprint, matching membership count and valid complete snapshots returns cached audit snapshots without reparsing or re-auditing.
- Changed sources, missing/legacy membership and invalid snapshots fall back to normal parsing and processing.
- Membership is written before the source is marked complete.
- Source bytes are still read to calculate SHA-256; timestamps alone are not trusted.

### 3. Recover from missing index, interrupted imports and changed sources
Regression coverage verifies:
- `test_unchanged_completed_source_reuses_cached_audits_without_parsing_export`
- `test_missing_source_snapshot_index_falls_back_to_parser_and_repairs_ledger`
- `test_interrupted_source_import_resumes_without_reauditing_completed_conversations`
- `test_changed_source_invalidates_source_cache_and_updates_conversation_snapshot`

The interrupted-import test confirms that already completed items are reused, the failed item is retried, and the source index is rebuilt before completion.

### 4. Reject silent changes to reviewed provenance
Reviewed intents, user-confirmed decisions and reviewed relations now reject every non-identical rewrite, including changes to source message IDs, evidence or confidence. Exact repeats remain idempotent.
- Regression: `test_reviewed_knowledge_provenance_and_evidence_cannot_be_silently_rewritten` verifies rejected changes leave the original records intact.

## Validation actually executed
- Focused knowledge-store and progress-store tests: passed (26 test cases).
- Broader selected suite passed with exit code 0:
  `python -m pytest -q tests\conversation_intelligence tests\contracts tests\organization tests\autonomy tests\security tests\cockpit`.
- `git diff --check`: exit code 0.
- Warnings remain for Starlette TestClient/httpx integration and FastAPI `on_event` deprecation.

## Local/GitHub synchronization
- DGM-MAT: local feature branch and GitHub are synchronized at `9987ece2328c39bf8ae496e4e429f141a3008f0c`; implementation, tests and architecture checkpoint were compared against GitHub, then the local branch was aligned to the fetched remote head. Worktree is clean.
- AndreOS memory: checkpoint file content hash matches GitHub main (`e7abcedfd9fa44b6323e668910a4a1e1faf7a7fa)). Git branch references/history are **not** synchronized: local branch still reports four commits ahead of cached `origin/main`, and `git fetch` fails because Windows Git Credential Manager cannot persist credentials or prompt. No reset, force-push or destructive history rewrite was attempted.

## Live Core safety gate
- Last known `GET http://127.0.0.1:8181/health` returned HTTP 200.
- Unauthenticated reads of `/runtime/status`, `/runtime/missions` and `/runtime/queue` returned HTTP 401, so active missions could not be verified.
- No Core restart, mission mutation or network exposure change was made.

## Next safe actions
1. Resolve AndreOS memory Git authentication safely before attempting full refs/history synchronization.
2. Continue focused state-transition and provenance tests only where a concrete gap is identified.
3. Keep PR #71 open until required remote checks/reviews are explicitly available.
4. Do not restart the live Core until active missions can be verified through an authorized read path or controlled maintenance is explicitly approved.


## 6. Guard source-level cache against duplicate conversation IDs across exports

A concrete cache-collision case was identified: the same provider conversation ID can appear in two distinct export files. The global progress ledger is keyed by provider and conversation ID, so importing the second export can replace the single stored audit snapshot. Without an additional check, the first export's unchanged source-level cache could then return the second export's snapshot.

Fix:
- Added an additive `conversation_fingerprint` column to `source_conversations`, including a safe migration for existing SQLite databases.
- Source membership now stores the fingerprint calculated from each conversation's normalized content.
- The source-level fast path verifies that the global completed snapshot still matches the member fingerprint before returning it. Legacy membership rows without a member fingerprint fall back to parsing and repair instead of being trusted.
- Added regression `test_source_cache_rejects_global_snapshot_from_another_export_with_same_conversation_id`.

Focused `test_progress_store.py` and `test_knowledge_store.py` suites passed. Added explicit regression coverage for migrating the existing SQLite membership schema and rejecting mismatched ID/fingerprint lists. The full selected regression suite passed with exit code 0: `tests\\conversation_intelligence tests\\contracts tests\\organization tests\\autonomy tests\\security tests\\cockpit`. `git diff --check` also passed (exit code 0).

## Next safe actions
1. Verify the explicit decision-supersession implementation and regression tests on both local and remote branch contents.
2. Recheck remote workflow runs and status checks; do not describe absent checks as passing.
3. Resolve AndreOS memory Git authentication before attempting full refs/history synchronization.
4. Keep PR #71 open and do not restart the live Core while active missions remain unverifiable.


## 7. Explicitly supersede confirmed decisions without rewriting history
A confirmed decision must remain immutable under ordinary `save_decision` calls, but a later, explicitly confirmed user decision may replace its current applicability. Treating all status changes as forbidden would make legitimate evolution impossible; silently overwriting the old row would destroy provenance.

Fix: `supersede_confirmed_decision` requires both records to exist, the successor to be user-confirmed and currently confirmed, and non-empty explicit evidence. It changes only the old decision's lifecycle status to `superseded`, retains the original statement/source/message/evidence/confirmation flag, and appends a `superseded` event to `knowledge_history` naming the successor and evidence. Repeating the same transition is idempotent; attempting to supersede it with a different successor is rejected.

Regression coverage:
- `test_confirmed_decision_can_only_be_superseded_explicitly_with_provenance`
- `test_confirmed_decision_supersession_requires_confirmed_successor_and_evidence`

Validation after this addition: the selected regression suite (`conversation_intelligence`, `contracts`, `organization`, `autonomy`, `security`, `cockpit`) passed with exit code 0; `git diff --check` passed. The standard Git push initially failed because Windows Git Credential Manager could not persist credentials or prompt. The exact local implementation, tests and docs were published through the authorized GitHub contents interface, then the public feature branch was fetched anonymously, compared and aligned locally at `9987ece2328c39bf8ae496e4e429f141a3008f0c`. Local DGM-MAT worktree is clean and matches GitHub. Remote CI remains unverified.

[executed on device: PC-Vazao-Anjos (982eb058-a42c-4897-9732-547f04cb44f0)]

## 8. Local-first test isolation and provider authentication boundary ? 2026-10-10

### Findings
- The first unrestricted local full-suite run used the default persistent runtime database. The contract tests inserted test actions into the live action queue. The run was stopped as soon as the side effect was identified. Two exact queued rows created by that run (IDs 1035 and 1036, payload goals `contract boundary` and `result boundary`) were rejected through `SafeActionQueue.reject`, preserving an audit trail. The completed cross-process test action was retained; no bulk queue or mission cleanup was performed.
- The runtime's API health endpoint returned HTTP 200, but the authenticated runtime snapshot reported status `starting`, 495 mission records (491 FAILED, 3 RUNNING, 1 QUEUED), and `worker_alive=false`. These records were not mass-mutated and the Core was not restarted.
- The Claude Code CLI is installed but reports `loggedIn=false`; Ollama is not running/reachable. Neither tool was represented as available for inference.

### Fixes
- Added `tests/conftest.py`, which sets `DGM_STORAGE_PATH` and `DGM_BASE_PATH` to a disposable temporary root before importing project modules. Subprocess tests inherit the isolated environment. The storage default-path test now explicitly removes the test overrides only for its own assertion and restores them afterward.
- Updated API integration tests to obtain short-lived test sessions rather than treating protected endpoints as public.
- Provider-execution routes now delegate to their own dedicated API/operator bearer-token checks. This is necessary because a single HTTP Authorization header cannot simultaneously contain both the local-session token and the provider-specific token. Provider endpoints still fail closed when their own credentials are missing/invalid.

### Validation and publication policy
- Full local suite: `python -m pytest -q --disable-warnings` completed with exit code 0 using isolated temporary storage.
- `git diff --check` passed.
- No GitHub push, PR update, workflow dispatch, or Actions run was performed for these changes. They remain local-only until a workflow-safe synchronization path is agreed.
- Core was not restarted; no external network binding was changed.

### Next priorities
1. Diagnose the runtime bootstrap/worker lifecycle and reconcile stale RUNNING mission records conservatively, without automatically re-running them.
2. Make cockpit authentication/pairing work for the PC-local client while preserving the loopback-only bootstrap boundary; do not expose to Tailscale/LAN until separately authorized and tested.
3. Establish a truthful local-inference readiness path. Do not assume Claude Code or Ollama is usable until authenticated/installed and verified; provide a deterministic no-model mode for inventory, memory retrieval, static checks and test execution.
4. Continue running tests locally with isolated storage; never trigger GitHub Actions while the minute budget is constrained.

## 9. Full-runtime headless startup and interrupted-mission reconciliation ? 2026-10-10

- Root cause confirmed: the Startup shortcut `DGM-MAT Headless.lnk` invoked `scripts/autostart/backend_service.py start`, whose implementation launched only `uvicorn core.api.api_server:app`. Its own description explicitly said it did not start autonomous workers. This produced HTTP health 200 while runtime status remained `starting` and the durable queue worker was absent.
- `backend_service.py` now has explicit `--mode api|full`. `api` preserves the existing API-only mode; `full` launches `main.py --headless`, remains loopback-only, and considers startup successful only after authenticated runtime status is `running` and the queue worker reports alive. It refuses to start a second process if an API already occupies the port but full readiness cannot be proved. Failed starts terminate the exact child they created. Process identity is checked before stopping either mode.
- The startup installer now selects `--mode full` for future installation/reconfiguration. The currently installed Startup shortcut has not yet been switched and the live API-only process has not yet been restarted; that final activation is deferred until the mission-state review is completed.
- An isolated smoke test ran the full runtime through the service manager on loopback port 8182 with a disposable database. It verified `runtime_status=running`, `worker_alive=true`, `status` success, and clean service stop. The isolated runtime was stopped; port 8182 is not left running.
- Added `MissionEngine.recover_interrupted_missions`, called before the queue worker starts. It uses the execution timeout and durable action state to reset stale RUNNING checkpoints with still-unapproved actions to QUEUED, leaves explicitly approved actions eligible for their approval path, and marks other stale/inconsistent RUNNING missions FAILED with preserved provenance and an explicit no-replay recovery marker. It never auto-approves or automatically replays work.
- Regression tests cover stale unapproved missions and explicitly approved actions. Focused service/auth/recovery tests passed. The full local suite was run with `tests/conftest.py` isolating storage; no GitHub Actions workflow was triggered.
- Production queue audit found 1,038 action rows: 1 APPROVED, 107 COMPLETED, 70 FAILED, 787 QUEUED, and 73 REJECTED. The sole APPROVED row is action 1037 of type `test_action` (approved by `test_user`); it was left untouched. Unapproved queued actions were not executed, bulk-rejected or deleted.

## 10. Core agent visibility in cockpit truth ? 2026-10-10
- The full runtime was activated locally and reports `running`, `is_degraded=false`, and a live durable queue worker. Startup recovery converted the three stale RUNNING test missions to two unapproved QUEUED missions and one FAILED mission requiring review; none was automatically replayed. The production queue still contains 787 unapproved QUEUED actions, which remain untouched. The only formerly APPROVED action was an unknown-handler test action and was recorded as FAILED by the worker rather than executing any external handler.
- A read-only runtime check then found `agents={}` despite `Runtime` constructing repo, provider and autonomy agents. Added explicit state-store registration for each constructed core agent with status `initialized`, role, implementation class and provider-required flag. This status intentionally does not claim external provider readiness. The regression test asserts all three core roles appear in the single cockpit truth store.
- Full local pytest suite passed after startup/recovery changes. After the agent-visibility change, the full local suite is being rerun with isolated storage. No GitHub push or Actions workflow has been triggered.
- The actual Windows Startup shortcut is now set to `backend_service.py start --mode full`; the live API-only process was stopped safely and replaced by the full headless runtime. Full-runtime service readiness and queue-worker heartbeat were verified on port 8181.

## 11. Runtime startup reliability and final local verification ? 2026-10-10
- Federation/rendezvous is now explicitly opt-in via DGM_FEDERATION_ENABLED=1. Default local boot skips outbound registration, avoiding a startup hang and preserving the local-only boundary.
- Mission restoration now suppresses per-record state notifications and publishes one MISSIONS_RECONCILED snapshot after loading and human-handoff reconciliation. This avoids repeated full-state broadcasts for hundreds of mission files.
- Full local pytest suite passed after these changes with isolated temporary storage. git diff --check passed. No GitHub push, PR update, or Actions workflow was triggered.
- Live local runtime is running on 127.0.0.1:8181, is_degraded=false, with three core agents (core:repo, core:provider, core:autonomy) registered as initialized and the durable queue worker alive. The Windows Startup shortcut selects full mode.
- Low-memory profile is active at 2.96 GB RAM; provider/autonomy startup scans remain deferred. Claude Code is installed but logged out; Ollama was not running/reachable at the last check. Verified local inference remains the next priority.
- Queue safety remains manual: unapproved actions stay queued; no bulk approvals, deletions, or replay. Stale mission recovery preserves provenance and does not automatically replay work.
\n\n

## 12. Local Ollama provider and resource-safe planning ? 2026-10-10
- Added a trusted local Ollama provider adapter and registered it first in provider priority. The adapter permits loopback HTTP only, lists installed models, supports bounded JSON-mode chat, and labels its cost profile local_zero_token. It never silently falls back to a remote provider.
- The mission planner can ask the local model for 3?5 proposed subtasks, validates the JSON and stores planning provenance. It never executes generated subtasks automatically. If the server is unavailable, the response is invalid, or resource guards trip, the existing deterministic planner is used.
- Ollama service helper and Startup shortcut now start the local server hidden on 127.0.0.1:11434, with the original shortcut backed up. The model server health check sees four installed models.
- A real inference smoke test with llama3.2:1b did not return within 90 seconds on this 2.96 GB RAM machine. Ollama reported a 1.3 GB model at 100% CPU and free RAM dropped to 0.02 GB. The model was stopped; free RAM recovered to about 0.93 GB. No further generation attempt was made.
- Added a 1.25 GB free-RAM guard and keep_alive=0. The planner now falls back quickly and deterministically instead of starving Windows; no paid API or remote provider is used as fallback. A stronger machine or more free RAM is needed to validate useful local inference latency.
- Full local pytest suite passed with isolated temporary storage and no GitHub Actions run. Provider/planner focused tests also passed. Changes are local-only and not pushed.

## 13. Provider health truth-store integration ? 2026-10-10
- Full local test suite passed again after the provider changes (pytest exit code 0; 56.82 seconds; git diff --check passed). Tests used local temporary storage; no GitHub Actions workflow was triggered.
- Found that ProviderBase.broadcast_health() previously emitted only a websocket message. That did not persist the provider observation into the runtime state store used as the cockpit current truth.
- Updated provider health broadcasts to dispatch PROVIDER_UPDATED into state_store, including observed-at timestamps, installed/loaded, health/availability, freshness and provenance fields. Bootstrap now publishes the local Ollama health observation instead of only tracing it.
- Added regression coverage that checks the health observation is present in the state store.
- Restarting the live Core is deliberately deferred: the runtime authenticated mission/action safety gate could not be completed reliably through the available runtime API. The source changes are local and tested, but live cockpit state will not reflect them until a separately verified safe restart.
- No GitHub push, PR merge, workflow dispatch or Core restart performed.


## 14. Main runtime loop trace-noise reduction — 2026-10-10
- Removed the per-second `TRACE_LOOP_START:main.py` call from the `run_runtime()` keep-alive loop. The loop still sleeps once per second and retains the existing startup/ownership traces; runtime lifecycle behavior is otherwise unchanged.
- Evidence: `.runtime/runtime_activation.log` had 52,612 lines (~1.37 MB), with the repeated loop marker at the end. This was unnecessary high-frequency disk and stdout logging.
- Validation: `python -m py_compile main.py` passed; `git diff --check` passed. No full suite was run because this is a one-line removal from a logging-only loop.
- The running process has already imported the previous version, so this source change takes effect only on a future safe restart. No restart was performed because the durable action queue/runtime safety state must be verified first.
- Historical logs were not deleted or truncated. No queue/mission state was changed. No push, merge or GitHub Actions run was performed.
