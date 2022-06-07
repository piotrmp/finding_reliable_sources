def findPredictedSources(sentence, client, index, size):
    result = []
    response = client.search(index=index, body={"query": {"match": {"text": {"query": sentence}}}}, size=size)
    for item in response['hits']['hits']:
        result.append(item["_source"]['id'])
    return result
