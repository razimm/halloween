"""Independent HEOS soundboard: local HTTP audio and player-specific CLI commands."""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import socket
import subprocess
import threading
import time
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import wave

ROOT = Path(__file__).resolve().parents[1]


class Client:
    def __init__(self, host, timeout=3):
        self.socket = socket.create_connection((host, 1255), timeout=timeout)
        self.stream = self.socket.makefile('rb')
        self.timeout = timeout

    def command(self, command, **params):
        if any('\r' in str(v) or '\n' in str(v) for v in params.values()):
            raise ValueError('Invalid HEOS command parameter')
        # HEOS explicitly requires the unescaped URL as the last attribute.
        url = params.pop('url', None)
        query = urlencode(params)
        if url is not None:
            query += ('&' if query else '') + 'url=' + url
        request = 'heos://' + command + ('?' + query if query else '') + '\r\n'
        self.socket.sendall(request.encode())
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            self.socket.settimeout(max(.01, deadline - time.monotonic()))
            line = self.stream.readline(65536)
            if not line:
                raise ConnectionError('HEOS connection closed')
            response = json.loads(line)
            header = response.get('heos', {})
            if header.get('command', '').strip() != command:
                continue
            if header.get('result') != 'success':
                raise RuntimeError('HEOS rejected ' + command + ': ' + header.get('message', ''))
            if header.get('message', '').strip().rstrip("'").lower() == 'command under process':
                # This acknowledges processing, not completion. Wait for the
                # actual response rather than treating missing payload as empty.
                continue
            return response
        raise TimeoutError('HEOS response timeout')

    def close(self):
        try:
            self.stream.close()
        finally:
            self.socket.close()


def message_fields(response):
    return {k: v[0] for k, v in parse_qs(response['heos'].get('message', '')).items()}


class Renderer:
    """Standard UPnP AVTransport with finite music-track metadata."""
    SERVICE = 'urn:schemas-upnp-org:service:AVTransport:1'

    def __init__(self, host):
        base = f'http://{host}:60006'
        with urlopen(base + '/upnp/desc/aios_device/aios_device.xml', timeout=3) as response:
            device = ET.fromstring(response.read())
        for service in device.findall('.//{*}service'):
            if service.findtext('{*}serviceType') == self.SERVICE:
                self.control_url = urljoin(base, service.findtext('{*}controlURL'))
                break
        else:
            raise RuntimeError('HEOS AVTransport service is unavailable')

    def action(self, name, **args):
        namespace = 'http://schemas.xmlsoap.org/soap/envelope/'
        envelope = ET.Element('{' + namespace + '}Envelope')
        body = ET.SubElement(envelope, '{' + namespace + '}Body')
        action = ET.SubElement(body, '{' + self.SERVICE + '}' + name)
        for key, value in dict(InstanceID=0, **args).items():
            ET.SubElement(action, key).text = str(value)
        request = Request(self.control_url, data=ET.tostring(envelope, encoding='utf-8'),
                          headers={'Content-Type': 'text/xml; charset="utf-8"',
                                   'SOAPACTION': f'"{self.SERVICE}#{name}"'})
        with urlopen(request, timeout=3) as response:
            root = ET.fromstring(response.read())
        payload = root.find('.//{' + namespace + '}Body')[0]
        return {child.tag.split('}')[-1]: child.text or '' for child in payload}

    def load_track(self, url, duration, size):
        didl_ns = 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'
        didl = ET.Element('DIDL-Lite', {'xmlns': didl_ns,
                                      'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                                      'xmlns:upnp': 'urn:schemas-upnp-org:metadata-1-0/upnp/'})
        item = ET.SubElement(didl, 'item',
                             id='halloween-laugh', parentID='0', restricted='1')
        ET.SubElement(item, 'dc:title').text = 'Halloween Lachen'
        ET.SubElement(item, 'upnp:class').text = 'object.item.audioItem.musicTrack'
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        resource = ET.SubElement(item, 'res',
                                 protocolInfo='http-get:*:audio/mpeg:*',
                                 duration=f'{int(hours)}:{int(minutes):02d}:{seconds:06.3f}',
                                 size=str(size))
        resource.text = url
        self.action('SetAVTransportURI', CurrentURI=url,
                    CurrentURIMetaData=ET.tostring(didl, encoding='unicode'))
        self.action('SetPlayMode', NewPlayMode='NORMAL')


def prepare_laugh():
    source = ROOT / 'audio/laughing.wav'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    target = ROOT / 'audio/playback' / ('heos-laugh-' + digest + '.mp3')
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-i', str(source),
                        '-map', '0:a:0', '-c:a', 'libmp3lame', '-b:a', '128k', str(target)],
                       check=True, capture_output=True)
    with wave.open(str(source)) as audio:
        duration = audio.getnframes() / audio.getframerate()
    return target, duration


