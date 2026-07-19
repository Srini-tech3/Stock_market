import os
import sys
import time
import socket
import logging
import subprocess
import webbrowser

# -----------------------------------------------------
# Configuration
# -----------------------------------------------------

HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}/dashboard"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "..", "Logs")
APP_FILE = os.path.join(BASE_DIR, "app.py")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "launcher.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -----------------------------------------------------
# Utility Functions
# -----------------------------------------------------

def is_port_open(host, port):
    """Return True if Flask is already running."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def wait_for_server(timeout=30):
    """Wait until Flask starts."""
    start = time.time()

    while time.time() - start < timeout:

        if is_port_open(HOST, PORT):
            return True

        time.sleep(1)

    return False


# -----------------------------------------------------
# Main
# -----------------------------------------------------

try:

    logging.info("Launcher started.")

    # Flask already running
    if is_port_open(HOST, PORT):

        logging.info("Dashboard already running.")
        webbrowser.open(URL)
        sys.exit()

    logging.info("Starting Flask server...")

    subprocess.Popen(
        [sys.executable, APP_FILE],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    logging.info("Waiting for Flask...")

    if wait_for_server():

        logging.info("Dashboard is ready.")
        webbrowser.open(URL)

    else:

        logging.error("Flask failed to start within timeout.")

except Exception as ex:

    logging.exception(ex)