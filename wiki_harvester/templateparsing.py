import re

from mwparserfromhell import nodes


def onlyText(wiki):
    for node in wiki.nodes:
        if isinstance(node, nodes.text.Text):
            pass
        elif isinstance(node, nodes.tag.Tag) and str(node.tag) in ['b', 'i']:
            if not onlyText(node.contents):
                return False
        else:
            return False
    return True


def findSourceByText(wiki, sources):
    text = str(wiki).replace('&nbsp;', ' ')
    parts = re.split('\\W+', text)
    validParts = []
    for part in parts:
        if part.lower() in ['p', 'pp', 'page', 'pages', 'vol', 'chapter', 'chapters', 'citing']:
            break
        elif len(part) >= 4:
            validParts.append(part)
    if len(validParts) > 0:
        sourceIds = sources.idByInclusion(validParts)
        if len(sourceIds) == 1:
            return sourceIds, ['']
    return [], []


def sfnrefTemplateExtract(node):
    anchor = ''
    for param in node.params:
        if not param.showkey:
            anchor = anchor + str(param.value).strip()
    return anchor


def parseRefAnchor(wiki):
    result = ''
    for node in wiki.nodes:
        if isinstance(node, nodes.text.Text):
            result = result + str(node)
        elif isinstance(node, nodes.template.Template):
            tname = str(node.name)
            if tname.lower() == 'sfnref' or tname.lower() == 'harvid':
                result = result + 'CITEREF' + sfnrefTemplateExtract(node)
    result = result.strip()
    if result.startswith('CITEREF'):
        result = 'CITEREF' + result[len('CITEREF'):].lower()
    # else:
    #    result = result.lower()
    result = result.replace(' ', '_')
    return (result)


def paramValueByNames(node, names=['']):
    for param in node.params:
        for name in names:
            if (not param.showkey and name == '') or name == str(param.name):
                return param.value
    return ''


def rTemplateExtract(node):
    refNames = []
    refPages = []
    unnamedMode = False
    for param in node.params:
        if not param.showkey:
            unnamedMode = True
    if unnamedMode:
        for param in node.params:
            if not param.showkey:
                refNames.append(param.value)
        refPages.append(paramValueByNames(node, ['p', 'pp', 'page', 'pages']))
    else:
        count = 0
        for param in node.params:
            if str(param.name)[1:].isdigit():
                thiscount = int(str(param.name)[1:])
                if thiscount > count:
                    count = thiscount
        refNames = [''] * count
        refPages = [''] * count
        for i in range(count):
            refNames[i] = paramValueByNames(node, [str(i + 1)])
            refPages[i] = paramValueByNames(node, ['p' + str(i + 1)])
    if len(refNames) != len(refPages):
        print("WARNING: unable to parse {r}: " + str(node))
        refNames = []
        refPages = []
    return (refNames, refPages)


def wikiciteTemplateExtract(node):
    anchor = ''
    if node.has('ref'):
        anchor = parseRefAnchor(node.get('ref').value)
    elif node.has('id'):
        anchor = 'Reference-' + parseRefAnchor(node.get('id').value)
    source = ''
    if node.has('reference'):
        source = node.get('reference').value
    return anchor, source


def hasNotEmpty(node, key):
    return node.has(key) and str(node.get(key).value).strip() != ''


def citeTemplateExtract(node):
    anchor = None
    if node.has('ref'):
        value = parseRefAnchor(node.get('ref').value)
        if value == 'harv':
            anchor = None
        else:
            anchor = value
    if anchor is None:
        anchor = getAnchor(node)
    return anchor, str(node)


def citationTemplateExtract(node):
    anchor = None
    if node.has('ref'):
        value = parseRefAnchor(node.get('ref').value)
        if value == 'none':
            anchor = ''
        elif value == 'harv':
            anchor = None
        else:
            anchor = value
    if anchor is None:
        anchor = getAnchor(node)
    return anchor, str(node)


