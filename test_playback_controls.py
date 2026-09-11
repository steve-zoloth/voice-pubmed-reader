import asyncio
import json
import threading
import time
import unittest
from unittest.mock import Mock, patch
import muse_stt
from nova_speech import control
from playback_controls import PlaybackControls


class CommandTests(unittest.TestCase):
    def listener(self): return PlaybackControls(7)

    def test_polite_commands_and_speaker_prefix(self):
        for phrase, expected in [('Please pause.', 'pause'), ('Reader, could you pause please?', 'pause'), ('Resume reading', 'resume'), ('Reader slow down', 'slower'), ('clinical results were similar reader stop reading', 'stop')]:
            self.assertEqual(control(phrase), expected)
        for phrase in ['patients pause treatment', 'do not stop reading', '5', 'a faster response was reported']:
            self.assertIsNone(control(phrase))

    def test_early_pause_only_once_per_turn(self):
        c = self.listener()
        c._transcript('Reader pause', False)
        self.assertEqual(c.get(.01), 'pause')
        c._transcript('Reader pause', False)
        c._transcript('Reader pause please', True)
        self.assertIsNone(c.get(.01))
        c._transcript('Reader resume', True)
        self.assertEqual(c.get(.01), 'resume')

    def test_attention_before_finished_command(self):
        c = self.listener()
        c._transcript('Study result reader', False)
        self.assertEqual(c.get(.01), 'attention')
        c._transcript('Study result reader', False)
        self.assertIsNone(c.get(.01))
        c._transcript('Study result reader pause', False)
        self.assertEqual(c.get(.01), 'pause')

    def test_skip_waits_for_complete_phrase(self):
        c = self.listener()
        c._transcript('Reader next', False)
        self.assertIsNone(c.get(.01))
        c._transcript('Reader next paragraph', True)
        self.assertEqual(c.get(.01), 'forward')

    def test_feedback_audio_is_ignored(self):
        c = self.listener()
        c.muted.set(); c._transcript('Reader stop', False)
        c.muted.clear(); c._transcript('Reader stop', True)
        self.assertIsNone(c.get(.01))
        c._transcript('Reader pause', True)
        self.assertEqual(c.get(.01), 'pause')

    def test_clean_close_and_selected_microphone(self):
        seen = []
        def stream(device, on_text, ready, stop, muted):
            seen.append(device); ready(); stop.wait(2)
        with patch.object(muse_stt, 'stream_commands', side_effect=stream):
            c = self.listener().start(); c.close()
        self.assertEqual(seen, [7])
        self.assertFalse(c.thread.is_alive())


class StreamingTests(unittest.IsolatedAsyncioTestCase):
    async def test_multiple_turns_share_connection_and_survive_silence(self):
        events = iter([
            {'sessionId':'test'}, asyncio.TimeoutError(),
            {'type':'speechStart'}, {'type':'transcript','transcript':'Reader pause'},
            {'type':'speechComplete','transcript':'Reader pause'},
            asyncio.TimeoutError(), {'type':'speechStart'},
            {'type':'transcript','transcript':'Reader resume'},
            {'type':'speechComplete','transcript':'Reader resume'},
        ])
        class Finished(Exception): pass
        class Socket:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): pass
            async def send(self, data): pass
            async def recv(self):
                event = next(events, None)
                if event is None: raise Finished()
                if isinstance(event, Exception): raise event
                return json.dumps(event)
        observed=[]; ready=Mock()
        stream = Mock(); stream.__enter__=Mock(return_value=stream);stream.__exit__=Mock(return_value=False)
        with patch.dict('os.environ', {'MODEL_API_KEY':'test-only'}), patch.object(muse_stt.websockets, 'connect', return_value=Socket()) as connect, patch.object(muse_stt.sd, 'RawInputStream', return_value=stream) as mic:
            with self.assertRaises(Finished):
                await muse_stt._record_utterance(7,2,60,on_text=lambda t,f: observed.append((t,f)),on_ready=ready)
        self.assertEqual([t for t,f in observed if f], ['Reader pause','Reader resume'])
        self.assertEqual(connect.call_count,1)
        self.assertEqual(mic.call_args.kwargs['device'],7)
        ready.assert_called_once()

    async def test_one_shot_returns_first_turn_as_before(self):
        events = iter([{'sessionId':'test'}, {'type':'speechStart'}, {'type':'speechComplete','transcript':'heart failure'}])
        class Socket:
            async def __aenter__(self): return self
            async def __aexit__(self,*a): pass
            async def send(self,data): pass
            async def recv(self): return json.dumps(next(events))
        stream=Mock();stream.__enter__=Mock(return_value=stream);stream.__exit__=Mock(return_value=False)
        with patch.dict('os.environ', {'MODEL_API_KEY':'test-only'}), patch.object(muse_stt.websockets,'connect',return_value=Socket()), patch.object(muse_stt.sd,'RawInputStream',return_value=stream):
            text=await muse_stt._record_utterance(7,2,60)
        self.assertEqual(text,'heart failure')


if __name__ == '__main__': unittest.main()
