import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../../tiny.git/tiny/pysrc')
from singletrace import *
import tinyutils
import random
from optparse import OptionParser

def cut_x_suffix(trace):
    new_trace = []
    for step in trace:
        if step.act() == 'X':
            new_trace.append(PathStep(step.x(), step.y(), step.direction(), 'NULL', step.time(), step.observation(), step.implicit()))
            return new_trace
        else:
            new_trace.append(step)
    return new_trace

if __name__ == '__main__':
    parser = OptionParser(usage = 'usage: %prog [-f NUM_FOLDS] ')
    parser.add_option('-f', '--folds', dest = 'num_folds', default = 1, help = 'Number of folds')
    parser.add_option('-i', '--include-implicit', dest = 'include_implicits', action = 'store_true', default = False, help = 'Include implicit instruction sets')
    parser.add_option('-s', '--ignored-ids', dest = 'ignored_ids', default = None, help = 'Instruction IDs to ignore')
    parser.add_option('-a', '--all', dest = 'all', action = 'store_true', default = False, help = 'Include all instructions, except ignored IDs, if specified.')
    parser.add_option('-v', '--verify', dest = 'verify', action = 'store_true', default = False, help = 'Verify consistency of some flags')
    (options, args) = parser.parse_args()

    dataset = read_instructions(args[0]).values()
    num_folds = int(options.num_folds)
    if not options.all:
        dataset = filter(lambda inst: inst.stats().has_key('annotated') and inst.stats()['annotated'] and inst.stats()['valid'] and (options.include_implicits or not inst.stats()['implicit']), dataset)
    random.shuffle(dataset)

    ## Remove ignored IDs
    if not options.ignored_ids is None:
        ignored_ids = set(map(lambda x: x.strip(), open(options.ignored_ids).readlines()))
        dataset = filter(lambda inst: not inst.id() in ignored_ids, dataset)

    ## Verify implicit flag is correct -- each set that has the flag contains, should have at least a single implicit step
    if options.verify:
        for inst in dataset:
            found_implicit = False
            for sentence, label, trace in inst.text():
                if trace:
                    for step in trace:
                        if step.implicit() == True: found_implicit = True
            if found_implicit != inst.stats()['implicit']:
                print >> sys.stderr, '%s implicit flag is inconsistent' % (inst.id())


    for fold in range(num_folds):
        out = open('fold%d.settrc' % (fold), 'w')
        out_labeled = open('fold%d.ccgsettrc' % (fold), 'w')
        for inst in dataset[fold::num_folds]:
            inst._text = [(tinyutils.preprocess_text(t[0]), t[1], t[2]) for t in inst._text]
            ## Temporarily cut X suffix
            inst._text = [(t[0], t[1], cut_x_suffix(t[2])) for t in inst._text]

            out.write(inst.to_java_file_string())
            out.write('\n\n')

            ## Temporarily add dummy LFs
            inst._text = [(t[0], 'you:ps' if t[1] is None else t[1], t[2]) for t in inst._text]

            out_labeled.write(inst.to_java_file_string())
            out_labeled.write('\n\n')

        out.close()
        out_labeled.close()


