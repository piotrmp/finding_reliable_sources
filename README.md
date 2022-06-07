# Finding Reliable Sources

This repository contains the source code accompanying our study on the task of Finding Reliable Sources (FRS). The challenge of FRS is to, given a short textual claim (e.g. *Smoking tobacco is good for your helath.*), recommend a set of reliable sources (e.g. scholarly papers, publications from established institutions) that could support or refute the claim. The results of this study were described in the article *[Countering Disinformation by Finding Reliable Sources: a Citation-Based Approach](TODO)* presented at the IJCNN 2022 conference in Padoa. The datasets created for this work are published on Zenodo as [Wikipedia Complete Citation Corpus](https://doi.org/10.5281/zenodo.6539054) and [FRS Evaluation Datasets](https://doi.org/10.5281/zenodo.6539087).

## Code

The source code presented here allows to replicate the core results presented in our article. The following tasks are supported:

**Extracting a citation corpus from a Wikipedia database dump**

This is done through the code in the ```wiki_harverster``` package. The ```do_harvest.py``` script, when provided with a database dump (we used ```enwiki-20210201-pages-articles.xml```), will return a citation corpus. Instead of running the code, you can obtain the code from [Zenodo](https://doi.org/10.5281/zenodo.6539054).

**Converting a citation corpus to claim-source pairing dataset**

This task is performed by the ```distiller/do_distill.py``` script. It takes a citation corpus as an input and returns a CSP dataset. You will need to choose one of the available context generation techniques: ```sentence```, ```title+sentence``` or ```sentence+sentence```. See the article to understand what these variants correspond to and why the choice matters. This module also relies on the procedure extracting an identifier from a source description, included in ```source_explorer/normalise.py```. You can also download all three variants of the CSP dataset from [Zenodo](https://doi.org/10.5281/zenodo.6539087).

**Creating a search index using dense vector representations**

To index the reliable sources, we need to:
1. Compute the sentence embeddings for the contexts in the training data. This is performed by ```embedder/do_embed.py```. You can choose one of three embedding models: [Sentence-BERT](https://www.sbert.net), averaged [GloVe](https://nlp.stanford.edu/projects/glove/) or [Universal Sentence Encoder](https://tfhub.dev/google/universal-sentence-encoder/4).
2. Create a search index for finding the nearest neighbour in the embedding space, happening through ```dense_indexer/do_index.py```. This employs [NGT](https://github.com/yahoojapan/NGT), which you will need to install beforehand.

**Creating a search index using sparse vector represnetations**

This is an alternative to the previous approach, using bag-of-words representation ranked through Okapi BM25 function. The implementation in in ```sparse_indexer/do_index.py``` is indexing the source psudo-documents in [Elasticsearch](https://www.elastic.co/elasticsearch/) (you will need it installed before running the code). 

## Licence
