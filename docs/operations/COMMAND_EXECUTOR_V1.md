# Governed Command Executor v1

## Included in this branch

- `core/operations/command_executor.py`: explicit read-only command catalog; no arbitrary shell input.
- `GET /governance/commands/catalog`: returns the allowed command IDs and current limitations.
- `POST /governance/commands/run`: runs one catalog command and returns bounded stdout/stderr, exit code, duration and status.
- `core/api/security_policy.py`: explicitly classifies both routes as operator-only; the existing local-session middleware must authenticate the request.
- `tests/test_command_executor.py`: unit tests for unknown command denial, target path boundaries, shell=False, timeout reporting, output caps, fail-closed working directory, PowerShell arguments and diagnostic error redaction.
- `tests/security/test_api_global_auth_enforcement.py`: negative/positive coverage for missing, read-only and operator session access to the new endpoints.
- `tests/security/test_api_security_policy.py`: confirms both command routes remain operator-only and classified.

## Available command IDs

- `system.summary`: read-only host/runtime summary using PowerShell.
- `process.top`: bounded process listing using PowerShell.
- `git.status`: read-only Git status for an existing working tree under `DGM_COMMAND_ALLOWED_ROOTS`.
- `ollama.status`: calls `ollama list` if the executable is available; it never starts or stops Ollama.
- `claude.status`: calls `claude --version` if the CLI is available; it does not read auth files or submit prompts.

## Security behavior

The executor never accepts a raw command string. It invokes subprocesses with `shell=False`, bounded timeouts and capped output. It refuses to execute if none of the configured allowed roots exists instead of silently falling back to the process's current directory. Host diagnostics use a fixed PowerShell script. Operating-system launch errors return the exception type, not the raw OS message, which could reveal a local path.

The route middleware requires an operator-scoped local session for both command endpoints. This is not a substitute for keeping the API bound to loopback or an explicitly trusted private network. The static policy inventory and tests are evidence of intended enforcement; tests still need to be run in a checkout.

## Deliberate limitations

This is a first implementation slice, not unrestricted machine control. It does **not** accept arbitrary PowerShell/CMD strings, perform administrator elevation, install software, start/stop services, change files, or manage credentials. The default allowlisted repository roots are `C:\\ProgramasGodMode` and `C:\\DevopGodMode`; override them with the semicolon-separated `DGM_COMMAND_ALLOWED_ROOTS` environment variable only after reviewing the scope.

The current implementation does not yet provide persistent audit storage or request rate limiting. Those remain acceptance requirements before expanding this into mutating operations. Windows-specific runtime validation is also pending.

## Validation status

The code and tests have been added to the branch. The connected Desktop Commander reports the target PC offline, so tests have not been executed from this session. No claim is made that this branch is installed or active on the PC. The work so far is code-level/static review only.

## Next steps

1. Run the focused unit/security tests in a development checkout and fix any failures.
2. Add redacted persistent audit records and request correlation IDs.
3. Add a read-only lifecycle inventory, then lifecycle commands limited to processes explicitly started and tracked by DGM-MAT.
4. Add a separate approved elevation broker; never pass administrator passwords to the LLM or shell.
5. Integrate executor job status into the PC cockpit.
6. Implement isolated self-repair and browser automation as separate branches.
