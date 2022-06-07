import sys
from os import listdir

pathPrefix = sys.argv[1]  # "data/learntocite/"
path = pathPrefix + 'sentences/2021'
MAX = 200000

bigdict = {}
counter = 0
for filename in sorted(listdir(path)):
    print("Reading " + filename)
    for line in open(path + '/' + filename):
        parts = line.split('\t')
        idd = int(parts[0])
        sources = parts[2:]
        for source1 in sources:
            source = source1.strip()
            if source == '':
                continue
            if source not in bigdict:
                bigdict[source] = {}
            if idd not in bigdict[source]:
                bigdict[source][idd] = 1
            else:
                bigdict[source][idd] = bigdict[source][idd] + 1
    counter = counter + 1
    if counter == MAX:
        break

output = open(pathPrefix + 'out/out.tsv', 'w')
skipped = 0
for key in bigdict:
    numDoc = len(bigdict[key])
    numOcc = sum([bigdict[key][x] for x in bigdict[key]])
    if numOcc == 1:
        skipped = skipped + 1
    output.write(key + '\t' + str(numDoc) + '\t' + str(numOcc) + '\n')
output.close()
print("Skipped singletons: " + str(skipped))
