#!/usr/bin/env python3
"""LAN webcam viewer: one capture process, latest JPEG only, no recordings."""
import argparse
import json
import select
import signal
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEVICE = '/dev/v4l/by-id/usb-Trust_Webcam_Trust_Webcam_202116428-video-index0'
PAGE = Path(__file__).resolve().parents[1] / 'web' / 'webcam.html'


class Camera:
    def __init__(self, device, fps):
        self.command = [
            'ffmpeg', '-hide_banner', '-loglevel', 'warning', '-nostdin',
            '-f', 'v4l2', '-input_format', 'yuyv422', '-video_size', '640x480',
            '-framerate', str(fps), '-i', device, '-an',
            # This webcam repeats timestamps. Number frames without buffering
            # or waiting for a frame-rate conversion filter.
            '-vf', f'setpts=N/({fps}*TB)',
            '-c:v', 'mjpeg', '-threads', '1', '-q:v', '5',
            '-fps_mode', 'passthrough', '-f', 'image2pipe',
            '-flush_packets', '1', 'pipe:1',
        ]
        self.condition = threading.Condition()
        self.stop = threading.Event()
        self.process = None
        self.thread = threading.Thread(target=self.capture, daemon=True)
        self.frame = None
        self.sequence = 0
        self.updated = 0

    def publish(self, frame):
        with self.condition:
            self.frame = frame
            self.sequence += 1
            self.updated = time.monotonic()
            self.condition.notify_all()

    def latest(self, after=-1, timeout=3):
        with self.condition:
            self.condition.wait_for(
                lambda: self.sequence > after or self.stop.is_set(), timeout)
            if (self.stop.is_set() or self.sequence <= after or
                    time.monotonic() - self.updated > 3):
                return None
            return self.sequence, self.frame

    def status(self):
        with self.condition:
            age = time.monotonic() - self.updated if self.updated else None
            return {'online': age is not None and age < 3,
                    'frames': self.sequence,
                    'frame_age_ms': round(age * 1000) if age is not None else None}

    def capture(self):
        while not self.stop.is_set():
            try:
                self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE,
                                                bufsize=0)
                # close() may race with process creation during shutdown.
                if self.stop.is_set():
                    self.process.terminate()
                buffer = bytearray()
                while not self.stop.is_set():
                    ready, _, _ = select.select([self.process.stdout], [], [], 5)
                    if not ready:
                        raise RuntimeError('No camera frames for five seconds')
                    chunk = self.process.stdout.read(16384)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    while True:
                        start = buffer.find(b'\xff\xd8')
                        if start < 0:
                            buffer[:] = buffer[-1:]
                            break
                        if start:
                            del buffer[:start]
                        end = buffer.find(b'\xff\xd9', 2)
                        if end < 0:
                            if len(buffer) > 4 * 1024 * 1024:
                                raise RuntimeError('Oversized camera frame')
                            break
                        self.publish(bytes(buffer[:end + 2]))
                        del buffer[:end + 2]
            except (OSError, RuntimeError) as error:
                print(f'Camera: {error}', flush=True)
            finally:
                if self.process is not None:
                    if self.process.poll() is None:
                        self.process.terminate()
                    try:
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait()
                    self.process.stdout.close()
                with self.condition:
                    self.frame = None
                    self.updated = 0
                    self.condition.notify_all()
            self.stop.wait(2)

    def close(self):
        self.stop.set()
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        with self.condition:
            self.condition.notify_all()
        if self.thread.ident is not None:
            self.thread.join(timeout=5)


def handler_for(camera):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, content_type, length=None):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'SAMEORIGIN')
            if length is not None:
                self.send_header('Content-Length', str(length))
            self.end_headers()

        def do_GET(self):
            path = self.path.split('?', 1)[0]
            try:
                if path == '/':
                    body = PAGE.read_bytes()
                    self.respond(200, 'text/html; charset=utf-8', len(body))
                    self.wfile.write(body)
                elif path == '/status':
                    body = json.dumps(camera.status()).encode()
                    self.respond(200, 'application/json', len(body))
                    self.wfile.write(body)
                elif path == '/stream.mjpg':
                    self.stream()
                elif path == '/snapshot.jpg':
                    current = camera.latest()
                    if current is None:
                        self.send_error(503, 'Camera unavailable')
                    else:
                        frame = current[1]
                        self.respond(200, 'image/jpeg', len(frame))
                        self.wfile.write(frame)
                elif path == '/favicon.ico':
                    self.respond(204, 'image/x-icon', 0)
                else:
                    self.send_error(404)
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass

        def stream(self):
            current = camera.latest()
            if current is None:
                self.send_error(503, 'Camera unavailable')
                return
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32768)
            self.connection.settimeout(2)
            self.respond(200, 'multipart/x-mixed-replace; boundary=frame')
            while current is not None:
                sequence, frame = current
                self.wfile.write(
                    b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ' +
                    str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')
                self.wfile.flush()
                # Slow clients skip old frames instead of building a queue.
                current = camera.latest(after=sequence)

        def log_message(self, fmt, *args):
            if args and str(args[1] if len(args) > 1 else '').startswith(('4', '5')):
                super().log_message(fmt, *args)
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--device', default=DEVICE)
    parser.add_argument('--fps', type=int, choices=(5, 10, 15, 20, 25, 30), default=15)
    args = parser.parse_args()
    camera = Camera(args.device, args.fps)
    server = ThreadingHTTPServer((args.host, args.port), handler_for(camera))
    server.daemon_threads = True
    def interrupt(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupt)
    camera.thread.start()
    print(f'Webcam listening on {args.host}:{args.port}', flush=True)
    try:
        server.serve_forever(poll_interval=.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        camera.close()


if __name__ == '__main__':
    main()
