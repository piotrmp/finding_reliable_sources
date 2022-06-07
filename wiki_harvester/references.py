class Reference():
    def __init__(self, refId, sourceIds, locations):
        self.id = refId
        self.sourceIds = sourceIds
        self.locations = locations
        self.cited = False
    
    def toStr(self):
        result = ''
        for i in range(len(self.sourceIds)):
            if i != 0:
                result = result + '\t'
            result = result + self.sourceIds[i]
            loc = ''
            if self.locations is not None:
                loc = self.locations[i]
            result = result + '\t' + loc
        return result
    
    def cite(self):
        self.cited = True
        return self.id


class ReferenceDB():
    def __init__(self):
        self.byId = {}
        self.byString = {}
    
    def hasId(self, refId):
        return refId.lower() in self.byId
    
    def generateRefId(self, reference):
        refId = 'ref'
        for sourceId in reference.sourceIds:
            refId = refId + '_' + sourceId
        if reference.locations is not None:
            refId = refId + "_" + str(sum([x.startswith(refId + '_') for x in self.byId]) + 1)
        return refId
    
    def addReference(self, refId, sourceIds, locations, string):
        reference = Reference(refId, sourceIds, locations)
        if reference.id is None:
            reference.id = self.generateRefId(reference)
        else:
            reference.id = reference.id.lower()
        if reference.id in self.byId:
            # The same reference generated from another citation, no need to add it again
            # print('WARNING: duplicate reference ID = ' + reference.id)
            return
        if string is not None:
            stringId = string
            if stringId in self.byString:
                if refId is None:
                    # Reference identified by destination, no need for duplicate
                    return
                else:
                    print('WARNING: duplicate reference string: ' + string)
            self.byString[stringId] = reference
        self.byId[reference.id] = reference
    
    def refById(self, refId):
        return self.byId[refId.lower()]
    
    def writeTo(self, out):
        for key in self.byId:
            out.write(key + '\t' + self.byId[key].toStr() + '\n')
    
    def hasString(self, string):
        return string in self.byString
    
    def refByString(self, string):
        return self.byString[string]
    
    def simplifyId(self, reference):
        result = ''
        for sourceId in reference.sourceIds:
            result = result + sourceId
        return result
    
    def clean1(self):
        # Remove references that are not cited
        uselessReferences = {}
        for refId in self.byId:
            if not self.byId[refId].cited:
                uselessReferences[refId] = self.byId[refId]
        if len(uselessReferences) != 0:
            print("Removing " + str(len(uselessReferences)) + " references...")
            for refId in uselessReferences:
                del self.byId[refId]
        self.byString = None
    
    def clean2(self, citations):
        # Rename references
        newById = {}
        for refId in self.byId:
            simpleId = self.simplifyId(self.byId[refId])
            if simpleId in newById:
                simpleId = simpleId + '_' + str(sum([x.startswith(simpleId + '_') for x in newById]) + 1)
            self.byId[refId].id = simpleId
            newById[simpleId] = self.byId[refId]
            citations.renameRefId(refId, simpleId)
        self.byId = newById
    
    def size(self):
        return len(self.byId)
