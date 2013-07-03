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
        if not i.stats().has_key('valid'):
            print >> sys.stderr, 'Valid flag not present: ', i.id()
            raise
        if i.stats()['valid']:
            print >> sys.stderr, 'processing: ', i.id()
            for text, label, trace in i.text():
                trace_str = repr((trace[0].x(), trace[0].y(), trace[0].direction()))
                if options.unique:
                    sentences.add((text, label, i.stats()['map'], trace_str))
                else:
                    sentences.append((text, label, i.stats()['map'], trace_str))

    for nl, lf, mapname, trace_str in sentences:
        print >> sys.stdout, nl
        print >> sys.stdout, lf
        print >> sys.stdout, mapname
        print >> sys.stdout, trace_str
        print >> sys.stdout

