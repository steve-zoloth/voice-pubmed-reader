import unittest
from unittest.mock import patch
import voice_pubmed_bot as bot
from nova_speech import control


class MoreResultsTests(unittest.TestCase):
    def test_search_uses_offset(self):
        with patch.object(bot.Entrez,'esearch') as search, patch.object(bot.Entrez,'esummary'), patch.object(bot.Entrez,'read',side_effect=[{'IdList':['6']},[{'Title':'Six.'}]]):
            self.assertEqual(bot.search_pubmed('trial',start=5),(['Six'],['6']))
        search.assert_called_once_with(db='pubmed',term='trial',retmax=5,retstart=5)

    def test_more_jumps_to_new_results_and_previous_still_works(self):
        titles=['One','Two'];ids=['1','2']
        with patch.object(bot,'listen_for_speech',side_effect=['more results','previous','next','next']), patch.object(bot,'search_pubmed',side_effect=[(['Three'],['3']),([],[])]) as search, patch.object(bot,'speak') as speak:
            bot.navigate_results(titles,ids,query='trial')
        self.assertEqual([c.kwargs['start'] for c in search.call_args_list],[2,3])
        spoken=[c.args[0] for c in speak.call_args_list]
        self.assertIn('Article 3: Three',spoken)
        self.assertIn('Article 2: Two',spoken)
        self.assertEqual(ids,['1','2','3'])

    def test_next_at_end_loads_another_page(self):
        with patch.object(bot,'listen_for_speech',side_effect=['next','next']), patch.object(bot,'search_pubmed',side_effect=[(['Two'],['2']),([],[])]), patch.object(bot,'speak') as speak:
            bot.navigate_results(['One'],['1'],query='trial')
        self.assertIn('Article 2: Two',[c.args[0] for c in speak.call_args_list])

    def test_failed_page_retries_same_offset(self):
        with patch.object(bot,'listen_for_speech',side_effect=['more','next']), patch.object(bot,'search_pubmed',side_effect=[RuntimeError('retry'),([],[])]) as search, patch.object(bot,'speak'):
            bot.navigate_results(['One'],['1'],query='trial')
        self.assertEqual([c.kwargs['start'] for c in search.call_args_list],[1,1])

    def test_duplicates_do_not_advance_article_numbers(self):
        titles=['One'];ids=['1']
        with patch.object(bot,'listen_for_speech',side_effect=['more','next']), patch.object(bot,'search_pubmed',side_effect=[(['One','Two'],['1','2']),([],[])]) as search, patch.object(bot,'speak'):
            bot.navigate_results(titles,ids,query='trial')
        self.assertEqual(ids,['1','2'])
        self.assertEqual([c.kwargs['start'] for c in search.call_args_list],[1,3])

    def test_more_command_while_reading(self):
        self.assertEqual(control('Reader, more results please.'),'more')
        self.assertEqual(control('Show more results'),'more')
        self.assertEqual(control('next five'),'more')

if __name__=='__main__': unittest.main()
