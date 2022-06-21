from os import listdir
import json
import pandas as pd
import sys
import numpy as np

# create_wikiFever_map
# 1.Funkcja wczytuje z katalogu pliki jsonl z WikipediiFEVER.
# 2. Wybieramy tylko te artykuly, ktorych tytyly stron znajduja sie w zbiorze: "title_intersect"
# 3. Tworzymy slownik : tytul WikiFEVER => (slownik: nr lini => tekst linii). np.: 'Yellow_-LRB-Coldplay_song-RRB-': {0: "`` Yellow '' is a song by British rock band Coldplay ...}
def create_wikiFever_map(wiki_fever_path:str, title_intersect:set):
    wikiTitle_2_lines = dict()
    for filename in sorted(listdir(wiki_fever_path)):
        if not filename.endswith('.jsonl'):
            continue
        print("Reading " + filename)
        wiki_file = open(wiki_fever_path + '/' + filename, "r")
        wiki_sentences: list = [json.loads(jline) for jline in
                                wiki_file.read().splitlines()]  # obiekty postaci: {'id': '', 'text': '', 'lines': ''}
        for wiki_s in wiki_sentences:
            if wiki_s.get('id') in title_intersect:
                wiki_id: str = wiki_s.get("id")
                lines: str = wiki_s.get("lines")
                line_number_2_text = dict()

                for lin in lines.splitlines():
                    aux = lin.split("\t", 1)  # podzial w miejscu pierwszego wystapienia znaku "\t"
                    tekst_linii_PLUS_slowa_kluczowe = aux[1]
                    tekst_linii = tekst_linii_PLUS_slowa_kluczowe.split("\t", 1)[0] #UWAGA: wyrzucam bo, tutaj oprocz tekstu mamy tez slowa kluczowe zaczyjanjace sie od pierwszego \t

                    try:
                        nr_linii = int(aux[0]) #
                        line_number_2_text[nr_linii] = tekst_linii  # w aux[0] jest nr linii
                    except:
                        print("Oops!", sys.exc_info()[0], "occurred for line: ", aux)
                        print("Next entry.")
                        continue

                wikiTitle_2_lines[wiki_id] = line_number_2_text

    return wikiTitle_2_lines

# create_wiki_map
# 1. Tworzymy slownik : tytul Wiki => lista tupli (pojedycznczy tuple zawiera (text linii , zrodla))

def create_wiki_map(sentencePath:str, meta_train: pd.DataFrame, title_intersect:set):
    train_pages_from_intersect = meta_train[meta_train.titles.isin(title_intersect)]  # wybieram strony z Wiki Training, ktore sa w intersect
    idd_from_intersect = set(train_pages_from_intersect.idd)  # idd dla powyzszych stron

    wikiPageTile_2_linesAndSources: dict = dict()

    for filename in sorted(listdir(sentencePath)):
        print("Reading " + filename)
        current_idd = -1
        list_for_current_page = []
        curr_title = ""
        for line in open(sentencePath + '/' + filename):
            parts = line.split('\t')
            idd = int(parts[0])
            sources = parts[2:]
            line_text = parts[1]

            if idd == current_idd:  # kontynuujemy przetwarzanie tego samego (dobrego) dokumentu
                list_for_current_page.append((line_text, sources))  # dodaje tupla (text, zrodla)
            else:  # przeszlismy do kolejnego dokumentu
                if len(list_for_current_page) > 0:  # robie porzadki z poprzednim dokumentem
                    wikiPageTile_2_linesAndSources[curr_title] = list_for_current_page
                    list_for_current_page = []  # UWAGA: to nie zmienia mapy: pageTile_2_linesAndSources -- bo powyzej przy wstawianiu jest robiona kopia tej listy
                if idd in idd_from_intersect:
                    list_for_current_page.append((line_text, sources))  # dodaje tupla (text, zrodla)
                    curr_title = meta_train[meta_train.idd == idd].iloc[0].titles  # tu musi byc lista 1-elementowa
                    current_idd = idd

    return wikiPageTile_2_linesAndSources

def calculate_measures(precisions_list:list, ndcg_list:list, avg_prec_list:list):
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