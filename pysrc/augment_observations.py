import sys
from optparse import OptionParser
from navigationutils import *

def augment_observations(trace):
    # Get the map and positions form the ID, augment them into the trace 
    map_name = trace.instruction_id().split('_')[1].lower()
    if map_name[-1].isdigit(): map_name = map_name[:-1]
    start_pos = int(trace.instruction_id().split('_')[2])
    end_pos = int(trace.instruction_id().split('_')[3])
    trace.trace_stats()['map'] = map_name
    trace.trace_stats()['startPos'] = start_pos
    trace.trace_stats()['endPos'] = end_pos
    for step in trace.path():
        if int(step.direction()) in [0, 90, 180, 270]:
            try:
                r = robot_create(map_name, (int(step.x()), int(step.y()), int(step.direction())))
                step._observation = robot_state(r)[1]
            except:
                print >> sys.stderr, 'Skipping impossible step [%s] in %s' % (step, trace.instruction_id())

if __name__ == '__main__':
    parser = OptionParser(usage = '%prog <traces_file>')
    (options, args) = parser.parse_args()
    traces = read_follower(args[0])
    for trace in traces.values():
        augment_observations(trace)
        sys.stdout.write(trace.to_file_string())
        sys.stdout.write('\n')


