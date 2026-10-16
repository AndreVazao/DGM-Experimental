# Governed Command Executor v1

## Included in this branch

- `core/operations/command_executor.py`: explicit read-only command catalog; no arbitrary shell input.
- `GET /governance/commands/catalog`: returns the allowed command IDs and current limitations.
- `POST /governance/commands/run`: runs one catalog command and returns bounded stdout/stderr, exit code, duration and status.
- `core/operations/operation_audit.py`: append-only JSONL audit records with redacted metadata.
- `core/api/security_policy.py`: explicitly classifies both routes as operator-only; the existing local-session middleware must authenticate the request.
- `tests/test_command_executor.py`: unit tests for unknown command denial, target path boundaries, shell=False, timeout reporting, output caps, fail-closed working directory, PowerShell arguments, engine inventory privacy and diagnostic error redaction.
- `tests/test_operation_audit.py`: audit append, schema/redaction, invalid-event rejection and fail-closed storage tests.
- `tests/security/test_api_global_auth_enforcement.py`: negative/positive coverage for missing, read-only and operator session access, audit persistence and refusal to execute when the audit destination is unavailable.
- `tests/security/test_api_security_policy.py`: confirms both command routes remain operator-only and classified.

## Available command IDs

- `system.summary`: read-only host/runtime summary using PowerShell.
- `process.top`: bounded process listing using PowerShell.
- `engines.inventory`: identifies likely Ollama/Claude Code processes and returns only process names and IDs. It does not return full command lines, start/stop processes, or establish ownership.
- `git.status`: read-only Git status for an existing working tree under `DGM_COMMAND_ALLOWED_ROOTS`.
- `ollama.status`: calls `ollama list` if the executable is available; it never starts or stops Ollama.
- `claude.status`: calls `claude --version` if the CLI is available; it does not read auth files or submit prompts.

## Audit behavior

Before a governed command is executed, the API must persist a `command.requested` event. If audit storage is unavailable, execution is refused. A `command.completed` or `command.denied` event is then appended. Records include UTC timestamp, event, command ID, status, session ID, duration and return code where available. They do not include stdout/stderr, credential values, or target paths.

The default path is `%LOCALAPPDATA%\\DGM-MAT\\audit\\command-audit.jsonl` on Windows. `DGM_COMMAND_AUDIT_PATH` can override it for controlled testing. Appends are serialized within the process and flushed with `fsync`. This is an application-level audit trail, not tamper-proof forensic storage; local administrators can still alter files and multi-process writers need further validation.

## Security behavior

The executor never accepts a raw command string. It invokes subprocesses with `shell=False`, bounded timeouts and capped output. It refuses to execute if none of the configured allowed roots exists instead of silently falling back to the process's current directory. Host diagnostics use fixed PowerShell scripts. Operating-system launch errors return the exception type, not the raw OS message, which could reveal a local path.

The route middleware requires an operator-scoped local session for both command endpoints. This is not a substitute for keeping the API bound to loopback or an explicitly trusted private network. The static policy inventory and tests are evidence of intended enforcement; tests still need to be run in a checkout.

## Deliberate limitations

This is a first implementation slice, not unrestricted machine control. It does **not** accept arbitrary PowerShell/CMD strings, perform administrator elevation, install software, start/stop services, change files, or manage credentials. The default allowlisted repository roots are `C:\\ProgramasGodMode` and `C:\\DevopGodMode`; override them with the semicolon-separated `DGM_COMMAND_ALLOWED_ROOTS` environment variable only after reviewing the scope.

The engine inventory is observational only; it does not reliably identify which process instance was started by DGM-MAT. Do not add stop/restart actions until process ownership can be established using a DGM-MAT-created process record and a verified PID/start-time pair.

## Validation status

The code and tests have been added to the branch. The connected Desktop Commander reports the target PC offline, so tests have not been executed from this session. No claim is made that this branch is installed or active on the PC. The work so far is code-level/static review only.

## Next steps

1. Run the focused unit/security tests in a development checkout and fix any failures.
2. Validate the audit file's permissions and multi-process behavior on Windows.
3. Implement lifecycle actions only for processes explicitly started and tracked by DGM-MAT, with confirmation and timeout handling.
4. Add a separate approved elevation broker; never pass administrator passwords to the LLM or shell.
5. Integrate executor and engine status into the PC cockpit.
6. Implement isolated self-repair and browser automation as separate branches.
