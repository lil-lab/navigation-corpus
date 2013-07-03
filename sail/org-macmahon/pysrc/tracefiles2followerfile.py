from optparse import OptionParser
import os, sys
sys.path.append('../../pysrc')
from utils import *

if __name__ == '__main__':
    # Parse command line arguments
    parser = OptionParser(usage = 'usage: %prog files')
    (options, args) = parser.parse_args()

    files = dict(map(lambda x: (os.path.basename(x), x), args))
    available_traces = set(map(lambda x: x.split('-')[1].rsplit('.', 2)[0], args))
    traces = []
    for instruction_id in available_traces:
        try:
            trace_stats = {}
            trace_stats['directionRating'] = int(open(files['DirRtng-%s.txt' % (instruction_id)]).read().strip())
            trace_stats['efficiency'] = float(open(files['Efficiency-%s.txt' % (instruction_id)]).read().strip())
            trace_stats['confidence'] = int(open(files['NavConf-%s.txt' % (instruction_id)]).read().strip())
            trace_stats['targetFound'] = True if int(open(files['TgtFound-%s.txt' % (instruction_id)]).read().strip()) == 1 else False
            path = []
            for pos, act, time in zip(open(files['MotTrace-%s.txt' % (instruction_id)]).readlines(), open(files['ActTrace-%s.txt' % (instruction_id)]).readlines(), open(files['TimeTrace-%s.txt' % (instruction_id)]).readlines()):
                time = float(time.strip())
                act = act.strip()
                x, y, direction = map(int, pos.strip().split(','))
                path.append(PathStep(x, y, direction, act, time))
                if act == 'IncrTgt' or act == 'CorrTgt':
                    break
            traces.append(Trace(instruction_id, trace_stats, path))
        except KeyError as e:
            print >> sys.stderr, 'Skipping %s due to: %s' % (instruction_id, e)

    for trace in traces:
        print >> sys.stdout, trace.to_file_string()

    print >> sys.stderr, 'Processed %d traces' % (len(traces))