def handler_for(path, fetched):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_HEAD(self):
            self.serve(head=True)

        def do_GET(self):
            self.serve(head=False)

        def serve(self, head):
            if urlsplit(self.path).path != '/laugh.mp3':
                self.send_error(404)
                return
            size = path.stat().st_size
            start, end = 0, size - 1
            requested = self.headers.get('Range')
            if requested:
                match = re.fullmatch(r'bytes=(\d*)-(\d*)', requested.strip())
                if not match or not any(match.groups()):
                    self.send_error(416)
                    return
                left, right = match.groups()
                if left:
                    start = int(left)
                    end = min(end, int(right)) if right else end
                else:
                    start = max(0, size - int(right))
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header('Content-Range', f'bytes */{size}')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
            self.send_response(206 if requested else 200)
            self.send_header('Content-Type', 'audio/mpeg')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(end - start + 1))
            self.send_header('Cache-Control', 'no-store')
            if requested:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            if not head:
                fetched.set()
                try:
                    with path.open('rb') as stream:
                        stream.seek(start)
                        self.wfile.write(stream.read(end - start + 1))
                except (BrokenPipeError, ConnectionResetError):
                    pass
    return Handler


class Soundboard:
    def __init__(self, config, simulate=False, log=print):
        self.config, self.simulate, self.log = config, simulate, log
        self.lock = threading.Lock()
        self.request = threading.Event()
        self.stop_event = threading.Event()
        self.fetched = threading.Event()
        self.busy = False
        self.working = False
        self.suspended = False
        self.cancel_playback = threading.Event()
        self.transport_lock = threading.Lock()
        self.panic_worker = None
        self.last_error = None
        self.server = self.http_worker = self.worker = None
        self.duration = 0
        # evdev timestamps use CLOCK_REALTIME by default. Compare them with
        # this wall-clock boundary so delayed input cannot become a new play.
        self.accept_after = time.time()
        if simulate:
            return
        path, self.duration = prepare_laugh()
        self.path = path
        self.server = ThreadingHTTPServer((config['bind_host'], config['http_port']),
                                          handler_for(path, self.fetched))
        self.server.daemon_threads = True
        try:
            self.http_worker = threading.Thread(target=self.server.serve_forever,
                                                name='heos-audio-http', daemon=True)
            self.http_worker.start()
            self.worker = threading.Thread(target=self.run, name='heos-soundboard', daemon=True)
            self.worker.start()
        except BaseException:
            self.close()
            raise

    def trigger(self, pressed_at=None):
        if self.suspended:
            return False
        if self.simulate:
            self.log(f'Simulation HEOS: Lachen auf {self.config["name"]}, {self.config["volume"]} %')
            return True
        with self.lock:
            if (self.busy or self.suspended or self.stop_event.is_set()
                    or (pressed_at is not None and pressed_at <= self.accept_after)):
                return False
            self.busy = True
            self.last_error = None
            self.request.set()
            return True

    def panic(self):
        with self.lock:
            self.suspended = True
            self.cancel_playback.set()
            self.request.clear()
            if not self.working:
                self.busy = False
            self.accept_after = time.time()
            if self.simulate:
                self.log('Simulation HEOS: Panic-Stopp')
                return
            if self.panic_worker is None or not self.panic_worker.is_alive():
                self.panic_worker = threading.Thread(target=self.stop_player,
                                                     name='heos-panic-stop', daemon=True)
                self.panic_worker.start()

    def stop_player(self):
        client = None
        try:
            cfg = self.config
            client = Client(cfg['host'])
            players = client.command('player/get_players')['payload']
            if not any(str(p.get('pid')) == str(cfg['player_id'])
                       and p.get('name') == cfg['name'] and p.get('ip') == cfg['host']
                       for p in players):
                raise RuntimeError('Kitchen HEOS identity could not be verified')
            # A previously started load/play action must finish before STOP;
            # cancellation prevents every subsequent PLAY from being sent.
            with self.transport_lock:
                client.command('player/set_play_state', pid=cfg['player_id'], state='stop')
            self.log('HEOS: Panic-Stopp gesendet')
        except Exception as error:
            self.log(f'HEOS: Panic-Stopp fehlgeschlagen: {error}')
        finally:
            if client is not None:
                client.close()

    def resume(self):
        with self.lock:
            if self.busy or (self.panic_worker is not None and self.panic_worker.is_alive()):
                return False
            self.request.clear()
            self.cancel_playback.clear()
            self.accept_after = time.time()
            self.suspended = False
            return True

    def play_once(self):
        if self.cancel_playback.is_set():
            return
        cfg = self.config
        client = Client(cfg['host'])
        try:
            players = client.command('player/get_players')['payload']
            selected = next((p for p in players if str(p['pid']) == str(cfg['player_id'])), None)
            if (selected is None or selected.get('name') != cfg['name']
                    or selected.get('ip') != cfg['host']):
                raise RuntimeError('Configured kitchen HEOS identity could not be verified')
            # Reject grouping so that the other HEOS never plays this effect.
            groups = client.command('group/get_groups').get('payload', [])
            if any(str(p.get('pid')) == str(cfg['player_id'])
                   for group in groups for p in group.get('players', [])):
                raise RuntimeError('Kitchen HEOS is grouped; ungroup it in the HEOS app first')
            client.command('player/set_volume', pid=cfg['player_id'], level=cfg['volume'])
            client.command('player/set_mute', pid=cfg['player_id'], state='off')
            client.command('player/set_play_mode', pid=cfg['player_id'], repeat='off', shuffle='off')
            renderer = Renderer(cfg['host'])
            base_url = f'http://{cfg["advertise_host"]}:{cfg["http_port"]}/laugh.mp3'
            state = renderer.action('GetTransportInfo').get('CurrentTransportState')
            if state in ('PLAYING', 'TRANSITIONING'):
                current_uri = renderer.action('GetPositionInfo').get('TrackURI', '')
                if current_uri == base_url or current_uri.startswith(base_url + '?'):
                    self.log('HEOS: Lachen läuft bereits; Aufruf verworfen')
                    return
            self.fetched.clear()
            url = base_url + f'?play={time.monotonic_ns()}'
            with self.transport_lock:
                if self.cancel_playback.is_set():
                    return
                renderer.load_track(url, self.duration, self.path.stat().st_size)
                if self.cancel_playback.is_set():
                    return
                renderer.action('Play', Speed=1)
            self.log(f'HEOS: Lachen auf {cfg["name"]} ({cfg["volume"]} %)')
            observed_play = False
            # This is an error watchdog, never an estimated playback lock.
            deadline = time.monotonic() + self.duration + 15
            while not self.stop_event.is_set() and not self.cancel_playback.is_set():
                state = renderer.action('GetTransportInfo').get('CurrentTransportState')
                if state == 'PLAYING':
                    observed_play = True
                elif observed_play and state in ('STOPPED', 'NO_MEDIA_PRESENT'):
                    self.log(f'HEOS: Titel beendet; HTTP-Abruf {"bestätigt" if self.fetched.is_set() else "nicht gesehen"}')
                    return
                if time.monotonic() > deadline:
                    raise TimeoutError('HEOS track end could not be confirmed')
                self.stop_event.wait(.25)
        finally:
            client.close()

    def run(self):
        while not self.stop_event.is_set():
            self.request.wait(.5)
            if self.stop_event.is_set():
                return
            if not self.request.is_set():
                continue
            with self.lock:
                if self.suspended or not self.request.is_set():
                    self.request.clear()
                    self.busy = False
                    continue
                self.request.clear()
                self.working = True
            try:
                self.play_once()
            except Exception as error:
                self.last_error = str(error)
                self.log('HEOS-Sound konnte nicht abgespielt werden: ' + str(error))
            finally:
                with self.lock:
                    self.working = False
                    self.accept_after = time.time()
                    self.busy = False

    def close(self):
        self.stop_event.set()
        self.cancel_playback.set()
        self.request.set()
        if self.worker is not None and self.worker.is_alive():
            self.worker.join(timeout=4)
        if self.panic_worker is not None and self.panic_worker.is_alive():
            self.panic_worker.join(timeout=4)
        if self.server is not None:
            if self.http_worker is not None and self.http_worker.is_alive():
                self.server.shutdown()
                self.http_worker.join(timeout=1)
            self.server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test', action='store_true', help='Play laughter once on the configured HEOS')
    args = parser.parse_args()
    if not args.test:
        parser.error('Use --test to explicitly play the sound')
    config = json.loads((ROOT / 'config/show.json').read_text())['heos']
    board = Soundboard(config)
    try:
        board.trigger()
        deadline = time.monotonic() + 45
        while board.busy and time.monotonic() < deadline:
            time.sleep(.1)
        if board.last_error:
            raise SystemExit(board.last_error)
        if board.busy:
            raise SystemExit('HEOS test timed out')
    finally:
        board.close()


if __name__ == '__main__':
    main()
