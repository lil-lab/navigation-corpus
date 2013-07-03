from optparse import OptionParser
import sys
from navigationutils import *
from xml.sax import handler, make_parser, parseString
from infer_actions import augment_actions

sys.path.append('../code')

class XMLHanlder(handler.ContentHandler):
    def __init__(self):
        self._map_name = None
        self._instructions_filename = None
        self._path = None
        self._instruction_text = None
        self._id = None
        self._char_buffer = None
        self._traces = []
        self._instructions = []

    def startElement(self, name, attrs):
        if name == 'example':
            self._map_name = attrs['map'].lower()
            self._id = attrs['id']
        elif name == 'instruction':
            self._char_buffer = None
            self._instructions_filename = attrs['filename']
        elif name == 'path':
            self._char_buffer = None

    def endElement(self, name):
        if name == 'example':
            trace_stats = {}
            trace_stats['chenId'] = self._id
            trace_stats['map'] = self._map_name
            path = []
            for x, y, direction in self._path:
                path.append(PathStep(x, y, direction, 'NA', -1, None))
            self._instructions_filename = self._instructions_filename.rsplit('.', 2)[0]
            self._traces.append(Trace(self._instructions_filename, trace_stats, path))
            self._instructions.append((self._instructions_filename, self._instruction_text))
            # Reset everything
            self._map_name = None
            self._instructions_filename = None
            self._path = None
            self._instruction_text = None
            self._id = None
        elif name == 'instruction':
            self._instruction_text = self._char_buffer.strip()
        elif name == 'path':
            self._path = eval(self._char_buffer.strip())
        self._char_buffer = None

    def characters(self, content):
        if self._char_buffer is None:
            self._char_buffer = content.strip()
        else:
            self._char_buffer += content.strip()

def text_indicates_turn(text):
    return not re.search('(^|\s)(put|face|turn|place|orient|stand)($|\s)', text.lower()) is None and not text.lower().startswith('with') and not text.lower().startswith('move')

def process_trace(trace, text):
    augment_actions(trace)
    ## change turn actions to proper LEFT/RIGHT actions, starting at direction 0
    first = trace.path()[0]
    if first.act() == 'TURN' and first.direction() == -1:
        second = trace.path()[1]
        first._direction = 0
        if second.direction() == 0:
            if text_indicates_turn(text):
                ## need to add 4 LEFTs when there is a turn -- not clear how to solve this
                first._act = 'LEFT'
                trace.path().insert(1, PathStep(first.x(), first.y(), 90, 'LEFT', -1, None))
                trace.path().insert(1, PathStep(first.x(), first.y(), 180, 'LEFT', -1, None))
                trace.path().insert(1, PathStep(first.x(), first.y(), 270, 'LEFT', -1, None))
            else:
                del trace.path()[0]
        elif second.direction() == 90:
            first._act = 'RIGHT'
        elif second.direction() == 180:
            first._act = 'LEFT'
            trace.path().insert(1, PathStep(first.x(), first.y(), 270, 'LEFT', -1, None))
        elif second.direction() == 270:
            first._act = 'LEFT'
    return trace

def process(traces, instructions):
    current_chen_id = None
    current_file_name = None
    last_instruction_index = None
    map_name = None
    text = []
    complete_instructions = []
    for trace, inst in zip(traces, instructions):
        if inst[0] != current_file_name and not current_file_name is None:
            complete_instructions.append(Instruction(current_file_name, text, {'map' : map_name, 'x' : int(current_file_name.split('_')[3]), 'y' : int(current_file_name.split('_')[2])}))
            current_file_name = None
        if current_file_name is None:
            current_chen_id = int(trace.trace_stats()['chenId'].split('-', 2)[0])
            last_instruction_index = int(trace.trace_stats()['chenId'].split('-', 2)[1]) - 1
            map_name = str(trace.trace_stats()['map'])
            current_file_name = inst[0]
            text = []
        new_chen_id = int(trace.trace_stats()['chenId'].split('-', 2)[0])
        if new_chen_id != current_chen_id:
            raise Exception('%s: invalid id, expected %d, got %d' % (inst[0], current_chen_id, new_chen_id))
        if last_instruction_index >= int(trace.trace_stats()['chenId'].split('-', 2)[1]):
            raise Exception('%s: invalid index, previous was %d, got %d' % (inst[0], last_instruction_index, int(trace.trace_stats()['chenId'].split('-', 2)[1])))
        last_instruction_index = int(trace.trace_stats()['chenId'].split('-', 2)[1])
        if map_name != str(trace.trace_stats()['map']):
            raise Exception('%s: invalid map, expected %s, got %s' % (inst[0], map_name, str(trace.trace_stats()['map'])))
        if current_file_name != inst[0]:
            raise Exception('%s: invalid filename, expected %s, got %s' % (inst[0], current_file_name, inst[0]))
        text.append((inst[1], None, process_trace(trace, inst[1]).path()))
    return complete_instructions

if __name__ == '__main__':
    # Parse argument
    parser = OptionParser(usage = 'usage: %prog < xml_file')
    (options, args) = parser.parse_args()

    h = XMLHanlder()
    p = make_parser(['xml.sax.expatreader'])
    p.setContentHandler(h)
    for line in sys.stdin:
        p.feed(line)

    traces = h._traces
    instructions = h._instructions

    for inst in process(traces, instructions):
        sys.stdout.write(inst.to_file_string())
        sys.stdout.write('\n\n')

    print >> sys.stderr, 'Wrote %d traces' % (len(traces))
    print >> sys.stderr, 'Write %d instructions' % (len(instructions))
