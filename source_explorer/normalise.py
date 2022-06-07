import mwparserfromhell
from mwparserfromhell import nodes


def parseTemplate(node):
    result = {}
    name = str(node.name).strip().lower()
    result['NAME'] = name
    for param in node.params:
        if param.showkey:
            key = str(param.name).strip().lower()
            value = str(param.value).strip()
            result[key] = value
        else:
            key = 'UNNAMED'
            value = str(param.value).strip()
            result[key] = value
    return (result)


def normaliseTemplate(template, askGoogle):
    # First use DOI in template
    if 'doi' in template and template['doi'] != '':
        return 'DOI:' + template['doi']
    if template['NAME'] == 'doi' and 'UNNAMED' in template and template['UNNAMED'] != '':
        return 'DOI:' + template['UNNAMED']
    # Use ISBN, if present
    if 'isbn' in template and template['isbn'] != '':
        return 'ISBN:' + template['isbn'].replace('-', ' ').replace(' ', '')
    if template['NAME'] == 'isbn' and 'UNNAMED' in template and template['UNNAMED'] != '':
        return 'ISBN:' + template['UNNAMED'].replace('-', ' ').replace(' ', '')
    # Use arXiv ID for arXiv templates:
    if template['NAME'] == 'cite arxiv':
        for key in ['arxiv', 'eprint']:
            if key in template and template[key] != '':
                return 'ARXIV:' + template[key]
    # Use URL for all citation templates
    if template['NAME'].startswith('cite ') or template['NAME'] == 'citation':
        for key in ['url', 'chapter-url', 'chapterurl', 'contribution-url', 'contributionurl', 'section-url',
                    'sectionurl']:
            if key in template and template[key] != '':
                return 'URL:' + template[key]
    # Ask google for ISBN for books
    if askGoogle is not None:
        if template['NAME'] in ['cite book', 'citation']:
            title = ''
            if 'title' in template and template['title'] != '':
                title = template['title']
            author = ''
            for key in ['last', 'last1']:
                if key in template and template[key] != '':
                    author = template[key]
            if title != '':
                isbn = askGoogle.askGoogleForISBN(title, author)
                if isbn != '':
                    return 'ISBN:' + isbn.replace('-', ' ').replace(' ', '')
    return ''


def normalise(wikitext, askGoogle=None):
    wiki = mwparserfromhell.parse(wikitext)
    templates = []
    for node in wiki.nodes:
        if isinstance(node, nodes.template.Template):
            parsed = parseTemplate(node)
            if parsed['NAME'] in ['dead link', 'webarchive']:
                continue
            templates.append(parsed)
    result = []
    # Find IDs by templates
    for template in templates:
        norm = normaliseTemplate(template, askGoogle)
        if norm != '' and '{{' not in norm:
            result.append(norm)
    # Find free-standing URLs
    for node in wiki.nodes:
        if isinstance(node, nodes.external_link.ExternalLink):
            if str(node.url) != '' and '{{' not in str(node.url):
                result.append('URL:' + str(node.url))
        elif isinstance(node, nodes.tag.Tag) and str(node.tag) in ['b', 'i']:
            for node2 in node.contents.nodes:
                if isinstance(node2, nodes.external_link.ExternalLink):
                    if str(node2.url) != '' and '{{' not in str(node2.url):
                        result.append('URL:' + str(node2.url))
    
    return result
