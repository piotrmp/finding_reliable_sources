import json
import sys

import pandas as pd
from Levenshtein import jaro
import evaluator.evaluation_tools as eval_tools
import fever_tools

pathPrefix = sys.argv[1]

train_fever_path = pathPrefix + 'fever/train.jsonl'
wiki_fever_path = pathPrefix + 'fever/wiki-pages'
metaTrainPath = pathPrefix + 'corpus/2021/metaTrain.tsv' # tutaj jest mapowanie tytulow stron na numery
sentencePath = pathPrefix + 'sentences/2021s'

metaPath = pathPrefix + 'corpus/2021/meta.tsv'

sim_thresh = 0.8
sentences_label = 'REFUTES' # 'SUPPORTS' #
claim_2_evidences_csv = pathPrefix+"FEVER-FRS_REFUTES.csv"

read_file = open(train_fever_path, "r")

sentences_list = [json.loads(jline) for jline in read_file.read().splitlines()]
sentences_list_filtered = []

for sentence in sentences_list:
    if sentence.get('label') == sentences_label:
        sentences_list_filtered.append(sentence)

# I create a set of page titles from WikiFEVER that match evidences
evidences_set = set() #a compilation of all page titles that are used as evidence
for s in sentences_list_filtered:
    evidences=s.get('evidence')
    for evid in evidences: # evid: is a list that contains all the sources
        for evid2 in evid: # evid2: s single source (list)
            page_title = evid2[2] # page title is on a 3rd place of the list
            evidences_set.add(page_title)

# Create a set of page titles from Wiki Training
meta_train: pd.DataFrame = pd.read_csv(metaTrainPath, '\t', index_col=False, header=None).iloc[:, 0:2]  # select of 1st and 3nd column
meta_train.rename(columns={0: "idd", 1: "titles"}, inplace=True)
meta_train = meta_train.astype({"idd": int, "titles": str})

meta_train.titles: pd.Series = meta_train.titles.apply(lambda x: x.replace(" ", "_")) # change in DataFramie "meta_train" page titles to get FEVER convention
meta_train.titles: pd.Series = meta_train.titles.apply(lambda x: x.replace(")", "-RRB-"))
meta_train.titles: pd.Series = meta_train.titles.apply(lambda x: x.replace("(", "-LRB-"))
mtt_set = set(meta_train.titles) # the set of all page titles in the training set

#Intersection of titles from WikiFEFER (evidences) and WikiTraining
title_intersect: set = mtt_set.intersection(evidences_set)

wikiFEVERpageTitle_2_lines: dict = dict()
wikiPageTile_2_linesAndSources: dict = dict()

# generating hashmaps
wikiFEVERpageTitle_2_lines = fever_tools.create_wikiFever_map(wiki_fever_path, title_intersect)
wikiPageTile_2_linesAndSources: dict = fever_tools.create_wiki_map(sentencePath, meta_train, title_intersect)

claim_2_evidences = list()

for s in sentences_list_filtered:
    actual_sources = []
    evidences = s.get('evidence')
    claim = s.get('claim')

    for evid in evidences:  # evid: is a list that contains all the sources
        for evid2 in evid:  # evid2: s single source (list)
            page_title = evid2[2] # page title is on a 3rd place of the list
            line_num = evid2[3]
            lineId_2_lineText = wikiFEVERpageTitle_2_lines.get(page_title) #here is the entire wikiFever page in the form: "lineId" => "line text"
            if(lineId_2_lineText==None or (len(lineId_2_lineText)==0)):
                continue
            evid_txt = lineId_2_lineText.get((line_num))
            evid_txt = evid_txt.replace("-RRB-", ")").replace("-LRB-", "(").replace("-RSB-", "]").replace("-LSB-", "[")
            evid_txt_no_whitespaces = evid_txt.replace(" ", "")

            #Text search procedure on our Wikipedia
            linesAndSources: list = wikiPageTile_2_linesAndSources.get(page_title)
            if(linesAndSources == None):
                continue

            maxsim = -1
            lineAndSource_maxsim = -1
            for line_source in linesAndSources:
                sim = jaro(line_source[0].replace(" ", ""), evid_txt_no_whitespaces) #Skipping spaces
                if (sim > maxsim):
                    maxsim = sim
                    lineAndSource_maxsim = line_source

            if(maxsim>sim_thresh): #we consider that the found line corresponds to the one from the evidence
                stripped = [s.strip() for s in lineAndSource_maxsim[1]]
                actual_sources.extend(stripped) #merge of two lists

    if len(actual_sources) == 0:
        continue
    actual_sources = eval_tools.remove_duplicates(actual_sources)
    claim_2_evidences.append((claim,actual_sources)) #[claim] = actual_sources

# Write claim_2_evidences to csv
with open(claim_2_evidences_csv, 'w') as file:
    for key_isbnList in claim_2_evidences:
        file.write(key_isbnList[0])
        file.write("\t")
        for isbn in key_isbnList[1]:
            file.write(isbn)
            file.write("\t")
        file.write("\n")
