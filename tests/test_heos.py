import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import Mock, patch

from tools.heos import Client, Renderer, Soundboard, handler_for, ThreadingHTTPServer
import xml.etree.ElementTree as ET

CONFIG = json.loads((Path(__file__).resolve().parents[1] / 'config/show.json').read_text())['heos']


class HeosTests(unittest.TestCase):
    def test_panic_clears_pending_request_and_requires_resume(self):
        board = Soundboard(CONFIG, simulate=True, log=lambda *args: None)
        board.request.set()
        board.busy = True
        board.panic()
        self.assertFalse(board.request.is_set())
        self.assertFalse(board.trigger())
        self.assertTrue(board.cancel_playback.is_set())
        self.assertTrue(board.resume())
        self.assertTrue(board.trigger())

    def test_panic_during_track_loading_prevents_late_play_and_stops_target(self):
        board = Soundboard(CONFIG, simulate=True, log=lambda *args: None)
        board.simulate = False
        board.path = Mock()
        board.path.stat.return_value.st_size = 12345
        client, renderer = Mock(), Mock()
        def reply(command, **params):
            if command == 'player/get_players':
                return {'payload': [{'pid': CONFIG['player_id'], 'name': CONFIG['name'],
                                     'ip': CONFIG['host']}]}
            return {'payload': []}
        client.command.side_effect = reply
        renderer.action.return_value = {'CurrentTransportState': 'STOPPED'}
        renderer.load_track.side_effect = lambda *args: board.panic()
        with patch('tools.heos.Client', return_value=client), \
                patch('tools.heos.Renderer', return_value=renderer):
            board.play_once()
            board.panic_worker.join(timeout=1)
        self.assertFalse(board.panic_worker.is_alive())
        self.assertNotIn('Play', [call.args[0] for call in renderer.action.call_args_list])
        client.command.assert_any_call('player/set_play_state', pid=CONFIG['player_id'], state='stop')
        self.assertFalse(board.trigger())
        self.assertTrue(board.resume())

    def test_old_ok_from_before_panic_resume_cannot_be_replayed(self):
        board = Soundboard(CONFIG, simulate=True, log=lambda *args: None)
        old_press = time.time()
        board.panic()
        board.resume()
        board.simulate = False
        self.assertFalse(board.trigger(pressed_at=old_press))
        self.assertFalse(board.request.is_set())

    def test_client_skips_events_and_keeps_url_as_last_attribute(self):
        sock = Mock()
        stream = sock.makefile.return_value
        stream.readline.side_effect = [
            b'{"heos":{"command":"event/player_state_changed","message":"state=stop"}}\n',
            b'{"heos":{"command":"browse/play_stream","result":"success","message":"command under process"}}\n',
            b'{"heos":{"command":"browse/play_stream","result":"success"}}\n']
        with patch('tools.heos.socket.create_connection', return_value=sock):
            client = Client('kitchen')
            client.command('browse/play_stream', pid=1491570931,
                           url='http://192.168.178.130:8081/laugh.mp3')
            client.close()
        sock.sendall.assert_called_once_with(
            b'heos://browse/play_stream?pid=1491570931&url=http://192.168.178.130:8081/laugh.mp3\r\n')
        sock.close.assert_called_once()

    def test_playback_only_targets_kitchen_and_ends_on_real_transport_stop(self):
        board = Soundboard(CONFIG, simulate=True, log=lambda *args: None)
        board.duration = 7.035
        board.path = Mock()
        board.path.stat.return_value.st_size = 12345
        client, renderer = Mock(), Mock()
        client.command.side_effect = lambda command, **params: (
            {'payload': [{'pid': CONFIG['player_id'], 'name': CONFIG['name'], 'ip': CONFIG['host']}]}
            if command == 'player/get_players' else {'payload': []})
        states = iter(('STOPPED', 'PLAYING', 'STOPPED'))
        renderer.action.side_effect = lambda name, **args: (
            {'CurrentTransportState': next(states)} if name == 'GetTransportInfo' else {})
        with patch('tools.heos.Client', return_value=client), \
                patch('tools.heos.Renderer', return_value=renderer), \
                patch.object(board.stop_event, 'wait', return_value=False):
            board.play_once()
        client.command.assert_any_call('player/set_volume', pid=1491570931, level=10)
        for call in client.command.call_args_list:
            self.assertNotEqual(call.args[0], 'browse/play_stream')
            if 'pid' in call.kwargs:
                self.assertEqual(call.kwargs['pid'], 1491570931)
        renderer.load_track.assert_called_once()
        self.assertEqual(renderer.load_track.call_args.args[1:], (7.035, 12345))
        renderer.action.assert_any_call('Play', Speed=1)
        client.close.assert_called_once()

    def test_track_metadata_declares_a_finite_music_track(self):
        renderer = Renderer.__new__(Renderer)
        renderer.action = Mock()
        renderer.load_track('http://pi/laugh.mp3', 125.25, 12345)
        call = renderer.action.call_args_list[0]
        self.assertEqual(call.args[0], 'SetAVTransportURI')
        metadata = ET.fromstring(call.kwargs['CurrentURIMetaData'])
        self.assertEqual(metadata.find('.//{*}class').text, 'object.item.audioItem.musicTrack')
        resource = metadata.find('.//{*}res')
        self.assertEqual(resource.attrib['duration'], '0:02:05.250')
        self.assertEqual(resource.attrib['size'], '12345')
        renderer.action.assert_any_call('SetPlayMode', NewPlayMode='NORMAL')

    def test_already_playing_own_track_is_ignored_without_queued_restart(self):
        board = Soundboard(CONFIG, simulate=True, log=lambda *args: None)
        client, renderer = Mock(), Mock()
        client.command.side_effect = [
            {'payload': [{'pid': CONFIG['player_id'], 'name': CONFIG['name'], 'ip': CONFIG['host']}]},
            {'payload': []}, {}, {}, {}]
        renderer.action.side_effect = [
            {'CurrentTransportState': 'PLAYING'},
            {'TrackURI': 'http://192.168.178.130:8081/laugh.mp3?play=old'}]
        with patch('tools.heos.Client', return_value=client), \
                patch('tools.heos.Renderer', return_value=renderer):
            board.play_once()
        renderer.load_track.assert_not_called()
        self.assertNotIn('Play', [call.args[0] for call in renderer.action.call_args_list])

    def test_grouped_kitchen_is_rejected_before_any_playback_or_volume_change(self):
        board = Soundboard(CONFIG, simulate=True, log=lambda *args: None)
        client = Mock()
        client.command.side_effect = [
            {'payload': [{'pid': CONFIG['player_id'], 'name': CONFIG['name'], 'ip': CONFIG['host']}]},
            {'payload': [{'players': [{'pid': CONFIG['player_id']}, {'pid': 1378018644}]}]}]
        with patch('tools.heos.Client', return_value=client):
            with self.assertRaisesRegex(RuntimeError, 'grouped'):
                board.play_once()
        self.assertEqual([c.args[0] for c in client.command.call_args_list],
                         ['player/get_players', 'group/get_groups'])

    def test_rapid_ok_presses_do_not_queue_or_overlap(self):
        board = Soundboard(CONFIG, simulate=True, log=lambda *args: None)
        board.simulate = False
        started, release = threading.Event(), threading.Event()
        def play():
            started.set()
            release.wait(1)
        board.play_once = Mock(side_effect=play)
        board.worker = threading.Thread(target=board.run)
        board.worker.start()
        try:
            self.assertTrue(board.trigger())
            self.assertTrue(started.wait(1))
            pressed_during_playback = time.time()
            for _ in range(100):
                self.assertFalse(board.trigger())
            release.set()
            deadline = time.monotonic() + 1
            while board.busy and time.monotonic() < deadline:
                time.sleep(.005)
            self.assertFalse(board.busy)
            board.play_once.assert_called_once()
            self.assertFalse(board.trigger(pressed_at=pressed_during_playback))
            self.assertTrue(board.trigger(pressed_at=time.time()))
        finally:
            release.set()
            board.close()

    def test_http_serves_only_laugh_and_supports_ranges_and_head(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'laugh.mp3'
            path.write_bytes(b'0123456789')
            fetched = threading.Event()
            server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(path, fetched))
            worker = threading.Thread(target=server.serve_forever)
            worker.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                request = Request(base + '/laugh.mp3', headers={'Range': 'bytes=2-5'})
                with urlopen(request, timeout=2) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.read(), b'2345')
                self.assertTrue(fetched.is_set())
                with urlopen(Request(base + '/laugh.mp3', method='HEAD'), timeout=2) as response:
                    self.assertEqual(response.headers['Content-Length'], '10')
                    self.assertEqual(response.read(), b'')
                for suffix in ('/../config/show.json', '/laugh.mp3/../secret'):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(base + suffix, timeout=2)
                    self.assertEqual(error.exception.code, 404)
            finally:
                server.shutdown()
                worker.join()
                server.server_close()


if __name__ == '__main__':
    unittest.main()
