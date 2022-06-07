import random
import sys

path = sys.argv[1]

trainOut = open(path + 'metaTrain.tsv', 'w')
testOut = open(path + 'metaTest.tsv', 'w')

random.seed(1)

for line in open(path + 'meta.tsv'):
    if random.random() < 0.2:
        testOut.write(line)
    else:
        trainOut.write(line)

trainOut.close()
testOut.close()
