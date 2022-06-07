import sys
import xml.sax as sax

from wiki_harvester.articlehandler import ArticleHandler

outpath = sys.argv[1]
wikipath= sys.argv[2] #'enwiki-20210201-pages-articles.xml'

meta = open(outpath + 'meta.tsv', 'w')
parser = sax.make_parser()
parser.setFeature(sax.handler.feature_namespaces, 0)
handler = ArticleHandler(1000, outpath,meta)
parser.setContentHandler(handler)

parser.parse(wikipath)


handler.completeBatch()
meta.close()
