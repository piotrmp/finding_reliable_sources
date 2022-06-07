from os import listdir

import ngtpy
import numpy as np

SEGMENT_SIZE = 1000


class Index():
    def __init__(self, indexPath, sentencePath, mappingPath, metaPath, encoder):
        self.indexPath = indexPath
        self.sentencePath = sentencePath
        self.mappingPath = mappingPath
        self.encoder = encoder
        self.readTitles(metaPath)
    
    def clear(self):
        ngtpy.create(self.indexPath, self.encoder.getDim(), distance_type='Normalized Cosine')
        mappingFile = open(self.mappingPath, 'w')
        mappingFile.close()
    
    def addSentencesEmbedded(self, embeddedPath):
        for filename in sorted(listdir(self.sentencePath), key=lambda x: int(x.rstrip('.tsv').lstrip('batch'))):
            if not filename.endswith('.tsv'):
                continue
            print("Reading " + filename)
            matrix = np.load(embeddedPath + '/' + filename.rstrip('.tsv') + '.npy')
            print("Adding to index...")
            lineCounter = 0
            for line in open(self.sentencePath + '/' + filename):
                lineCounter = lineCounter + 1
                parts = line.split('\t')
                idd = int(parts[0])
                if idd not in self.titles:
                    # print('Skipping sentence from doc '+str(idd))
                    continue
                vector = matrix[lineCounter - 1]
                if np.count_nonzero(vector) == 0:
                    vector[0] = 1
                idd = self.ngtIndex.insert(vector)
                self.mapping[idd] = (filename, lineCounter)
        print("Rebuilding index...")
        self.ngtIndex.build_index(22)
    
    def readTitles(self, metaPath):
        self.titles = {}
        for line in open(metaPath):
            parts = line.split('\t')
            idd = int(parts[0])
            title = parts[1]
            self.titles[idd] = title
    
    def load(self):
        self.ngtIndex = ngtpy.Index(self.indexPath)
        self.mapping = {}
        for line in open(self.mappingPath):
            parts = line.split('\t')
            filename = parts[0]
            linenumber = int(parts[1])
            idd = int(parts[2].strip())
            self.mapping[idd] = (filename, linenumber)
    
    def search(self, sentence, num=10):
        # print('Searching for ' + sentence)
        embedding = self.encoder.encode([sentence])[0]
        searchResult = self.searchInternal(embedding, num)
        results = []
        for sResult in searchResult[:num]:
            idd = sResult[0]
            location = self.mapping[idd]
            fp = open(self.sentencePath + '/' + location[0])
            for i, line in enumerate(fp):
                if i == location[1] - 1:
                    results.append(line.strip())
                    break
            fp.close()
        return results
    
    def searchInternal(self, embedding, num):
        if np.count_nonzero(embedding) == 0:
            embedding[0] = 1
        # Avoid anomalous results for very low num
        if num < 0:
            number = 10
        else:
            number = num
        searchResult = self.ngtIndex.search(embedding, number)
        return searchResult
    
    def save(self):
        self.ngtIndex.save()
        mappingFile = open(self.mappingPath, 'w')
        for key in self.mapping:
            filename, lineNumber = self.mapping[key]
            mappingFile.write(filename + '\t' + str(lineNumber) + '\t' + str(key) + '\n')
        mappingFile.close()
    
    def get(self, idd):
        return self.ngtIndex.get_object(idd)
    
    def getTitle(self, idd):
        return self.titles[idd]
