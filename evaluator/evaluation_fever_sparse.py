import json
import sys
import traceback
from builtins import print

import numpy as np
from elasticsearch import Elasticsearch

import evaluator.evaluation_tools as eval_tools
import evaluator.ranking as rank
from sparse_indexer.find_sources import findPredictedSources

pathPrefix = sys.argv[1]

train_fever_path = pathPrefix + 'fever/train.jsonl'
wiki_fever_path = pathPrefix + 'fever/wiki-pages'
metaTrainPath = pathPrefix + 'corpus/2021/metaTrain.tsv'
sentencePath = pathPrefix + 'sentences/2021s'

metaPath = pathPrefix + 'corpus/2021/meta.tsv'

server = "http://localhost:9200"
index = "test"
client = Elasticsearch(server)
print(client.ping())

sim_thresh = 0.8
n_search_results_list = [100]
k_precision = 10
k_ndcg = 10
sentences_label = 'REFUTES'  # 'SUPPORTS' #

### paths to maps in csv form:
claim_2_evidences_SUPPORTS_csv = pathPrefix + "claim_2_evidences_SUPPORTS.csv"
claim_2_evidences_REFUTES_csv = pathPrefix + "claim_2_evidences_REFUTES.csv"

read_file = open(train_fever_path, "r")

sentences_list = [json.loads(jline) for jline in read_file.read().splitlines()]
sentences_list_filtered = []  # filtered according to 'label' == 'SUPPORTS' / 'REFUTES'

for sentence in sentences_list:
    if sentence.get('label') == sentences_label:
        sentences_list_filtered.append(sentence)

wikiFEVERpageTitle_2_lines: dict
wikiPageTile_2_linesAndSources: dict
claim_2_evidences: dict


def claim_2_evidences_lines_read(claim_2_evidences_csv: str):
    claim_2_evidences = dict()
    for line in open(claim_2_evidences_csv):
        parts = line.strip().split('\t')
        claim = str(parts[0])
        actual_sources = list(parts[1:])
        claim_2_evidences[claim] = actual_sources
    return claim_2_evidences


def calculate_measures(precisions_list: list, ndcg_list: list, avg_prec_list: list):
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


if sentences_label == 'REFUTES':
    claim_2_evidences = claim_2_evidences_lines_read(claim_2_evidences_REFUTES_csv)
elif sentences_label == 'SUPPORTS':
    claim_2_evidences = claim_2_evidences_lines_read(claim_2_evidences_SUPPORTS_csv)
else:
    raise ValueError

# Main loop
for n_search_results in n_search_results_list:
    precisions_list = []
    ndcg_list = []
    avg_prec_list = []
    
    for claim, actual_sources in claim_2_evidences.items():
        query = claim
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
        if len(precisions_list) % 50 == 0:
            calculate_measures(precisions_list, ndcg_list, avg_prec_list)
    
    print("sentences_label: ", sentences_label, ";  n_search_results: ", n_search_results)
    calculate_measures(precisions_list, ndcg_list, avg_prec_list)
