import sys
import time
import traceback
from os import listdir

import numpy as np
import pandas as pd

import evaluation_tools as eval_tools
import ranking as rank
from elasticsearch import Elasticsearch

from sparse_indexer.find_sources import findPredictedSources

prefix = sys.argv[1]
sentencePath = prefix + 'sentences/2021s'
mappingPath = None
metaPath = prefix + 'corpus/2021/meta.tsv'

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
        
        test_case: bool = (idd in test_idd_set)  # czy dany idd jest w zb testowym czy nie
        
        for source_aux in sources:
            src = source_aux.strip()
            if src == '':
                continue
            if test_case:
                test_set_references.add(src)
            else:
                train_set_references.add(src)

intersect = test_set_references.intersection(train_set_references)

server = "http://localhost:9200"
index = "test"
client = Elasticsearch(server)
print(client.ping())

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
            predicted_sources = []
            try:
                predicted_sources = findPredictedSources(query, client, index, n_search_results)
            except Exception as e:
                print("EXCEPTION for query=" + query)
                traceback.print_exc(file=sys.stdout)
            
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

