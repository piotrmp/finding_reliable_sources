from os import listdir


def generateSourceDocuments(metaPath, sentencePath):
    idds = set()
    for line in open(metaPath):
        parts = line.split('\t')
        idd = int(parts[0])
        idds.add(idd)
    sourceDocuments = {}
    for filename in sorted(listdir(sentencePath), key=lambda x: int(x.rstrip('.tsv').lstrip('batch'))):
        if not filename.endswith('.tsv'):
            continue
        print("Reading " + filename)
        for line in open(sentencePath + '/' + filename):
            parts = line.split('\t')
            idd = int(parts[0])
            if idd not in idds:
                continue
            sentence = parts[1].strip()
            for part in parts[2:]:
                sourceId = part.strip()
                if sourceId not in sourceDocuments:
                    sourceDocuments[sourceId] = sentence
                else:
                    sourceDocuments[sourceId] = sourceDocuments[sourceId] + '\n' + sentence
    return sourceDocuments


def generateSourceDocumentsClaims(metaPath, sentencePath, claimsPath):
    idds = set()
    for line in open(metaPath):
        parts = line.split('\t')
        idd = int(parts[0])
        idds.add(idd)
    sourceDocuments = {}
    for filename in sorted(listdir(sentencePath), key=lambda x: int(x.rstrip('.tsv').lstrip('batch'))):
        if not filename.endswith('.tsv'):
            continue
        print("Reading " + filename)
        claimsFile = open(claimsPath + '/' + filename.rstrip('.tsv') + '.txt')
        for line in open(sentencePath + '/' + filename):
            claimsLine = claimsFile.readline()
            parts = line.split('\t')
            idd = int(parts[0])
            if idd not in idds:
                continue
            representation = ' '.join([x.replace(' ', '_') for x in claimsLine.strip().split('\t')])
            for part in parts[2:]:
                sourceId = part.strip()
                if sourceId not in sourceDocuments:
                    sourceDocuments[sourceId] = representation
                else:
                    sourceDocuments[sourceId] = sourceDocuments[sourceId] + '\n' + representation
        claimsFile.close()
    return sourceDocuments
