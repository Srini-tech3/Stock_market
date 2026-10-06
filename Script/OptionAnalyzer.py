import threading
import time
import socket
import webview

from app import app
from waitress import serve


HOST = "127.0.0.1"
PORT = 5000


def run_server():
    serve(
        app,
        host=HOST,
        port=PORT,
        threads=4
    )


def wait_for_server(timeout=15):
    start = time.time()

    while time.time() - start < timeout:
        try:
            with socket.create_connection((HOST, PORT), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)

    return False


if __name__ == "__main__":

    flask_thread = threading.Thread(
        target=run_server,
        daemon=True
    )

    flask_thread.start()

    if wait_for_server():

        webview.create_window(
            title="NIFTY Options — Sensibull Practice Scanner",
            url=f"http://{HOST}:{PORT}/dashboard",
            width=1600,
            height=900,
            min_size=(1200, 700)
        )

        webview.start()
    else:
        raise SystemExit("Dashboard server did not start. Check Logs/application.log and whether port 5000 is available.")