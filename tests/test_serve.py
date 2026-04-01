from contextlib import closing
from http.client import HTTPConnection
from pathlib import Path
import socket
import subprocess
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
SCRIPT = ROOT / "serve.sh"
INDEX_MARKER = "道藏知識庫"


def pick_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request(port: int, path: str = "/") -> tuple[int, str]:
    conn = HTTPConnection("127.0.0.1", port, timeout=1)
    try:
        conn.request("GET", path)
        response = conn.getresponse()
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body
    finally:
        conn.close()


def wait_for_content(port: int, marker: str, timeout: float = 5.0) -> tuple[int, str]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            status, body = request(port)
            if marker in body:
                return status, body
            last_error = AssertionError(f"marker {marker!r} not found, status={status}")
        except Exception as exc:  # pragma: no cover - timing-related retries
            last_error = exc
        time.sleep(0.1)

    if last_error is not None:
        raise last_error
    raise TimeoutError(f"timed out waiting for server on port {port}")


class ServeScriptTests(unittest.TestCase):
    def tearDown(self) -> None:
        proc = getattr(self, "_proc", None)
        if proc is None:
            return

        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)

        if proc.stdout is not None:
            proc.stdout.close()

        self._proc = None

    def start_server(self, cwd: Path, port: int) -> subprocess.Popen[str]:
        self._proc = subprocess.Popen(
            ["bash", str(SCRIPT), str(port)],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return self._proc

    def test_serve_script_works_from_workspace_root(self) -> None:
        port = pick_free_port()
        self.start_server(WORKSPACE_ROOT, port)

        status, body = wait_for_content(port, INDEX_MARKER)
        self.assertEqual(status, 200)
        self.assertIn("概念星圖", body)

    def test_serve_script_falls_back_when_requested_port_is_busy(self) -> None:
        busy_port = pick_free_port()
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", busy_port))
            sock.listen(1)

            self.start_server(ROOT, busy_port)

            for candidate in range(busy_port + 1, busy_port + 6):
                try:
                    status, body = wait_for_content(candidate, INDEX_MARKER, timeout=1.5)
                    self.assertEqual(status, 200)
                    self.assertIn("雙經入口", body)
                    return
                except Exception:
                    continue

        self.fail("serve.sh should keep running and choose the next free port")


if __name__ == "__main__":
    unittest.main()
