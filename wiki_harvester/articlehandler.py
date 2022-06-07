import os.path
from xml import sax
from zipfile import ZipFile

import mwparserfromhell

from wiki_harvester.citrefsrc import codeToSources, codeToText, codeToReferences, makePrettyText


class ArticleHandler(sax.ContentHandler):
    def __init__(self, maxCounter, path, metaOut):
        self.currentTag = ""
        self.inPage = False
        self.counter = 0
        self.hasRedirect = False
        self.title = ''
        self.wikicode = ''
        self.maxCounter = maxCounter
        self.ns = ''
        self.metaOut = metaOut
        self.path = path
        self.wikiid = ''
        self.idFinished = False
    
    def startElement(self, tag, attributes):
        if tag == 'page':
            self.inPage = True
        elif tag == 'redirect':
            self.hasRedirect = True
        self.currentTag = tag
    
    def endElement(self, tag):
        self.currentTag = ""
        if tag == 'id':
            self.idFinished = True
        elif tag == 'page':
            if not self.hasRedirect:
                self.completePage()
            self.inPage = False
            self.hasRedirect = False
            self.title = ''
            self.wikicode = ''
            self.ns = ''
            self.wikiid = ''
            self.idFinished = False
    
    def characters(self, content):
        if self.inPage and self.currentTag == 'title':
            self.title = self.title + content
        elif self.inPage and self.currentTag == 'text':
            self.wikicode = self.wikicode + content
        elif self.inPage and self.currentTag == 'ns':
            self.ns = self.ns + content
        elif self.inPage and self.currentTag == 'id' and not self.idFinished:
            self.wikiid = self.wikiid + content
    
    def completePage(self):
        self.counter = self.counter + 1
        print(str(self.counter) + " " + self.title)
        if self.ns != '0':
            print("Non article, skipping.")
        else:
            wiki = mwparserfromhell.parse(self.wikicode)
            
            # Generate sources, references and citations
            sources = codeToSources(wiki)
            references = codeToReferences(wiki, sources)
            text, citations = codeToText(wiki, sources, references)
            
            # Clean everything
            references.clean1()
            sources.clean(references)
            references.clean2(citations)
            prettyText = makePrettyText(text, citations)
            
            # Regenerate text
            if sources.size() == 0:
                print("No sources, skip.")
            else:
                out = open(self.path + str(self.counter) + '_sources.txt', 'w')
                sources.writeTo(out)
                out.close()
                
                out = open(self.path + str(self.counter) + '_references.txt', 'w')
                references.writeTo(out)
                out.close()
                
                out = open(self.path + str(self.counter) + '_citations.txt', 'w')
                citations.writeTo(out)
                out.close()
                
                out = open(self.path + str(self.counter) + '_text.txt', 'w')
                out.write(text)
                out.close()
                
                out = open(self.path + str(self.counter) + '.txt', 'w')
                out.write(self.title + '\n\n')
                out.write(prettyText)
                out.close()
                
                self.metaOut.write(str(
                    self.counter) + "\t" + self.title + "\t" + self.wikiid + "\t" + str(len(text)) + "\t" + str(
                    sources.size()) + "\t" + str(references.size()) + "\t" + str(citations.size()) + "\n")
        
        if self.counter % self.maxCounter == 0:
            self.completeBatch()
    
    def completeBatch(self):
        batchNo = format(self.counter / self.maxCounter, '.0f')
        zipObj = ZipFile(self.path + 'batch' + batchNo + '.zip', 'w')
        for filename in os.listdir(self.path):
            if filename.endswith(".txt"):
                zipObj.write(self.path + filename, filename)
        for filename in os.listdir(self.path):
            if filename.endswith(".txt"):
                os.remove(self.path + filename)
        zipObj.close()

