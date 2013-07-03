from navigationutils import *
from optparse import OptionParser
import sys

'''
    Convert a labeled set of instructions to a SingleSentence dataset file.
'''

if __name__ == '__main__':
    # Parser command line arguments
    parser = OptionParser(usage = 'usage: %prog [-u] labeled_file')
    parser.add_option('-u', '--unique', action = 'store_true', dest = 'unique', help = 'Create dataset with unique samples')
    (options, args) = parser.parse_args()


    instructions = read_instructions(args[0])

    sentences = None
    if options.unique:
        sentences = set()
    else:
        sentences = []

    for i in instructions.values():
        for text, label, trace in i.text():
            if not label is None:
                if options.unique:
                    sentences.add((text, label))
                else:
                    sentences.append((text, label))

    for nl, lf in sentences:
        print >> sys.stdout, nl
        print >> sys.stdout, lf
        print >> sys.stdout

