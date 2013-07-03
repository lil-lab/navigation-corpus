import os, sys
sys.path.append('../../../../../tiny/pysrc')

from singlesentence import *


if __name__ == '__main__':
    sentences = SingleSentenceDataset.parse(open('corpus1-instructions.xgoal.noimplicit-partial.segmented.train.wlh.txt').read())
    folds = 4
    outs = []
    for n in range(folds):
        outs.append(open('corpus1-instructions.xgoal.noimplicit-partial.segmented.train.wlh.%d.ccg' % (n), 'w'))

    for n, sentence in zip(range(len(sentences)), sentences):
        outs[n % folds].write(sentence.to_file_string())
        outs[n % folds].write('\n\n')

    for out in outs:
        out.close()



