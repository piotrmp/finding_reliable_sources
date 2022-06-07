import sys
import time
from os import listdir

import numpy as np

from embedder.encoder import Encoder

prefix = sys.argv[1]
onGPU = False
sentencePath = prefix + '/sentences/2021s'
embeddingsPath = prefix + '/out'
metaPath = prefix + '/corpus/2021/meta.tsv'
SEGMENT_SIZE = 1000
# encoder = Encoder('paraphrase-distilroberta-base-v1', onGPU)
# encoder = Encoder('average_word_embeddings_glove.6B.300d', onGPU)
encoder = Encoder('universal-sentence-encoder-v4', onGPU)
section = -1
if len(sys.argv) > 2:
    section = int(sys.argv[2])

if __name__ == '__main__':
    if onGPU:
        import torch
        
        print(torch.cuda.current_device())
        print(torch.cuda.device(0))
        print(torch.cuda.device_count())
        print(torch.cuda.get_device_name(0))
        print(torch.cuda.is_available())
    
    titles = {}
    for line in open(metaPath):
        parts = line.split('\t')
        idd = int(parts[0])
        title = parts[1]
        titles[idd] = title
    
    start_time = time.time()
    for filename in sorted(listdir(sentencePath), key=lambda x: int(x.rstrip('.tsv').lstrip('batch'))):
        if not filename.endswith('.tsv'):
            continue
        if section != -1:
            if not (filename.endswith(str(section) + '.tsv') or filename.endswith(str(section + 5) + '.tsv')):
                continue
        print("Reading " + filename)
        sentences = []
        embeddings = []
        for line in open(sentencePath + '/' + filename):
            parts = line.split('\t')
            idd = int(parts[0])
            title = titles[idd]
            sentence = parts[1].strip()
            sentences.append(sentence)
            if len(sentences) == SEGMENT_SIZE:
                embeddings.append(encoder.encode(sentences))
                sentences = []
        if len(sentences) != 0:
            embeddings.append(encoder.encode(sentences))
        matrix = np.concatenate(embeddings, axis=0)
        print('Final matrix of shape ' + str(matrix.shape))
        np.save(embeddingsPath + '/' + filename[:-len('.tsv')] + '.npy', matrix)
    print("--- %s seconds ---" % (time.time() - start_time))
