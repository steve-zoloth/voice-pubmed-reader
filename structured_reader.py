"""Structured source retrieval for the optional reader; legacy retrieval is unchanged."""
import xml.etree.ElementTree as ET
import voice_pubmed_bot as backend

def text(node):
    return ' '.join(''.join(node.itertext()).split()) if node is not None else ''

def abstract(pmid):
    with backend.Entrez.efetch(db='pubmed', id=pmid, retmode='xml') as handle:
        root = ET.fromstring(handle.read())
    article = root.find('.//Article')
    if article is None:
        return [], ''
    sections = [(node.get('Label') or node.get('NlmCategory') or 'Abstract', text(node))
                for node in article.findall('./Abstract/AbstractText') if text(node)]
    authors = []
    for author in article.findall('./AuthorList/Author'):
        name = text(author.find('CollectiveName')) or ' '.join(filter(None, [text(author.find('ForeName')), text(author.find('LastName'))]))
        if name:
            authors.append(name)
    return sections, '; '.join(authors) or 'No author information available.'

def full_text(pmid):
    pmcid = backend.get_pmc_id(pmid)
    if not pmcid:
        return []
    with backend.Entrez.efetch(db='pmc', id=pmcid, rettype='full', retmode='xml') as handle:
        root = ET.fromstring(handle.read())
    body = root.find('.//body')
    if body is None:
        return []
    sections = []
    def walk(node, heading):
        for child in node:
            if child.tag == 'sec':
                walk(child, text(child.find('title')) or heading)
            elif child.tag == 'p' and text(child):
                sections.append((heading, text(child)))
            elif child.tag not in ('title', 'fig', 'table-wrap'):
                walk(child, heading)
    walk(body, 'Full text')
    return sections


def result_count(query):
    with backend.Entrez.esearch(db='pubmed', term=query, retmax=0) as handle:
        return int(backend.Entrez.read(handle)['Count'])


def publication_types(pmids):
    if not pmids:
        return {}
    with backend.Entrez.efetch(db='pubmed', id=','.join(pmids), retmode='xml') as handle:
        root = ET.fromstring(handle.read())
    return {text(article.find('./MedlineCitation/PMID')):
            [text(node) for node in article.findall('./MedlineCitation/Article/PublicationTypeList/PublicationType')]
            for article in root.findall('.//PubmedArticle')}
