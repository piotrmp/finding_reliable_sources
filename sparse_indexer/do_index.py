import json
import sys

from elasticsearch import Elasticsearch

from sparse_indexer.source_documents import generateSourceDocuments

server = "http://localhost:9200"
index = "test"

prefix = sys.argv[1]
sentencePath = prefix + '/sentences/2021s'
metaPath = prefix + '/corpus/2021/metaTrain.tsv'
claimsPath = prefix + '/representations/claims/2021s'

client = Elasticsearch(server)
print(client.ping())

sourceDocuments = generateSourceDocuments(metaPath, sentencePath)
sourceDocuments = {id: sourceDocuments[id] for id in sourceDocuments if sourceDocuments[id] != ''}


def storeSources(client, index, sourceIds, sourceTexts):
    bulk = "\n".join(
        ['{ "index" : { "_index" : "' + index + '" } }\n' + json.dumps({"id": sourceIds[i], "text": sourceTexts[i]}) for
         i in range(len(sourceIds))])
    isStored = True
    try:
        outcome = client.bulk(bulk)
        # print(outcome)
    except Exception as ex:
        print('Error in indexing data')
        print(str(ex))
        isStored = False
    finally:
        return isStored


mapping = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "text": {"type": "text"}
        }
    }
}

result = client.indices.delete(index=index, ignore=[400, 404])
print(result)

result = client.indices.create(index=index, body=mapping)
print(result)

tried = 0
currentIds = []
currentDocs = []
for sourceId in sourceDocuments:
    currentIds.append(sourceId)
    currentDocs.append(sourceDocuments[sourceId])
    if len(currentIds) == 1000:
        result = storeSources(client, index, currentIds, currentDocs)
        if not result:
            break
        currentIds = []
        currentDocs = []
    tried = tried + 1
    if tried % 10000 == 0:
        print(str(int(tried / 1000)) + 'k')

result = storeSources(client, index, currentIds, currentDocs)

client.indices.refresh(index=index)

result = client.search(index=index, body={"query": {"match_all": {}}})
print("Got %d Hits:" % result['hits']['total']['value'])
for hit in result['hits']['hits']:
    print(hit["_source"])
