import os, sys
sys.path.append('../../../../pysrc')

from utils import *


if __name__ == '__main__':
    insts = read_instructions('corpus1-instructions.xgoal.noimplicit.segmented.train.sample20.txt')
    for i, n in zip(insts.values(), range(1, len(insts) + 1)):
        out = open('corpus1-instructions.xgoal.noimplicit.segmented.train.sample20-%d.txt' % (n), 'w')
        out.write(i.to_file_string())
        out.write('\n\n')
        out.close()



