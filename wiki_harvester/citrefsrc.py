import re

import mwparserfromhell.nodes as nodes

from wiki_harvester.citations import CitationDB, Citation
from wiki_harvester.references import ReferenceDB
from wiki_harvester.sources import SourceDB
from wiki_harvester.templateparsing import paramValueByNames, rTemplateExtract, wikiciteTemplateExtract, \
    citationTemplateExtract, \
    citeTemplateExtract, sfnTemplateExtract, sfnmTemplateExtract, harvsTemplateExtract, onlyText, findSourceByText


# GATHER ALL MENTIONS OF SOURCES
def codeToSources(wiki):
    print("Scanning sources...")
    sources = SourceDB()
    findSources(wiki, sources)
    return sources


def findSources(wiki, sources):
    for node in wiki.nodes:
        if isinstance(node, nodes.wikilink.Wikilink):
            # If link, look inside its text
            if node.text is not None:
                findSources(node.text, sources)
        elif isinstance(node, nodes.external_link.ExternalLink):
            # The same with external links
            if node.title is not None:
                findSources(node.title, sources)
        elif isinstance(node, nodes.tag.Tag):
            # Firstly, let's explore the inside
            findSources(node.contents, sources)
            tag = str(node.tag)
            if tag == 'ref':
                text = str(node.contents)
                if text != "":
                    # If non-empty <ref>, add the text as source
                    sources.addSource(None, text)
        elif isinstance(node, nodes.template.Template):
            name = str(node.name).strip().lower()
            if name == 'refn':
                content = paramValueByNames(node)
                # Firstly, let's explore the inside
                if content != '':
                    findSources(content, sources)
                text = str(content)
                if text != "":
                    # Add the content as source
                    sources.addSource(None, text)
            elif name == 'reflist':
                if node.has('refs'):
                    # Values of refs in {{reflist}} are potential sources
                    findSources(node.get('refs').value, sources)
            elif name == 'wikicite':
                # Parse the wikicite template and add if has anchor
                anchor, source = wikiciteTemplateExtract(node)
                if anchor == '':
                    sources.addSource(None, str(source))
                else:
                    sources.addSource(anchor, str(source))
            elif name == 'citation':
                # Parse the citation template and add if has anchor
                anchor, source = citationTemplateExtract(node)
                if anchor == '':
                    sources.addSource(None, str(source))
                else:
                    sources.addSource(anchor, str(source))
            elif name.startswith("cite "):
                # Parse the cite template and add if has anchor
                anchor, source = citeTemplateExtract(node)
                if anchor == '':
                    sources.addSource(None, str(source))
                else:
                    sources.addSource(anchor, str(source))
            else:
                # Greedy search for sources -- even if you don't understand the template, explore the unnamed parameters
                for param in node.params:
                    findSources(param.value, sources)


# GATHER ALL REFERENCES IN TEXT
gPagerefCounter = 0


def codeToReferences(wiki, sources):
    print("Scanning references...")
    global gPagerefCounter
    gPagerefCounter = 0
    references = ReferenceDB()
    findReferences(wiki, sources, references)
    if gPagerefCounter > 0:
        print("WARNING: page includes {{rp}} or {{r}} -- page indication ignored.")
    return references


def findReferences(wiki, sources, references):
    global gPagerefCounter
    for node in wiki.nodes:
        if isinstance(node, nodes.wikilink.Wikilink):
            # If link, look inside its text
            if node.text is not None:
                findReferences(node.text, sources, references)
        elif isinstance(node, nodes.external_link.ExternalLink):
            # The same with external links
            if node.title is not None:
                findReferences(node.title, sources, references)
        elif isinstance(node, nodes.tag.Tag):
            tag = str(node.tag)
            if tag == 'ref':
                # Add reference from this <ref>
                addReferenceViaRef(node, sources, references)
            else:
                # Other tags: just look inside
                findReferences(node.contents, sources, references)
        elif isinstance(node, nodes.template.Template):
            name = str(node.name).strip()
            if name == 'refn':
                # Add reference from this {{refn}}
                addReferenceViaRef(node, sources, references)
                content = paramValueByNames(node, [''])
                if content != '':
                    # It may have nested references, look inside
                    findReferences(content, sources, references)
            elif name.lower() == 'reflist':
                if node.has('refs'):
                    # Look in the {{reflist refs=...}} in case there are references there
                    findReferences(node.get('refs').value, sources, references)
            elif name.lower() in ['harvard citation no brackets', 'harvnb', 'harvard citation', 'harv',
                                  'harvard citation text', 'harvtxt', 'harvcoltxt', 'harvcol', 'harvcolnb', 'harvp',
                                  'sfn', 'sfnp']:
                # Regular short format reference
                anchor, coord = sfnTemplateExtract(node)
                addReferenceViaSourceAnchors([anchor], [coord], sources, references, str(node))
            elif name.lower() == 'sfnm' or name.lower() == 'sfnmp':
                # Multi-source short format reference
                anchors, coords = sfnmTemplateExtract(node)
                addReferenceViaSourceAnchors(anchors, coords, sources, references, str(node))
            elif name.lower() == 'harvs' or name.lower() == 'harvard citations':
                # Multi-year short format reference
                anchors, coords = harvsTemplateExtract(node)
                addReferenceViaSourceAnchors(anchors, coords, sources, references, str(node))
            elif name == 'r' or name == 'rp':
                gPagerefCounter = gPagerefCounter + 1
            else:
                # Greedy search for references -- even if you don't understand the template, look inside
                for param in node.params:
                    findReferences(param.value, sources, references)


