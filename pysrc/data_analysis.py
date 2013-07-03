from navigationutils import *
from optparse import OptionParser
import os
from numpy import mean, std
from collections import defaultdict
from operator import itemgetter

'''
    Script to analyze data. 
    Loads all the data and allows easy access to it.
'''

def get_traces(instruction_id, traces_dict):
    filtered_traces = {}
    for filename, traces in traces_dict.items():
        for trace_instruction_id, trace in traces.items():
            if trace_instruction_id == instruction_id:
                filtered_traces[filename] = trace
    return filtered_traces

def collect_instruction_stats(instructions, traces):
    # get all traces for specific instruction
    for instruction in instructions.values():
        inst_traces = get_traces(instruction.id(), traces)
        num_followers = len(inst_traces)
        meanstd = lambda x: (0.0, 0.0) if len(x) == 0 else (mean(x), std(x))
        efficinecy = meanstd(map(lambda x: float(x.trace_stats()['efficiency']), inst_traces.values()))
        confidence = meanstd(map(lambda x: float(x.trace_stats()['confidence']), inst_traces.values()))
        direction = meanstd(map(lambda x: float(x.trace_stats()['directionRating']), inst_traces.values()))
        success = meanstd(map(lambda x: float(1.0 if x.trace_stats()['targetFound'] == 'True' else 0.0), inst_traces.values()))
        instruction.stats()['numFollowers'] = num_followers
        instruction.stats()['efficiency'] = efficinecy
        instruction.stats()['confidence'] = confidence
        instruction.stats()['targetFound'] = success
        instruction.stats()['directionRating'] = direction


def aggregate_trace_stats(traces, stat_name):
    instruction_id_to_value = {}
    histo = defaultdict(int)
    for t in traces:
        if t.trace_stats().has_key(stat_name):
            histo[t.trace_stats()[stat_name]] += 1
            instruction_id_to_value[t.instruction_id()] = t.trace_stats()[stat_name]
        else:
            instruction_id_to_value[t.instruction_id()] = None
    for value, freq in histo.items():
        print '%s\t::\t%d' % (value, freq)
    print 'Most frequent value: %s' % (max(histo.items(), key = itemgetter(1))[0])

if __name__ == '__main__':
    # Parser command line arguments
    parser = OptionParser(usage = 'usage: %prog -i INSTRUCTIONS [-p IGNORED_PREFIX] TRACES_FILE1 TRACES_FILE2 ....')
    parser.add_option('-i', '--instructions', dest = 'instructions', help = 'Instructions')
    parser.add_option('-p', '--ignored-prefix', dest = 'ignored_prefix', default = '', help = 'Instruction ID prefix to ignore (default: Cleaned-)')
    (options, args) = parser.parse_args()

    # Read instructions
    instructions = read_instructions(options.instructions)

    # Read traces
    traces = {}
    for trace_file in args:
        file_traces = {}
        for instruction_id, trace in read_follower(trace_file).items():
            if instruction_id.startswith(options.ignored_prefix):
                instructions_id = instruction_id[len(options.ignored_prefix):]
                trace._instruction_id = instruction_id
            file_traces[instruction_id] = trace
        traces[os.path.basename(trace_file).rsplit('.', 2)[0]] = file_traces
