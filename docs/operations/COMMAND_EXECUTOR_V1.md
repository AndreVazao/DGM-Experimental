# Governed Command Executor v1

## Included in this branch

- `core/operations/command_executor.py`: explicit read-only command catalog; no arbitrary shell input.
- `GET /governance/commands/catalog`: returns the allowed command IDs and current limitations.
- `POST /governance/commands/run`: runs one catalog command and returns bounded stdout/stderr, exit code, duration and status.
- `core/api/security_policy.py`: explicitly classifies both routes as operator-only; the existing local-session middleware must authenticate the request.
- `tests/test_command_executor.py`: unit tests for unknown command denial, target path boundaries, shell=False, timeout reporting and output caps.

## Available command IDs

- `system.summary`: read-only host/runtime summary using PowerShell.
- `process.top`: bounded process listing using PowerShell.
- `git.status`: read-only Git status for an existing working tree under `DGM_COMMAND_ALLOWED_ROOTS`.
- `ollama.status`: calls `ollama list` if the executable is available.

## Deliberate limitations

This is a first implementation slice, not unrestricted machine control. It does **not** accept arbitrary PowerShell/CMD strings, perform administrator elevation, install software, start/stop services, change files, or manage credentials. The default allowlisted repository roots are `C:\\ProgramasGodMode` and `C:\\DevopGodMode`; override them with the semicolon-separated `DGM_COMMAND_ALLOWED_ROOTS` environment variable only after reviewing the scope. The executor invokes subprocesses with `shell=False`, bounded timeouts and capped output.

The API requires an operator-scoped local session according to the route security inventory. Do not expose the API on a public network. The current implementation does not yet provide persistent audit storage; production acceptance requires audit metadata, secret redaction, request rate limiting, and Windows-specific runtime tests.

## Validation status

The code and tests have been added to the branch. The connected Desktop Commander reports the target PC offline, so Windows execution/integration tests have not been run from this session. No claim is made that this branch is installed or active on the PC.

## Next steps

1. Run the unit suite on a development checkout and add API auth/route tests.
2. Add redacted persistent audit records and request correlation IDs.
3. Add service lifecycle commands limited to DGM-managed processes.
4. Add a separate approved elevation broker; never pass administrator passwords to the LLM or shell.
5. Integrate executor job status into the PC cockpit.
6. Implement isolated self-repair and browser automation as separate branches.