# Browse the contents of a <ref> or {{refn}} in search of source identifiers
def exploreReference(wiki, sources,aggresive=False):
    anchors = []
    coords = []
    for node in wiki.nodes:
        if isinstance(node, nodes.wikilink.Wikilink):
            if str(node.title).startswith("#"):
                # Local link may be a source identifier...
                anchor = str(node.title)[1:]
                if anchor.startswith("CITEREF"):
                    anchor = "CITEREF" + anchor[len("CITEREF"):].lower()
                if sources.hasId(anchor):
                    # .. if there's a source with matching anchor
                    anchors = anchors + [anchor]
                    coords = coords + ['']
            elif node.text is not None:
                # Otherwise look inside
                a, c = exploreReference(node.text, sources)
                anchors = anchors + a
                coords = coords + c
        elif isinstance(node, nodes.external_link.ExternalLink):
            # If external link, look inside
            if node.title is not None:
                a, c = exploreReference(node.title, sources)
                anchors = anchors + a
                coords = coords + c
        elif isinstance(node, nodes.tag.Tag):
            # If tag, look inside
            a, c = exploreReference(node.contents, sources)
            anchors = anchors + a
            coords = coords + c
        elif isinstance(node, nodes.template.Template):
            name = str(node.name).strip()
            if name == 'refn':
                content = paramValueByNames(node, [''])
                if str(content) != '':
                    # If refn, look inside
                    a, c = exploreReference(content, sources)
                    anchors = anchors + a
                    coords = coords + c
            elif name.lower() in ['harvard citation no brackets', 'harvnb', 'harvard citation', 'harv',
                                  'harvard citation text', 'harvtxt', 'harvcoltxt', 'harvcol', 'harvcolnb', 'harvp',
                                  'sfn', 'sfnp']:
                # If short-format citation, add source id accordingly
                a, c = sfnTemplateExtract(node)
                if a != '':
                    anchors = anchors + [a]
                    coords = coords + [c]
            elif name.lower() == 'sfnm' or name.lower() == 'sfnmp':
                # same for multiple-source references
                a, c = sfnmTemplateExtract(node)
                if a != '':
                    anchors = anchors + a
                    coords = coords + c
            elif name.lower() == 'harvs' or name.lower() == 'harvard citations':
                # and for multi-year ones.
                a, c = harvsTemplateExtract(node)
                if a != '':
                    anchors = anchors + a
                    coords = coords + c
    if len(anchors)==0 and aggresive and onlyText(wiki):
        anchors,coords=findSourceByText(wiki,sources)
    return anchors, coords


# Add reference mentioned through <ref> or {{refn}}
def addReferenceViaRef(node, sources, references):
    refId = None
    if isinstance(node, nodes.tag.Tag):
        content = node.contents
    else:
        content = paramValueByNames(node)
    text = str(content)
    if text.strip() == '':
        # Empty contents, no need to add reference (citation will be added here later)
        return
    if node.has('name'):
        # If it has a name, create refID
        name = nodeToText(node.get('name').value, False)
        refId = name
    # Look inside for source mentions
    anchors, coords = exploreReference(content, sources,aggresive=True)
    if len(anchors) == 0:
        # If not found, get source id by content
        if not sources.hasContent(text):
            print("WARNING: unable to find source by content: " + text)
        else:
            anchors = [sources.idByContent(text)]
        coords = None
    for sourceId in anchors:
        if not sources.hasId(sourceId):
            print('WARNING: source missing for anchor ' + str(sourceId))
            return
    if len(anchors) != 0:
        references.addReference(refId, anchors, coords, str(node))


def addReferenceViaSourceAnchors(anchors, coords, sources, references, string):
    for sourceId in anchors:
        if not sources.hasId(sourceId):
            print('WARNING: source missing for anchor ' + str(sourceId))
            return
    references.addReference(None, anchors, coords, string)


# GENERATE TEXT WHILE PUTTING CITATIONS IN IT
def codeToText(wiki, sources, references):
    print("Scanning text...")
    citations = CitationDB()
    text = nodeToText(wiki, True, sources, references, citations)
    return text, citations


# Ignore text under these headers
blackHeaders = ['References', 'Sources', 'Citations', 'Notes', 'Further reading', 'External links', 'See also',
                'Footnotes', 'Gallery']


