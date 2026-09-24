"""Start Mink in a tmux split while leaving the user's shell real."""

import os
import shutil
import subprocess
import sys
import uuid
from typing import Optional
import shlex


COMMANDS = {
    "play", "pause", "toggle", "next", "prev", "previous",
    "volume", "status", "quit", "close",
}


def _socket_candidates() -> list:
    configured = os.environ.get("MINK_SOCKET")
    if configured:
        return [configured]
    try:
        return [f"/tmp/{name}" for name in os.listdir("/tmp")
                if name.startswith("mink-") and name.endswith(".sock")]
    except OSError:
        return []


def _running_socket() -> Optional[str]:
    import socket
    for path in _socket_candidates():
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(0.5)
                client.connect(path)
                client.sendall(b"status")
                client.recv(256)
            return path
        except OSError:
            continue
    return None


def _send_command(command: str) -> int:
    path = _running_socket()
    if not path:
        if command == "close":
            print("Mink is not running.")
            return 0
        print("mink: no running instance found", file=sys.stderr)
        return 1
    import socket
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(1)
            client.connect(path)
            client.sendall(command.encode())
            if command == "status":
                response = client.recv(256).decode().strip()
                if response:
                    print(response)
    except OSError as error:
        print(f"mink: cannot contact running instance: {error}", file=sys.stderr)
        return 1
    return 0


def _direct() -> int:
    from .ui import run_ui
    try:
        run_ui()
    finally:
        session = os.environ.get("MINK_SESSION")
        if session and shutil.which("tmux"):
            subprocess.run(["tmux", "kill-session", "-t", session],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False)
    return 0


def main() -> int:
    if "--direct" in sys.argv:
        return _direct()
    command_name = sys.argv[1] if len(sys.argv) > 1 else ""
    if command_name in COMMANDS:
        command = " ".join(sys.argv[1:])
        return _send_command(command)
    if command_name in {"help", "--help", "-h", ""}:
        print("usage: mink start|play|pause|toggle|next|prev|volume N|status|quit|close")
        print("mink close    Completely close Mink and clean up its process/resources")
        return 0
    if command_name != "start":
        print(f"mink: unknown command: {command_name}", file=sys.stderr)
        return 2
    if _running_socket():
        print("Mink is already running.")
        return 0
    tmux = shutil.which("tmux")
    if not tmux:
        print("mink: tmux is required (install it with your Linux package manager)",
              file=sys.stderr)
        return 1
    session = "mink-" + uuid.uuid4().hex[:8]
    socket_path = f"/tmp/{session}.sock"
    root = os.environ.get("MINK_ROOT")
    if not root:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = os.path.realpath(root)
    shell = os.environ.get("MINK_SHELL") or os.environ.get("SHELL") or "/bin/sh"
    cwd = os.getcwd()
    subprocess.run(["env", f"MINK_SOCKET={socket_path}",
                    f"MINK_SESSION={session}", f"MINK_SHELL={shell}",
                    tmux, "new-session", "-d", "-s", session, "-c", cwd, shell],
                   check=True)
    # Keep the split visually seamless: Mink should feel embedded, not boxed in.
    for option, value in (
        ("pane-border-style", "fg=black,bg=black"),
        ("pane-active-border-style", "fg=black,bg=black"),
    ):
        subprocess.run([tmux, "set-option", "-t", session, option, value],
                       check=True)
    direct = " ".join([
        f"MINK_ROOT={shlex.quote(root)}",
        f"PYTHONPATH={shlex.quote(root)}",
        f"MINK_SESSION={shlex.quote(session)}",
        f"MINK_SOCKET={shlex.quote(socket_path)}",
        shlex.quote(sys.executable),
        "-m", "mink", "--direct",
    ])
    # Keep the shell full-width while reserving enough rows for the pet and
    # complete playback metadata at laptop-sized terminal heights.
    subprocess.run([tmux, "split-window", "-v", "-l", "9",
                    "-t", f"{session}:0.0", "-c", cwd,
                    direct], check=True)
    mink_pane = f"{session}:0.1"
    subprocess.run([tmux, "set-option", "-t", session, "mouse", "on"],
                   check=True)
    subprocess.run([tmux, "set-option", "-p", "-t", mink_pane,
                    "@mink_pane", "1"], check=True)
    # tmux must claim wheel input from the terminal, but must not enter
    # copy-mode or scroll history when the pointer is over Mink's pane.
    for wheel in ("WheelUpPane", "WheelDownPane"):
        subprocess.run(
            [tmux, "bind-key", "-T", "root", wheel, "if-shell", "-F",
             "#{@mink_pane}", "run-shell -b ':'", "send-keys -M"],
            check=True,
        )
    subprocess.run([tmux, "select-pane", "-t", f"{session}:0.0"], check=True)
    if os.environ.get("TMUX"):
        return subprocess.run([tmux, "switch-client", "-t", session]).returncode
    return subprocess.run([tmux, "attach-session", "-t", session]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
