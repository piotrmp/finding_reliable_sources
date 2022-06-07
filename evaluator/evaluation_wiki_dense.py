import sys
import time
from os import listdir

import numpy as np
import pandas as pd

import evaluation_tools as eval_tools
import ranking as rank
from dense_indexer.index import Index
from embedder.encoder import Encoder

prefix = sys.argv[1]
indexPath = prefix + 'index/2021s_glove'
sentencePath = prefix + 'sentences/2021s'
mappingPath = None
metaPath = prefix + 'corpus/2021/meta.tsv'
# model = 'universal-sentence-encoder-v4'
# model = 'paraphrase-distilroberta-base-v1'
model = 'average_word_embeddings_glove.6B.300d'
encoder = Encoder(model)

metaTestPath = prefix + 'corpus/2021/metaTest.tsv'
metaTrainPath = prefix + 'corpus/2021/metaTrain.tsv'
n_search_results = 1
k_precision = 5
k_ndcg = 5
everyN = 1

print('Collecting documents numbers from the Test Set')
test = pd.read_csv(metaTestPath, '\t', index_col=False, header=None)
test_idd_set = set(test.iloc[:, 0])

test_set_references = set()
train_set_references = set()

for filename in sorted(listdir(sentencePath)):
    print("Reading " + filename)
    for line in open(sentencePath + '/' + filename):
        parts = line.split('\t')
        idd = int(parts[0])
        sources = parts[2:]
        
        test_case: bool = (idd in test_idd_set)
        
        for source_aux in sources:
            src = source_aux.strip()
            if src == '':
                continue
            if test_case:
                test_set_references.add(src)
            else:
                train_set_references.add(src)

intersect = test_set_references.intersection(train_set_references)

index = Index(indexPath, sentencePath, mappingPath, metaPath, encoder)
index.load()
precisions_list = []
ndcg_list = []
avg_prec_list = []

start = time.time()
for filename in sorted(listdir(sentencePath), key=lambda x: int(x.rstrip('.tsv').lstrip('batch'))):
    if not filename.endswith('.tsv'):
        continue
    if int(filename.rstrip('.tsv').lstrip('batch')) % everyN != 0:
        continue
    print("Reading " + filename)
    for line in open(sentencePath + '/' + filename):
        parts = line.strip().split('\t')
        docId = int(parts[0])
        if docId not in test_idd_set:
            continue
        else:
            actual_sources = []
            predicted_sources = []
            sources = parts[2:]
            
            for src_aux in sources:
                src = src_aux.strip()
                if src == '':
                    continue
                
                if src in intersect:
                    actual_sources.append(src)
                else:
                    continue
            
            if len(actual_sources) == 0:
                continue
            query = parts[1]
            results = index.search(query, n_search_results)
            for result in results:
                parts2 = result.split('\t')
                # docId2 = int(parts2[0])
                for source2 in parts2[2:]:
                    predicted_sources.append(source2)
            
            predicted_sources = eval_tools.remove_duplicates(predicted_sources)
            prec = eval_tools.precision(actual_sources, predicted_sources, k_precision)
            precisions_list.append(prec)
            # print(prec)
            ndcg = rank.ndcg_at([predicted_sources], [actual_sources], k_ndcg)
            ndcg_list.append(ndcg)
            # print(ndcg)
            avg_prec = rank.mean_average_precision([predicted_sources], [actual_sources])
            avg_prec_list.append(avg_prec)
            # print(avg_prec)
            if len(precisions_list) % 100 == 0:
                print("Number of calculated precisions value:" + str(len(precisions_list)))
                np_array = np.array(precisions_list)
                print(["Mean of precision: ", "{0:.4f} ({1:.4f})".format(np.mean(np_array), np.std(np_array))])
                ##
                np_array = np.array(ndcg_list)
                print(["Mean of ndcg: ", "{0:.4f} ({1:.4f})".format(np.mean(np_array), np.std(np_array))])
                ##
                np_array = np.array(avg_prec_list)
                print(["Mean of average_precision (MAP): ",
                       "{0:.4f} ({1:.4f})".format(np.mean(np_array), np.std(np_array))])

print("END")
print("Number of calculated precisions value:" + str(len(precisions_list)))
np_array = np.array(precisions_list)
print(["Mean of precision: ", "{0:.4f} ({1:.4f})".format(np.mean(np_array), np.std(np_array))])
##
np_array = np.array(ndcg_list)
print(["Mean of ndcg: ", "{0:.4f} ({1:.4f})".format(np.mean(np_array), np.std(np_array))])
##
np_array = np.array(avg_prec_list)
print(["Mean of average_precision (MAP): ",
       "{0:.4f} ({1:.4f})".format(np.mean(np_array), np.std(np_array))])

end = time.time()
print((end - start) / 60)

