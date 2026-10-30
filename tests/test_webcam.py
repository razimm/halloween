import importlib.util
import json
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

spec = importlib.util.spec_from_file_location(
    'webcam', Path(__file__).resolve().parents[1] / 'tools/webcam.py')
webcam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(webcam)


class WebcamTests(unittest.TestCase):
    def setUp(self):
        self.camera = webcam.Camera('unused', 15)

    def test_slow_viewer_gets_latest_frame_without_queue(self):
        self.camera.publish(b'old')
        self.camera.publish(b'new')
        self.assertEqual(self.camera.latest(after=0), (2, b'new'))
        self.assertIsNone(self.camera.latest(after=2, timeout=0))

    def test_stale_frame_is_not_live_or_served(self):
        self.camera.publish(b'old')
        self.camera.updated = time.monotonic() - 4
        self.assertFalse(self.camera.status()['online'])
        self.assertIsNone(self.camera.latest())

    def test_stop_wakes_waiting_viewer(self):
        self.camera.stop.set()
        self.assertIsNone(self.camera.latest(after=100))

    def test_http_viewer_status_and_unavailable_camera(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0),
                                     webcam.handler_for(self.camera))
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base, timeout=2) as response:
                self.assertIn(b'/stream.mjpg', response.read())
                self.assertIn('no-store', response.headers['Cache-Control'])
            with urlopen(base + '/status', timeout=2) as response:
                self.assertFalse(json.load(response)['online'])
            with self.assertRaises(HTTPError) as error:
                urlopen(base + '/stream.mjpg', timeout=2)
            self.assertEqual(error.exception.code, 503)
            error.exception.close()
            with self.assertRaises(HTTPError) as error:
                urlopen(base + '/snapshot.jpg', timeout=2)
            self.assertEqual(error.exception.code, 503)
            error.exception.close()
            jpeg = b'\xff\xd8test\xff\xd9'
            self.camera.publish(jpeg)
            with urlopen(base + '/snapshot.jpg?t=123', timeout=2) as response:
                self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
                self.assertIn('no-store', response.headers['Cache-Control'])
                self.assertEqual(int(response.headers['Content-Length']), len(jpeg))
                self.assertEqual(response.read(), jpeg)
            self.camera.publish(jpeg + b'new')
            with urlopen(base + '/snapshot.jpg?t=124', timeout=2) as response:
                self.assertEqual(response.read(), jpeg + b'new')
            self.camera.publish(jpeg)
            with urlopen(base + '/stream.mjpg', timeout=2) as response:
                self.assertIn('multipart/x-mixed-replace',
                              response.headers['Content-Type'])
                self.assertEqual(response.readline(), b'--frame\r\n')
                self.assertEqual(response.readline(), b'Content-Type: image/jpeg\r\n')
                self.assertEqual(response.readline(), b'Content-Length: 8\r\n')
                self.assertEqual(response.readline(), b'\r\n')
                self.assertEqual(response.read(len(jpeg)), jpeg)
        finally:
            self.camera.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
