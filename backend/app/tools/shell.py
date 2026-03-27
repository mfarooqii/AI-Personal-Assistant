"""
Shell command tool — sandboxed command execution with timeout.
"""

import asyncio
import shlex


# Commands that are never allowed
BLOCKED_COMMANDS = {"rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:", "shutdown", "reboot", "poweroff"}


async def run_command(command: str, timeout: int = 30) -> dict:
    """Execute a shell command with safeguards."""
    # Safety check
    cmd_lower = command.lower().strip()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return {"error": f"Blocked command for safety: {command}"}

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=None,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode(errors="replace")
        errors = stderr.decode(errors="replace")

        # Truncate long output
        if len(output) > 10000:
            output = output[:10000] + "\n... [truncated]"

        return {
            "command": command,
            "exit_code": proc.returncode,
            "stdout": output,
            "stderr": errors[:2000] if errors else "",
        }
    except asyncio.TimeoutError:
        return {"command": command, "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"command": command, "error": str(e)}
