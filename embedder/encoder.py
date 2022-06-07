import tensorflow_hub as hub
from sentence_transformers import SentenceTransformer


class Encoder():
    def __init__(self, modelName, onGPU=False):
        if modelName in ['distilbert-base-nli-mean-tokens', 'paraphrase-distilroberta-base-v1'] or modelName[0] == '/':
            self.encSentenceBERT = SentenceTransformer(modelName)
            self.dim = 768
        elif modelName == 'average_word_embeddings_glove.6B.300d':
            self.encSentenceBERT = SentenceTransformer(modelName)
            self.dim = 300
        elif modelName == 'universal-sentence-encoder-v4':
            self.encUSE = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
            self.dim = 512
        self.onGPU = onGPU
        if self.onGPU and (self.encSentenceBERT is not None):
            self.pool = self.encSentenceBERT.start_multi_process_pool()
    
    def encode(self, sentences):
        if hasattr(self, 'encSentenceBERT'):
            if self.onGPU:
                result = self.encSentenceBERT.encode_multi_process(sentences, self.pool)
            else:
                result = self.encSentenceBERT.encode(sentences)
        elif hasattr(self, 'encUSE'):
            result = self.encUSE(sentences).numpy()
        return result
    
    def getDim(self):
        return self.dim
