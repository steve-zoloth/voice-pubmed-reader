import io
import unittest
from unittest.mock import patch
import structured_reader as sr

class StructuredTests(unittest.TestCase):
    def test_abstract_omits_metadata_and_preserves_inline_text(self):
        xml='<PubmedArticle><Article><ArticleTitle>Title</ArticleTitle><AuthorList><Author><ForeName>Jane</ForeName><LastName>Smith</LastName></Author></AuthorList><Abstract><AbstractText Label="RESULTS">Some <i>useful</i> findings.</AbstractText></Abstract></Article></PubmedArticle>'
        with patch.object(sr.backend.Entrez,'efetch',return_value=io.StringIO(xml)):
            sections,authors=sr.abstract('1')
        self.assertEqual(sections,[('RESULTS','Some useful findings.')])
        self.assertEqual(authors,'Jane Smith')
    def test_nested_full_text_retains_headings_without_duplicate_paragraphs(self):
        xml='<article><body><sec><title>Methods</title><p>First.</p><sec><title>Analysis</title><p>Second.</p></sec></sec><sec><title>Results</title><p>Third.</p></sec></body></article>'
        with patch.object(sr.backend,'get_pmc_id',return_value='1'),patch.object(sr.backend.Entrez,'efetch',return_value=io.StringIO(xml)):
            self.assertEqual(sr.full_text('1'),[('Methods','First.'),('Analysis','Second.'),('Results','Third.')])

    def test_journal_without_abstract_or_full_text(self):
        xml='<PubmedArticle><Article><Journal><Title>Medical Journal</Title></Journal></Article></PubmedArticle>'
        with patch.object(sr.backend.Entrez,'efetch',return_value=io.StringIO(xml)):
            self.assertEqual(sr.journal('1'), 'Medical Journal')
