class Citation():
    def __init__(self, refId, offset):
        self.refId = refId
        self.offset = offset
    
    def toStr(self):
        return '[' + self.refId + ']'


class CitationDB():
    def __init__(self):
        self.offsets = []
        self.byOffset = {}
        self.byRefId = {}
    
    def addCitation(self, citation):
        offset = citation.offset
        if offset not in self.offsets:
            self.offsets.append(offset)
            self.byOffset[offset] = []
        self.byOffset[offset].append(citation)
        if citation.refId not in self.byRefId:
            self.byRefId[citation.refId] = []
        self.byRefId[citation.refId].append(citation)
    
    def writeTo(self, out):
        for offset in self.offsets:
            for citation in self.byOffset[offset]:
                out.write(str(offset) + '\t' + citation.refId + '\n')
    
    def citationsByOffset(self, offset):
        return self.byOffset[offset]
    
    def renameRefId(self, refId, newId):
        if newId in self.byRefId:
            raise Exception('Duplicate reference id!')
        for citation in self.byRefId[refId]:
            citation.refId = newId
        self.byRefId[newId] = self.byRefId[refId]
        del self.byRefId[refId]
    
    def size(self):
        return sum([len(self.byRefId[x]) for x in self.byRefId])
