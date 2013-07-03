from navigationutils import *
from optparse import OptionParser
import sys

'''
    Infer actions (Forward, Left, Right, ReDirct) from traces.
    Output traces augmented with actions.
'''


def augment_actions(trace):
    path = trace.path()
    for i in range(1, len(path)):
        prev = path[i - 1]
        current = path[i]
        changes = 0
        changes += 1 if prev.x() != current.x() else 0
        changes += 1 if prev.y() != current.y() else 0
        changes += 1 if prev.direction() != current.direction() else 0
        if changes > 1:
            raise Exception('Too many changes in %s step %d' % (trace.instruction_id(), i))
        if prev.x() != current.x() or prev.y() != current.y():
            prev._act = 'FORWARD'
        elif int(prev.direction()) != int(current.direction()):
            if int(prev.direction()) == -1:
                prev._act = 'TURN'
            elif int(prev.direction()) == 0:
                prev._act = 'LEFT' if int(current.direction()) == 270 else 'RIGHT'
            elif int(current.direction()) == 0:
                prev._act = 'LEFT' if int(prev.direction()) == 90 else 'RIGHT'
            elif int(prev.direction()) > int(current.direction()):
                prev._act = 'LEFT'
            else:
                prev._act = 'RIGHT'
        else:
            prev._act = 'REDIRCT'
    # The last step is assigned an End action
    path[-1]._act = 'NULL'

if __name__ == '__main__':
    parser = OptionParser(usage = '%prog <traces_file>')
    (options, args) = parser.parse_args()
    traces = read_follower(args[0])
    for trace in traces.values():
        augment_actions(trace)
        sys.stdout.write(trace.to_file_string())
        sys.stdout.write('\n')
