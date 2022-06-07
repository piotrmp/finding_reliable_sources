import io
import sys
from os import listdir
from zipfile import ZipFile

import spacy

from source_explorer.normalise import normalise

nlp = spacy.load("en_core_web_sm")

corpusPath = sys.argv[1]
metaPath = corpusPath + '/../meta.tsv'
outPath = sys.argv[2]

askGoogle = None
useContext = "sentence+sentence"

titles = {}
for line in open(metaPath):
    parts = line.split('\t')
    idd = int(parts[0])
    title = parts[1]
    titles[idd] = title


def readNormalisedSources(srcFile):
    result = {}
    all = 0
    while True:
        line = srcFile.readline()
        if line == '':
            break
        parts = line.split('\t')
        if len(parts) != 2:
            print("WARNING: malformed line " + line)
            continue
        all = all + 1
        idd = parts[0]
        source = parts[1].strip()
        norms = normalise(source, askGoogle)
        if norms != []:
            result[idd] = norms
    print("Have " + str(len(result)) + " normalised (" + str(all) + " all) source ids.")
    return result


def readNormalisedReferences(refFile, sources):
    result = {}
    all = 0
    while True:
        line = refFile.readline()
        if line == '':
            break
        parts = line.split('\t')
        if len(parts) < 3 or len(parts) % 2 == 0:
            print("WARNING: malformed line " + line)
            continue
        all = all + 1
        idd = parts[0]
        for i in range(int((len(parts) - 1) / 2)):
            sourceId = parts[i * 2 + 1]
            if sourceId in sources:
                if idd not in result:
                    result[idd] = []
                result[idd].append(sourceId)
    print("Have " + str(len(result)) + " normalised (" + str(all) + " all) references.")
    return result


def readNormalisedCitations(citFile, references):
    result = []
    all = 0
    while True:
        line = citFile.readline()
        if line == '':
            break
        parts = line.split('\t')
        if len(parts) != 2:
            print("WARNING: malformed line " + line)
            continue
        all = all + 1
        offset = int(parts[0])
        refId = parts[1].strip()
        if refId in references:
            result.append((offset, refId))
    print("Have " + str(len(result)) + " normalised (" + str(all) + " all) citations.")
    return result


def getContext(text, sentenceStarts, sentenceEnds, i, title, contextType):
    if contextType == "sentence":
        return text[sentenceStarts[i]:sentenceEnds[i]].strip()
    elif contextType == "title+sentence":
        return title + ". " + text[sentenceStarts[i]:sentenceEnds[i]].strip()
    elif contextType == "sentence+sentence":
        ii = i
        if ii > 0:
            ii = ii - 1
        return text[sentenceStarts[ii]:sentenceEnds[i]].strip()


def distillFile(index, citFile, refFile, srcFile, txtFile, contextType, out):
    sources = readNormalisedSources(srcFile)
    references = readNormalisedReferences(refFile, sources)
    citations = readNormalisedCitations(citFile, references)
    text = txtFile.read()
    doc = nlp(text)
    title = titles[int(index)]
    print(title)
    currCitation = 0
    sentenceStarts = []
    sentenceEnds = []
    for sentence in doc.sents:
        if len(sentence.text) > 5 or sentenceStarts == []:
            sentenceStarts.append(sentence.start_char)
            sentenceEnds.append(sentence.end_char)
        else:
            sentenceEnds[-1] = sentence.end_char
    
    for i in range(len(sentenceStarts)):
        citationsHere = []
        sourcesHere = []
        while currCitation < len(citations) and citations[currCitation][0] <= sentenceEnds[i]:
            for srcId in references[citations[currCitation][1]]:
                sourcesHere.extend(sources[srcId])
            citationsHere.append(citations[currCitation])
            currCitation = currCitation + 1
        if citationsHere != []:
            context = getContext(text, sentenceStarts, sentenceEnds, i, title, contextType)
            out.write(index + '\t' + context.replace('\n', ' ').replace('\t', ' ').strip())
            for source in sourcesHere:
                out.write("\t" + source)
            out.write('\n')
        if currCitation == len(citations):
            break


for filename in sorted(listdir(corpusPath), key=lambda x: int(x.rstrip('.zip').lstrip('batch'))):
    if not filename.endswith('.zip'):
        continue
    print("Processing " + corpusPath + '/' + filename)
    zipObj = ZipFile(corpusPath + '/' + filename, 'r')
    out = open(outPath + '/' + filename[:-4] + '.tsv', 'w')
    for name in sorted(zipObj.namelist(), key=lambda x: int(x.rstrip('.txt_text_citations_references_sources'))):
        if not name.endswith('_text.txt'):
            continue
        j = int(name[:-(len('_text.txt'))])
        mainFileName = str(j) + '.txt'
        if mainFileName not in zipObj.namelist():
            print("File " + mainFileName + " missing, moving on.")
            continue
        print("Processing " + str(j))
        mainFile = io.TextIOWrapper(zipObj.open(str(j) + '.txt'))
        citFile = io.TextIOWrapper(zipObj.open(str(j) + '_citations.txt'))
        refFile = io.TextIOWrapper(zipObj.open(str(j) + '_references.txt'))
        srcFile = io.TextIOWrapper(zipObj.open(str(j) + '_sources.txt'))
        txtFile = io.TextIOWrapper(zipObj.open(str(j) + '_text.txt'))
        distillFile(str(j), citFile, refFile, srcFile, txtFile, useContext, out)
        mainFile.close()
        citFile.close()
        refFile.close()
        srcFile.close()
        txtFile.close()
    out.close()
    zipObj.close()
