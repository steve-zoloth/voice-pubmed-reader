"""Offline voice-first regression tests. No keys, microphone, or network."""
import contextlib
import io
import threading
import time
import unittest
from unittest.mock import Mock, patch
import voice_pubmed_bot as bot
from nova_speech import NovaAudio, Reading, control, segments


def eventually(predicate):
    deadline = time.monotonic() + 2
    while not predicate():
        if time.monotonic() > deadline:
            raise AssertionError('Timed out waiting for playback state')
        time.sleep(.01)


class FakePlayer:
    def __init__(self, audio):
        self.audio = audio
        self.position = 42
        self.running = False
        self.speed = 1
    def play(self): self.running = True
    def pause(self): self.running = False
    def stop(self): self.running = False
    def playing(self): return self.running
    def rate(self, value): self.speed = value


class PlaybackTests(unittest.TestCase):
    def reading(self, text='First paragraph.\n\nSecond paragraph.'):
        source = Mock()
        source.synthesize.side_effect = lambda text: text
        reading = Reading(text, source, FakePlayer).start()
        self.addCleanup(reading.stop)
        eventually(lambda: reading.player is not None)
        return reading

    def test_pause_resume_preserve_position_and_speed(self):
        r = self.reading()
        player = r.player
        r.pause()
        time.sleep(.08)
        self.assertEqual(r.index, 0)
        self.assertFalse(player.running)
        r.change_speed(.25)
        r.resume()
        self.assertIs(r.player, player)
        self.assertEqual(player.position, 42)
        self.assertTrue(player.running)
        self.assertEqual(player.speed, 1.25)

    def test_paragraph_navigation_and_repeat(self):
        r = self.reading()
        r.paragraph(1)
        eventually(lambda: r.player is not None and r.player.audio == 'Second paragraph.')
        r.paragraph(-1)
        eventually(lambda: r.player is not None and r.player.audio == 'First paragraph.')
        original = r.player
        r.paragraph(0)
        eventually(lambda: r.player is not None and r.player is not original)
        self.assertEqual(r.player.audio, 'First paragraph.')

    def test_stop_during_generation_never_starts_audio(self):
        entered, release = threading.Event(), threading.Event()
        def synth(text):
            entered.set(); release.wait(2); return b'audio'
        source = Mock(); source.synthesize.side_effect = synth
        factory = Mock()
        r = Reading('text', source, factory).start()
        self.assertTrue(entered.wait(1))
        r.stop(); release.set(); r.thread.join(2)
        factory.assert_not_called()

    def test_pause_during_generation_waits_for_resume(self):
        entered, release = threading.Event(), threading.Event()
        def synth(text):
            entered.set(); release.wait(2); return b'audio'
        source = Mock(); source.synthesize.side_effect = synth
        r = Reading('text', source, FakePlayer).start()
        self.addCleanup(r.stop)
        self.assertTrue(entered.wait(1)); r.pause(); release.set()
        eventually(lambda: r.player is not None)
        self.assertFalse(r.player.running)
        r.resume(); self.assertTrue(r.player.running)

    def test_completion_advances_and_finishes(self):
        r = self.reading()
        r.player.running = False
        eventually(lambda: r.index == 1 and r.player is not None)
        r.player.running = False
        self.assertTrue(r.done.wait(1))
        self.assertIsNone(r.error)

    def test_failure_surfaces(self):
        source = Mock(); source.synthesize.side_effect = RuntimeError('unavailable')
        r = Reading('text', source, FakePlayer).start()
        self.assertTrue(r.done.wait(1))
        self.assertIsInstance(r.error, RuntimeError)

    def test_bounded_text_preserves_content_and_paragraphs(self):
        text = ('Medical β numbers 123. ' * 200) + '\n\nConclusion.'
        parts = segments(text)
        self.assertTrue(all(len(t) <= 1200 for _, t in parts))
        self.assertEqual(' '.join(' '.join(t for _,t in parts).split()), ' '.join(text.split()))
        self.assertEqual(parts[-1], (1, 'Conclusion.'))

    def test_cache_and_nova_configuration(self):
        client = Mock(); client.audio.speech.create.return_value.content = b'mp3'
        nova = NovaAudio(client)
        self.assertEqual(nova.synthesize('text'), b'mp3')
        nova.synthesize('text')
        client.audio.speech.create.assert_called_once()
        args = client.audio.speech.create.call_args.kwargs
        self.assertEqual(args['voice'], 'nova')
        self.assertEqual(args['model'], 'gpt-4o-mini-tts')

    def test_exact_commands(self):
        self.assertEqual(control('Reader, pause.'), 'pause')
        self.assertEqual(control('Next paragraph.'), 'forward')
        self.assertIsNone(control('Patients pause medication during treatment.'))

    def test_navigation_and_article_output(self):
        commands = iter(['abstract', 'full text', 'full text', 'next'])
        with patch.object(bot, 'listen_for_speech', side_effect=lambda *a: next(commands)), patch.object(bot, 'fetch_abstract', return_value='Abstract body'), patch.object(bot, 'fetch_full_text', side_effect=['Full body', None]), patch.object(bot, 'speak') as speak, patch.object(bot, 'read_article', return_value=None) as read:
            bot.navigate_results(['Trial title'], ['123'])
        self.assertEqual(speak.call_args_list[0].args[0], 'Article 1: Trial title')
        self.assertEqual([c.args[0] for c in read.call_args_list], ['Abstract: Abstract body','Full body','Abstract body'])

    def test_article_next_returns_to_existing_navigation(self):
        with patch.object(bot,'listen_for_speech',side_effect=['abstract','next']), patch.object(bot,'fetch_abstract',return_value='body'), patch.object(bot,'read_article',return_value='next'), patch.object(bot,'speak') as speak:
            bot.navigate_results(['One','Two'], ['1','2'])
        self.assertIn('Article 2: Two', [c.args[0] for c in speak.call_args_list])

    def test_muse_remains_primary(self):
        with patch.object(bot, '_MUSE_OK', True), patch.object(bot, 'SELECTED_DEVICE', 7), patch.object(bot.muse_stt, 'transcribe_once', return_value='abstract') as muse, patch.object(bot, '_google_once') as google:
            self.assertEqual(bot.capture(), 'abstract')
            muse.assert_called_once_with(device=7, initial_timeout=8.0, max_seconds=45.0)
            google.assert_not_called()

    def test_muse_failure_retains_fallback(self):
        with patch.object(bot, '_MUSE_OK', True), patch.object(bot.muse_stt, 'transcribe_once', side_effect=bot.muse_stt.STTError('test')), patch.object(bot, '_google_once', return_value='next'), patch.object(bot, 'speak'):
            self.assertEqual(bot.capture(), 'next')

if __name__ == '__main__': unittest.main()
