import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import realtime_adapter as rt

class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.reader = rt.Reader()
        for name, value in [('result_count', 42), ('publication_types', {'1':['Review'], '2':['Journal Article']})]:
            mocked = patch.object(rt.structured_reader, name, return_value=value)
            mocked.start()
            self.addCleanup(mocked.stop)
    def search(self):
        with patch.object(rt.backend, 'search_pubmed', return_value=(['One','Two'],['1','2'])):
            self.reader.execute('search', 'sarcopenia and elderly males')
    def test_citation_commands_preserve_reading_without_full_text(self):
        self.search()
        self.reader.last = 'Prior passage'
        with patch.object(rt.structured_reader, 'journal', return_value='Medical Journal'), patch.object(rt.structured_reader, 'abstract', return_value=([], 'Jane Smith')), patch.object(rt.structured_reader, 'full_text', side_effect=AssertionError('Must not need PMC')):
            self.assertEqual(self.reader.execute('pmid')['text'], 'PMID: 1.')
            self.assertEqual(self.reader.execute('journal')['text'], 'Medical Journal')
            self.assertEqual(self.reader.execute('authors')['text'], 'Jane Smith')
            citation = self.reader.execute('citation')['text']
            for value in ('One', 'Jane Smith', 'Medical Journal', 'PMID: 1'):
                self.assertIn(value, citation)
            self.assertEqual(self.reader.execute('repeat')['text'], 'Prior passage')

    def test_navigation_and_retry(self):
        self.search()
        self.assertIn('Two', self.reader.execute('next')['text'])
        with patch.object(rt.backend, 'search_pubmed', side_effect=RuntimeError('retry')):
            with self.assertRaises(RuntimeError): self.reader.execute('next')
        self.assertEqual(self.reader.offset, 2)
        with patch.object(rt.backend, 'search_pubmed', return_value=(['Two','Three'], ['2','3'])):
            self.assertIn('Three', self.reader.execute('next')['text'])
        self.assertEqual(self.reader.ids, ['1','2','3'])
        self.assertIn('Two', self.reader.execute('previous')['text'])
    def test_read_repeat_stop_continue_preserves_source(self):
        self.search()
        source=' '.join('word'+str(i) for i in range(400))
        with patch.object(rt.structured_reader, 'abstract', return_value=([('Abstract', source)], 'Authors')):
            first=self.reader.execute('abstract')
        self.reader.execute('stop')
        self.assertEqual(first, self.reader.execute('repeat'))
        self.assertIn('word180', self.reader.execute('continue')['text'])
        self.assertEqual(' '.join(self.reader.chunks), source)
        self.reader.execute('next')
        self.assertIn('Ask for an abstract', self.reader.execute('continue')['text'])
    def test_repeat_survives_information_commands(self):
        self.search()
        with patch.object(rt.structured_reader, 'abstract', return_value=([('Abstract', 'Source passage')], 'Jane Smith')):
            passage = self.reader.execute('abstract')
        for action in ('authors', 'count', 'sections', 'help', 'article_type', 'stop'):
            self.reader.execute(action)
            self.assertEqual(passage, self.reader.execute('repeat'))

    def test_position_uses_total_or_loaded_count(self):
        self.search()
        self.assertIn('Article 2 of 42:', self.reader.execute('next')['text'])
        self.reader.total = None
        self.assertIn('Article 1 of 2 loaded:', self.reader.execute('previous')['text'])

    def test_revisiting_article_reuses_source_but_not_other_article(self):
        self.search()
        with patch.object(rt.structured_reader, 'abstract', return_value=([('Abstract', 'Source')], 'Author')) as fetch:
            first = self.reader.execute('abstract')
            self.reader.execute('next')
            self.reader.execute('abstract')
            self.reader.execute('previous')
            self.assertEqual(first, self.reader.execute('abstract'))
            self.assertEqual(fetch.call_count, 2)

    def test_failed_source_fetch_is_retried(self):
        self.search()
        with patch.object(rt.structured_reader, 'abstract', side_effect=[RuntimeError('network'), ([('Abstract', 'Recovered')], 'Author')]) as fetch:
            with self.assertRaises(RuntimeError):
                self.reader.execute('abstract')
            self.assertIn('Recovered', self.reader.execute('abstract')['text'])
            self.assertEqual(fetch.call_count, 2)

    def test_turn_wait_can_return_to_previous_setting(self):
        with patch.dict(rt.os.environ, {'VOICE_PUBMED_TURN_EAGERNESS': 'auto'}):
            self.assertEqual(rt.session_config()['audio']['input']['turn_detection']['eagerness'], 'auto')

    def test_full_text_fallback(self):
        self.search()
        with patch.object(rt.structured_reader,'full_text',return_value=[]) as full, patch.object(rt.structured_reader,'abstract',return_value=([('Abstract','Abstract text')], 'Authors')):
            self.assertIn('PMC full text unavailable', self.reader.execute('full_text')['text'])
        full.assert_called_once_with('1')
    def test_save_reuses_backend_without_nova(self):
        self.search()
        with tempfile.TemporaryDirectory() as folder, patch.object(rt.backend,'REF_FILE',str(Path(folder)/'refs.txt')), patch.object(rt.backend,'speak') as speak:
            self.reader.execute('save')
            self.assertIn('https://pubmed.ncbi.nlm.nih.gov/1/',(Path(folder)/'refs.txt').read_text())
            speak.assert_not_called()
    def test_sections_authors_and_skips(self):
        self.search()
        sections=[('METHODS', ' '.join('m'+str(i) for i in range(200))), ('RESULTS', 'Important findings'), ('CONCLUSIONS', 'Final conclusion')]
        with patch.object(rt.structured_reader,'abstract',return_value=(sections,'Jane Smith')):
            self.assertNotIn('Jane Smith',self.reader.execute('abstract')['text'])
        self.assertIn('Jane Smith',self.reader.execute('authors')['text'])
        self.assertTrue(self.reader.execute('skip',seconds=10,heard_seconds=4)['text'].startswith('m35'))
        self.assertTrue(self.reader.execute('skip',seconds=10,direction='backward')['text'].startswith('m10'))
        self.assertIn('Important findings',self.reader.execute('section',section='results')['text'])
        self.assertIn('not labeled',self.reader.execute('section',section='limitations')['text'])
        self.assertIn('CONCLUSIONS',self.reader.execute('sections')['text'])
        with self.assertRaises(ValueError): self.reader.execute('skip',seconds=-1)

    def test_counts_and_review_filter(self):
        self.search()
        self.assertEqual(self.reader.execute('count')['text'], '42 articles found. 2 loaded.')
        self.assertIn('Review', self.reader.execute('article_type')['text'])
        with patch.object(rt.backend, 'search_pubmed', return_value=(['Review title'], ['1'])) as search:
            self.reader.execute('reviews')
            self.assertIn('Review[pt]', search.call_args.args[0])
            self.assertEqual(self.reader.base_query, 'sarcopenia and elderly males')
        with patch.object(rt.backend, 'search_pubmed', return_value=([], [])), patch.object(rt.structured_reader,'result_count',return_value=0):
            self.reader.execute('search',query='new topic')
            self.assertEqual(self.reader.execute('count')['text'], '0 articles found. 0 loaded.')

    def test_count_failure_does_not_invent_total(self):
        with patch.object(rt.structured_reader,'result_count',side_effect=RuntimeError()):
            self.search()
            self.assertIn('Total count unavailable', self.reader.execute('count')['text'])

    def test_unknown_and_missing_query(self):
        for command in ['delete','search']:
            with self.assertRaises(ValueError): self.reader.execute(command)
    def test_session_errors_distinguish_quota_from_rate_limit(self):
        import io
        import json
        from urllib.error import HTTPError
        cases = [({'error': {'code': 'credit_balance_exhausted'}}, 'API prepaid credits exhausted'),
                 ({'error': {'code': 'project_spend_limit_exceeded'}}, 'Project spending limit reached'),
                 ({'error': {'code': 'slow_down'}}, 'API rate limit reached'),
                 ({'error': {'code': 'insufficient_quota'}}, 'API quota exhausted'),
                 ({'error': {'code': 'rate_limit_exceeded'}}, 'API rate limit reached'),
                 ({'error': {'message': 'secret-must-not-leak'}}, 'without a recognized reason'),
                 ([], 'without a recognized reason')]
        for body, expected in cases:
            with self.subTest(body=body):
                error = HTTPError('https://api.openai.com/v1/realtime/calls', 429, 'limit', {}, io.BytesIO(json.dumps(body).encode()))
                with patch.dict(rt.os.environ, {'OPENAI_API_KEY': 'test-secret'}), patch.object(rt.urllib.request, 'urlopen', side_effect=error):
                    with self.assertRaisesRegex(RuntimeError, expected) as caught:
                        rt.create_call('v=0')
                self.assertNotIn('secret', str(caught.exception))

    def test_session_interrupts_and_key_stays_server_side(self):
        config=rt.session_config()
        self.assertTrue(config['audio']['input']['turn_detection']['interrupt_response'])
        with patch.dict(rt.os.environ, {'OPENAI_API_KEY':''}):
            with self.assertRaisesRegex(RuntimeError,'OPENAI_API_KEY'): rt.create_call('v=0')

if __name__=='__main__': unittest.main()
