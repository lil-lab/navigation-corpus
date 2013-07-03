from navigationutils import *
from optparse import OptionParser
import sys, os
from operator import itemgetter


'''
    Given instruction files and traces, generate .trace files, 
    which couple instructions and traces.
'''

def trace_filename(instruction_id, follower_name, output_dir):
    '''
        Generate the name of the .trace output file
    '''
    return output_dir + '/' + follower_name + '_' + instruction_id + '.trace'

def convert_action(action):
    '''
        Convert action to the .trace action
    '''
    if action.upper() in ['END', 'CORRTGT', 'INCRTGT']:
        return 'GOAL'
    else:
        return action.upper()

def convert_step_to_string(step):
    '''
        Convert a step object to a string
    '''
    return convert_action(step.act()) + '[' + '(' + str(step.x()) + ', ' + str(step.y()) + ', ' + str(step.direction()) + ')' + ']'


def turn_left(dir):
    dir = int(dir)
    if dir == 0:
        return 270
    else:
        return dir - 90

def turn_right(dir):
    dir = int(dir)
    if dir == 270:
        return 0
    else:
        return dir + 90


def write_trace_file(instructions, trace, follower_name, filename):
    '''
        Write the content of the .trace file
    '''
    print >> sys.stderr, 'Writing %s' % (filename)
    out = open(filename, 'w')

    # Collect the attributes
    attributes = {}
    attributes['instructions_id'] = instructions.id()
    attributes['follower'] = follower_name
    for key, value in instructions.stats().items():
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], float) and isinstance(value[1], float):
            # Case of a mean and std pair
            attributes['i_' + str(key) + '_mean'] = str(value[0])
            attributes['i_' + str(key) + '_std'] = str(value[1])
        else:
            attributes['i_' + str(key)] = str(value)
    for key, value in trace.trace_stats().items():
        attributes['t_' + str(key) if key != 'map' else str(key)] = str(value)
    for key, value in attributes.items():
        out.write('%s=%s\n' % (key, value))
    out.write('\n')

    # Write instructions
    for sentence in map(itemgetter(0), instructions.text()):
        for single in sentence.split('.'):
            s = single.strip()
            if s != '':
                out.write(s)
                out.write('\n')
    out.write('\n')

    # Write trace steps
    first = True
    for step in trace.path():
        if step.act() != 'ReDirct':
            if first and int(step.direction()) == -1:
                # Case the direction undefined, if possible, define it to the inverse of the direction of the second step and write two steps to compensate for the turn
                if len(trace.path()) > 1:
                    second_dir = trace.path()[1].direction()
                    second_act = trace.path()[1].act()
                    if second_act == 'Right':
                        step._act = 'Left'
                        step._direction = turn_right(turn_right(second_dir))
                        out.write(convert_step_to_string(step))
                        out.write('\n')
                        step._direction = turn_right(second_dir)
                        out.write(convert_step_to_string(step))
                    else:
                        step._act = 'Right'
                        step._direction = turn_left(turn_left(second_dir))
                        out.write(convert_step_to_string(step))
                        out.write('\n')
                        step._direction = turn_left(second_dir)
                        out.write(convert_step_to_string(step))
                else:
                    step._direction = 0
                    out.write(convert_step_to_string(step))
            else:
                out.write(convert_step_to_string(step))
            out.write('\n')
            first = False
    out.write('\n')

    out.close()


if __name__ == '__main__':
    parser = OptionParser(usage = '%prog -i instructions_file -o output_dir trace_files')
    parser.add_option('-i', '--instructions', dest = 'instructions_file', help = 'Instructions file')
    parser.add_option('-o', '--output-dir', dest = 'output_dir', help = 'Output directory')
    (options, args) = parser.parse_args()

    # If IDs start with the prefix 'Cleaned-', remove it
    instructions = dict(map(lambda x: (x[0].split('-', 1)[1], x[1]) if x[0].startswith('Cleaned-') else x, read_instructions(options.instructions_file).items()))
    for i in instructions.values():
        if i.id().startswith('Cleaned-'):
            i._id = i.id().split('-', 1)[1]

    for trace_file in args:
        traces = read_follower(trace_file)
        for instruction_id, trace in traces.items():
            if instructions.has_key(instruction_id):
                i = instructions[instruction_id]
                follower_name = os.path.basename(trace_file).rsplit('.', 1)[0]
                write_trace_file(i, trace, follower_name, trace_filename(instruction_id, follower_name, options.output_dir))


