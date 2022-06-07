import sys
import time

from embedder.encoder import Encoder
from dense_indexer.index import Index

pathPrefix = sys.argv[1]

indexPath = pathPrefix + 'index/2021s_sb'
sentencePath = pathPrefix + 'sentences/2021s'
mappingPath = None
metaPath = pathPrefix + 'corpus/2021/metaTrain.tsv'
embeddingsPath = pathPrefix + 'embeddings/2021s_sb'
# model = 'average_word_embeddings_glove.6B.300d'
# model = 'distilbert-base-nli-mean-tokens'
model = 'universal-sentence-encoder-v4'
encoder = Encoder(model)

index = Index(indexPath, sentencePath, mappingPath, metaPath, encoder)

index.clear()

index.load()

start_time = time.time()
index.addSentencesEmbedded(embeddingsPath)
print("--- %s seconds ---" % (time.time() - start_time))

index.save()
