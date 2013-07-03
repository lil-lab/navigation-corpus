import os, sys
sys.path.append('../../../../pysrc')

from utils import *


if __name__ == '__main__':
    sample20 = read_instructions('../train.sample20/corpus1-instructions.xgoal.noimplicit.segmented.train.sample20.txt')
    sample10train = read_instructions('corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-train.txt')
    sample10eval = read_instructions('corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-eval.txt')
    sample10train = dict(map(lambda x: (x[0], sample20[x[0]]), sample10train.items()))
    sample10eval = dict(map(lambda x: (x[0], sample20[x[0]]), sample10eval.items()))
    out = open('corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-train.txt', 'w')
    for i in sample10train.values():
        out.write(i.to_file_string())
        out.write('\n\n')
    out.close()
    out = open('corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-eval.txt', 'w')
    for i in sample10eval.values():
        out.write(i.to_file_string())
        out.write('\n\n')
    out.close()



