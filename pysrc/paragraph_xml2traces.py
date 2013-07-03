from optparse import OptionParser
import sys
from navigationutils import *
from xml.sax import handler, make_parser, parseString

sys.path.append('../code')

class XMLHanlder(handler.ContentHandler):
    def __init__(self):
        self._start_place = None
        self._end_place = None
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
            self._map_name = attrs['map']
            start_x, start_y = eval(attrs['start'])
            end_x, end_y = eval(attrs['end'])
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
            path = []
            for x, y, direction in self._path:
                path.append(PathStep(x, y, direction, 'NA', -1))
            self._instructions_filename = self._instructions_filename.rsplit('.', 2)[0]
            self._traces.append(Trace(self._instructions_filename, trace_stats, path))
            self._instructions.append((self._instructions_filename, self._instruction_text))
            # Reset everything
            self._start_place = None
            self._end_place = None
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


if __name__ == '__main__':
    # Parse argument
    parser = OptionParser(usage = 'usage: %prog -o traces_output -u instructions_output xml_file')
    parser.add_option('-o', '--traces-output', dest = 'traces_output', help = 'Traces output')
    parser.add_option('-u', '--instructions-output', dest = 'instructions_output', help = 'Instructions output')
    (options, args) = parser.parse_args()

    h = XMLHanlder()
    p = make_parser(['xml.sax.expatreader'])
    p.setContentHandler(h)
    for line in sys.stdin:
        p.feed(line)

    traces = h._traces
    instructions = h._instructions

    out = open(options.traces_output, 'w')
    for trace in traces:
        out.write(trace.to_file_string())
        out.write('\n')
    out.close()

    out = open(options.instructions_output, 'w')
    for instruction in instructions:
        out.write(instruction[0])
        out.write('\n')
        out.write(instruction[1])
        out.write('\n\n')
    out.close()

    print >> sys.stderr, 'Wrote %d traces' % (len(traces))
    print >> sys.stderr, 'Write %d instructions' % (len(instructions))
