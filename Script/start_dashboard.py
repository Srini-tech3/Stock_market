"""Launch the local dashboard in the default browser."""
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from app_support import configure_logging, log_event
from config import project_root

HOST, PORT = "127.0.0.1", 5000
URL = f"http://{HOST}:{PORT}/dashboard"


def is_port_open(host=HOST, port=PORT):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def wait_for_server(timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_port_open():
            return True
        time.sleep(0.25)
    return False


def main():
    root = project_root()
    configure_logging(root)
    log_event("browser_launcher_started")
    if not is_port_open():
        # Keep startup output instead of discarding errors, including missing dependencies.
        with (root / "Logs" / "server.log").open("a", encoding="utf-8") as output:
            process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("app.py"))],
                                       cwd=root, stdout=output, stderr=subprocess.STDOUT)
        if not wait_for_server() or process.poll() is not None:
            raise SystemExit("Dashboard could not start. Check Logs/server.log and install requirements.txt.")
    webbrowser.open(URL)
    log_event("browser_dashboard_opened")


if __name__ == "__main__":
    main()