def nodeToText(wiki, addCitations, sources=None, references=None, citations=None):
    result = ""
    if wiki is None:
        return result
    blackLevel = 0
    for node in wiki.nodes:
        if isinstance(node, nodes.heading.Heading):
            text = nodeToText(node.title, False).strip()
            if blackLevel == 0 and (text in blackHeaders):
                # If new black-listed header was found, remember it
                blackLevel = node.level
            elif blackLevel > 0 and node.level <= blackLevel:
                # If under black-listed header and higher-order header found, overwrite
                if text in blackHeaders:
                    blackLevel = node.level
                else:
                    blackLevel = 0
            if blackLevel == 0:
                result = result + text + "\n"
        # If black-listed, skip generating text
        if blackLevel > 0:
            continue
        elif isinstance(node, nodes.text.Text):
            # Text found, just add
            text = str(node)
            if text != '\n':
                result = result + str(node)
        elif isinstance(node, nodes.external_link.ExternalLink):
            # For external links, prefer title, if defined
            if node.title is not None:
                text = nodeToText(node.title, addCitations, sources, references, citations)
            else:
                text = nodeToText(node.url, addCitations, sources, references, citations)
            result = result + text
        elif isinstance(node, nodes.wikilink.Wikilink):
            title = nodeToText(node.title, addCitations, sources, references, citations)
            # Ignore local links to files
            if title.startswith("File:") or title.startswith("Image:"):
                pass
            # Otherwise use text, if defined
            elif node.text is None:
                if ":" not in title:
                    result = result + title
            else:
                result = result + nodeToText(node.text, addCitations, sources, references, citations)
        elif isinstance(node, nodes.html_entity.HTMLEntity):
            # Normalise HTML entities (nbsp's and such)
            result = result + node.normalize()
        elif isinstance(node, nodes.tag.Tag):
            tag = str(node.tag)
            if tag == 'b' or tag == 'i':
                # Look inside these
                result = result + nodeToText(node.contents, addCitations, sources, references, citations)
            elif tag == 'li':
                # Convert li to textual item
                result = result + '-'
            elif tag == 'ref' and addCitations:
                # If ref, try to get name
                name = nodeToText(node.get('name').value, False) if node.has('name') else ''
                string = str(node)
                # Create textual representation of citation based on name or content and add
                addCitationByNameOrString(name, string, references, citations, len(result))
        elif isinstance(node, nodes.template.Template):
            tname = str(node.name).strip()
            if tname == 'quote':
                value = paramValueByNames(node, ['', 'text', '1', 'quote'])
                if value == '':
                    print("WARNING: malformed quote: " + str(node))
                else:
                    # For {{quote}}, look inside these parameters
                    result = result + nodeToText(paramValueByNames(node, ['', 'text', '1', 'quote']),
                                                 addCitations,
                                                 sources,
                                                 references, citations)
            elif tname == 'refn' and addCitations:
                # For {{refn}}, the same as <ref>
                name = nodeToText(node.get('name').value, False) if node.has('name') else ''
                string = str(node)
                addCitationByNameOrString(name, string, references, citations, len(result))
            elif tname == 'r' and addCitations:
                # For {{r}} the same, but may be many references (ignore pages)
                refNames, refPages = rTemplateExtract(node)
                for i in range(len(refNames)):
                    addCitationByNameOrString(str(refNames[i]), str(node), references, citations, len(result))
            elif tname.lower() in ['harvard citation no brackets', 'harvnb', 'harvard citation', 'harv',
                                   'harvard citation text', 'harvtxt', 'harvcoltxt', 'harvcol', 'harvcolnb', 'harvp',
                                   'sfn', 'sfnp', 'sfnm', 'sfnmp', 'harvs', 'harvard citations'] and addCitations:
                # Short citations added via content
                addCitationByNameOrString('', str(node), references, citations, len(result))

    return result


def makePrettyText(text, citations):
    result = ''
    prevOffset = 0
    for offset in sorted(citations.offsets):
        for citation in citations.citationsByOffset(offset):
            result = result + text[prevOffset:offset]
            result = result + citation.toStr()
            prevOffset = offset
    # Clean a bit
    result = result.replace("()", "")
    result = result.replace("  ", " ")
    result = re.sub(r'\n\n+', '\n\n', result).strip()
    return result


# Convert reference to citation
def addCitationByNameOrString(name, string, references, citations, offset):
    if name != '':
        # if non-empty name, use it
        refId = name
        if not references.hasId(refId):
            print('WARNING: Attempt to cite unknown reference: ' + name)
            return
        reference = references.refById(refId)
        reference.cite()
        citations.addCitation(Citation(reference.id, offset))
    elif string != '':
        # otherwise, find reference by string
        if not references.hasString(string):
            print('WARNING: Unable to find reference by string: ' + string)
            return
        reference = references.refByString(string)
        reference.cite()
        citations.addCitation(Citation(reference.id, offset))
