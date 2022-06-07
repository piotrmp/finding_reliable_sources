import io
import sys
from os import listdir
from zipfile import ZipFile

from source_explorer.normalise import normalise

corpusPath = sys.argv[1]

idsourcesOld = set()
idsourcesNew = set()
sumS = 0
sumR = 0
sumC = 0
sumW = 0


def countNormalisedSources(srcFile):
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
        norms = normalise(source, None)
        if norms != []:
            for norm in norms:
                idsourcesNew.add(norm)
                if norm.startswith('ISBN:') or norm.startswith('DOI:'):
                    idsourcesOld.add(norm)
    return all


def countReferences(refFile):
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
    return all


def countCitations(citFile):
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
    return all


def ingestFile(citFile, refFile, srcFile, txtFile):
    global sumS, sumR, sumC, sumW
    sources = countNormalisedSources(srcFile)
    references = countReferences(refFile)
    citations = countCitations(citFile)
    words = txtFile.read().count(' ')
    # print("Sources: " + str(sources) + " References: " + str(references) + " Citations: " + str(citations) + " Words: " + str(words))
    sumS = sumS + sources
    sumR = sumR + references
    sumC = sumC + citations
    sumW = sumW + words


for section in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
    for filename in sorted(listdir(corpusPath + '/' + section), key=lambda x: int(x.rstrip('.zip').lstrip('batch'))):
        if not filename.endswith('.zip'):
            continue
        print("Processing " + corpusPath + '/' + section + '/' + filename)
        zipObj = ZipFile(corpusPath + '/' + section + '/' + filename, 'r')
        for name in sorted(zipObj.namelist(), key=lambda x: int(x.rstrip('.txt_text_citations_references_sources'))):
            if not name.endswith('_text.txt'):
                continue
            j = int(name[:-(len('_text.txt'))])
            mainFileName = str(j) + '.txt'
            if mainFileName not in zipObj.namelist():
                print("File " + mainFileName + " missing, moving on.")
                continue
            mainFile = io.TextIOWrapper(zipObj.open(str(j) + '.txt'))
            citFile = io.TextIOWrapper(zipObj.open(str(j) + '_citations.txt'))
            refFile = io.TextIOWrapper(zipObj.open(str(j) + '_references.txt'))
            srcFile = io.TextIOWrapper(zipObj.open(str(j) + '_sources.txt'))
            txtFile = io.TextIOWrapper(zipObj.open(str(j) + '_text.txt'))
            ingestFile(citFile, refFile, srcFile, txtFile)
            mainFile.close()
            citFile.close()
            refFile.close()
            srcFile.close()
            txtFile.close()
        zipObj.close()

######## Wikipedia Complete Citation Corpus
print("Sources: " + str(sumS))
print("References: " + str(sumR))
print("Citations: " + str(sumC))
print("Words: " + str(sumW))
print("Old source identifiers: " + str(len(idsourcesOld)))
print("All source identifiers: " + str(len(idsourcesNew)))

sourcesCited = 0
citations = 0
idsources = set()
idsourcesO = set()
sentencePath = sys.argv[2]  # 'data/learntocite/sentences/2021s'
for filename in sorted(listdir(sentencePath), key=lambda x: int(x.rstrip('.tsv').lstrip('batch'))):
    if not filename.endswith('.tsv'):
        continue
    print("Reading " + filename)
    for line in open(sentencePath + '/' + filename):
        parts = line.strip().split('\t')
        sourcesCited = sourcesCited + (len(parts) - 2)
        citations = citations + 1
        for source in parts[2:]:
            idsources.add(source)
            if source.startswith('DOI:') or source.startswith('ISBN:'):
                idsourcesO.add(source)
                if source not in idsourcesOld:
                    print(line + '=>' + source)

######## Learning to Cite Dataset
print("Citations: " + str(citations))
print("Sources per citation: " + str(sourcesCited / citations))
print("Different sources: " + str(len(idsources)))
print("Different sources old: " + str(len(idsourcesO)))
