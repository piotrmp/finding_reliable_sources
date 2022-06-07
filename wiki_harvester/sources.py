class Source():
    def __init__(self, sourceId, content):
        self.id = sourceId
        self.content = content
    
    def toStr(self):
        return self.content.strip().replace('\t', ' ').replace('\n', ' ')


class SourceDB():
    def __init__(self):
        self.byId = {}
        self.byContent = {}
    
    def generateSourceId(self, source):
        return "SRC_" + str(len(self.byId))
    
    def addSource(self, sourceId, content):
        source = Source(sourceId, content)
        if source.id is None:
            source.id = self.generateSourceId(source)
        if source.id in self.byId:
            print('WARNING: skipping duplicate source ID = ' + source.id)
            return
        if source.content in self.byContent:
            if self.byContent[source.content].id.startswith('SRC_') and not source.id.startswith('SRC_'):
                # Replacing source identified by content with one identified by name
                pass
            else:
                # print('WARNING: skipping duplicate source content = ' + source.content)
                return
        self.byId[source.id] = source
        self.byContent[source.content] = source
    
    def writeTo(self, out):
        for key in self.byId:
            out.write(key + '\t' + self.byId[key].toStr() + '\n')
    
    def idByContent(self, content):
        return self.byContent[content].id
    
    def hasId(self, sourceId):
        return sourceId in self.byId
    
    def hasContent(self, sourceText):
        return sourceText in self.byContent
    
    def simplifyId(self, id):
        if id.startswith('SRC_'):
            return id
        elif id.startswith('CITEREF'):
            return 'C' + id[len('CITEREF'):]
        else:
            return 'N' + id
    
    def clean(self, references):
        # Remove sources with no references
        newById = {}
        for refId in references.byId:
            for sourceId in references.byId[refId].sourceIds:
                newById[sourceId] = self.byId[sourceId]
        if len(newById) != len(self.byId):
            print("Removing " + str(len(self.byId) - len(newById)) + " sources...")
        self.byId = newById
        self.byContent = None
        # Rename source
        newById = {}
        renamingMap = {}
        for sourceId in self.byId:
            newSourceId = self.simplifyId(sourceId)
            if newSourceId != sourceId and newSourceId not in self.byId:
                source = self.byId[sourceId]
                source.id = newSourceId
                if newSourceId in newById:
                    raise Exception('Name conflict in source renaming!')
                newById[newSourceId] = source
                renamingMap[sourceId] = newSourceId
            else:
                newById[sourceId] = self.byId[sourceId]
        for refId in references.byId:
            for i in range(len(references.byId[refId].sourceIds)):
                if references.byId[refId].sourceIds[i] in renamingMap:
                    references.byId[refId].sourceIds[i] = renamingMap[references.byId[refId].sourceIds[i]]
        self.byId = newById
    
    def size(self):
        return len(self.byId)
    
    def idByInclusion(self, parts):
        result = []
        for key in self.byId:
            content = self.byId[key].content
            if key.startswith('SRC_'):
                continue
            if includesAll(content, parts):
                result.append(key)
        return result


def includesAll(content, parts):
    for part in parts:
        if part not in content:
            return False
    return True
