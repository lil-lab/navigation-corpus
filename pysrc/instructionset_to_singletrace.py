import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../../tiny.git/tiny/pysrc')
from singletrace import *
import tinyutils

if __name__ == '__main__':
    dataset = instruction_sets_to_singletrace(read_instructions(sys.argv[1]))
    for st in dataset:
        st._nl = tinyutils.preprocess_text(st._nl)
    sys.stdout.write(dataset.to_file_string())