def getAnchor(node, yearSuffix=''):
    author = ''
    if hasNotEmpty(node, 'last') or hasNotEmpty(node, 'last1'):
        for i in range(4):
            key = 'last' + str(i + 1)
            if node.has(key):
                author = author + str(node.get(key).value).strip()
                continue
            if i == 0:
                key = 'last'
                if node.has(key):
                    author = author + str(node.get(key).value).strip()
    elif hasNotEmpty(node, 'author'):
        author = str(node.get('author').value).strip()
    elif hasNotEmpty(node, 'editor-last') or hasNotEmpty(node, 'editor1-last') or hasNotEmpty(node, 'editor-last1'):
        for i in range(4):
            key = 'editor-last' + str(i + 1)
            if node.has(key):
                author = author + str(node.get(key).value).strip()
                continue
            key = 'editor' + str(i + 1) + '-last'
            if node.has(key):
                author = author + str(node.get(key).value).strip()
                continue
            if i == 0:
                key = 'editor-last'
                if node.has(key):
                    author = author + str(node.get(key).value).strip()
    elif hasNotEmpty(node, 'editor'):
        author = str(node.get('editor').value).strip()
    year = ''
    if hasNotEmpty(node, 'year' + yearSuffix):
        year = str(node.get('year' + yearSuffix).value).strip()
    elif yearSuffix != '':
        pass
    elif hasNotEmpty(node, 'date'):
        year = dateToYear(str(node.get('date').value))
    elif hasNotEmpty(node, 'publication-date'):
        year = dateToYear(str(node.get('publication-date').value))
    if author != '':
        anchor = 'CITEREF' + (author + year).lower()
    else:
        # print('WARNING: unable to generate anchor for citation: ' + str(node))
        anchor = ''
    anchor = anchor.replace('\n', ' ').replace('\t', ' ').replace(' ', '_')
    return (anchor)


def dateToYear(date):
    date = date.strip()
    if re.fullmatch('\d\d\d\d-\d\d-\d\d', date):
        year = date[:4]
    elif re.fullmatch('\d\d\d\d\D', date):
        year = date
    else:
        year = date[-4:]
        if date != '' and not year.isdigit():
            print("WARNING: unexpected date format: " + date)
    return year


def sfnTemplateExtract(node):
    anchor = ''
    if node.has('ref'):
        anchor = parseRefAnchor(node.get('ref').value)
    else:
        for param in node.params:
            if not param.showkey:
                anchor = anchor + str(param.value).strip()
        if anchor != '':
            anchor = 'CITEREF' + anchor.lower()
    if anchor == '':
        print('WARNING: unable to generate anchor from {{sfn}}: ' + str(node))
    coord = ''
    for parName in ['p', 'pp', 'loc']:
        if node.has(parName):
            if coord != '':
                coord = coord + ' '
            coord = coord + parName + '. ' + str(node.get(parName).value).strip()
    anchor = anchor.replace(' ', '_')
    return anchor, coord


def sfnmTemplateExtract(node):
    pars = {}
    counter = 0
    for param in node.params:
        if not param.showkey:
            rest = counter % 2
            if rest == 0:
                name = format((counter - rest) / 2 + 1, '.0f') + 'a1'
            else:
                name = format((counter - rest) / 2 + 1, '.0f') + 'y'
            pars[name] = param
            counter = counter + 1
        else:
            pars[str(param.name)] = param
    anchors = []
    coords = []
    for ii in range(100):
        i = ii + 1
        if str(i) + 'a1' not in pars:
            break
        anchor = ''
        for jj in range(4):
            j = jj + 1
            if str(i) + 'a' + str(j) not in pars:
                break
            anchor = anchor + str(pars[str(i) + 'a' + str(j)].value).strip()
        if str(i) + 'y' not in pars:
            print("WARNING: malformed {{sfnm}}: " + str(node))
            break
        anchor = anchor + str(pars[str(i) + 'y'].value).strip()
        anchor = 'CITEREF' + anchor.lower()
        coord = ''
        for parName in ['p', 'pp', 'loc']:
            if str(i) + parName in pars:
                if coord != '':
                    coord = coord + ' '
                coord = coord + parName + '. ' + str(pars[str(i) + parName].value).strip()
        anchor = anchor.replace(' ', '_')
        anchors.append(anchor)
        coords.append(coord)
    return anchors, coords


def harvsTemplateExtract(node):
    anchors = []
    coords = []
    for ii in range(100):
        if ii == 0:
            yearsuffix = ''
        else:
            yearsuffix = str(ii + 1)
        if not node.has('year' + yearsuffix):
            break
        anchor = getAnchor(node, yearsuffix)
        if anchor == '':
            print('WARNING: unable to generate anchor from {{harvs}}: ' + str(node))
        coord = ''
        for parName in ['otherpage', 'loc', 'loc1', 'loc2']:
            if node.has(parName):
                if coord != '':
                    coord = coord + ' '
                desc = 'loc'
                if parName == 'otherpage':
                    desc = 'p'
                coord = coord + desc + '. ' + str(node.get(parName).value).strip()
        anchor = anchor.replace(' ', '_')
        anchors.append(anchor)
        coords.append(coord)
    return anchors, coords
