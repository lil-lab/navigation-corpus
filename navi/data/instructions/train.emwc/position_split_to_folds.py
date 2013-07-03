import os, sys
from collections import defaultdict
sys.path.append('../../../../../navi/pysrc')

from positionsinglesentence import *


if __name__ == '__main__':
    sentences = PositionSingleSentenceDataset.parse(open('corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.ccg').read())
    folds = 4
    outs = []
    for n in range(folds):
        outs.append(open('corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.%d.ccg' % (n), 'w'))

    # collect for each natural language sentence all data items
    uniques = defaultdict(list)
    for item in sentences:
        uniques[item.nl()].append(item)
    uniques = uniques.values()

    for n, unique_sentences in zip(range(len(uniques)), uniques):
        for sentence in unique_sentences:
            outs[n % folds].write(sentence.to_file_string())
            outs[n % folds].write('\n\n')

    for out in outs:
        out.close()



