import sys, re

'''
    Utilities and general classes for the navigation-sail corpus.
'''

Left = 'Left'
At = 'At'
Right = 'Right'
FrontLeft = 'FrontLeft'
FrontRight = 'FrontRight'
Front = 'Front'

horizon_key = [Left, At, Right, FrontLeft, Front, FrontRight]

def horizon_to_string(horizon, elegant):
    if elegant:
        return  '\t\t'.join(map(lambda x: '%s%s' % (x[1], x[0]), zip(horizon, horizon_key)[3:])) + '\n' + '\t' + '\t'.join(map(lambda x: '%s%s' % (x[1], x[0]), zip(horizon, horizon_key)[:3]))
    else:
        return '\t'.join(map(lambda x: '%s%s' % (x[1], repr(x[0])), zip(horizon, horizon_key)))

def dict_to_line(d):
    return '\t'.join([(str(key) + '=' + str(value)) for key, value in  d.items()]).replace(' ', '')

def line_to_dict(line):
    return dict([(entry.split('=', 1)[0], entry.split('=', 1)[1]) for entry in line.split('\t')])

class Instruction:
    def __init__(self, id, text, stats):
        self._id = id
        self._text = text
        self._stats = stats
    def id(self): return self._id
    def text(self): return self._text
    def stats(self): return self._stats
    def __str__(self):
        return self.to_file_string()
    def to_java_file_string(self):
        ret = self.id()
        ret += '\n'
        ret += dict_to_line(self.stats())
        for sentence, label, trace in self.text():
            ret += '\n'
            ret += sentence
            if not label is None:
                ret += '\n'
                ret += label
            ret += '\n'
            ret += ';'.join([str((x.x(), x.y(), x.direction())) if x.act() == 'NULL' else str(x) for x in trace])
        return ret
    def to_file_string(self):
        ret = self.id()
        ret += '\n'
        ret += repr(self.stats())
        for sentence, label, trace in self.text():
            ret += '\n'
            ret += sentence
            if not label is None:
                ret += '\n'
                ret += '## '
                ret += label
            for step in trace:
                ret += '\n'
                ret += '%% '
                ret += str(step)
        return ret
    @staticmethod
    def parse(text):
        lines = filter(lambda x: not x.startswith('//'), text.split('\n'))
        id = lines[0]
        stats = eval(lines[1])
        lines = lines[2:]
        i = 0
        text = []
        while i < len(lines):
            sentence = lines[i]
            i += 1
            if len(lines) > i and lines[i].startswith('##'):
                label = lines[i].strip('# ')
                i += 1
            else:
                label = None
            trace = []
            while len(lines) > i and lines[i].startswith('%%'):
                step = PathStep.step_parse_no_observations(lines[i].strip('% '))
                trace.append(step)
                i += 1
            text.append((sentence, label, trace))
        return Instruction(id, text, stats)

class PathStep:
    def __init__(self, x, y, direction, act, time, observation, implicit = False):
        self._x = x
        self._y = y
        self._direction = direction
        self._act = act
        self._time = time
        self._observation = observation
        self._implicit = implicit
    def x(self): return self._x
    def y(self): return self._y
    def direction(self): return self._direction
    def act(self): return self._act
    def time(self): return self._time
    def implicit(self): return self._implicit
    def observation(self): return self._observation
    @staticmethod
    def step_parse_no_observations(s):
        step_re = re.match('(?P<act>[A-Z]+)(|(?P<imp>\[I\]))\((?P<x>\d+),\s*(?P<y>\d+),\s*(?P<dir>\d+)\)', s)
        if step_re is None:
            raise Exception(s)
        step_dict = step_re.groupdict()
        return PathStep(int(step_dict['x']), int(step_dict['y']), int(step_dict['dir']), step_dict['act'], None, None, not step_dict['imp'] is None)
    def __str__(self, elegant = True, no_observation = True):
        ret = '%s%s(%s,%s,%s)' % (self.act(), '[I]' if self.implicit() else '', str(self.x()), str(self.y()), str(self.direction()))
        if not no_observation and self.observation():
            for horizon_str in map(lambda x: horizon_to_string(x, elegant), reversed(self.observation()) if elegant else self.observation()):
                ret += '\n\t'
                ret += '\n\t'.join(horizon_str.split('\n'))
        return ret
    def __repr__(self):
        return str(self)

class Trace:
    def __init__(self, instruction_id, trace_stats, path):
        self._instruction_id = instruction_id
        self._trace_stats = trace_stats
        self._path = path
    def instruction_id(self):
        return self._instruction_id
    def path(self):
        return self._path
    def trace_stats(self):
        return self._trace_stats
    def to_file_string(self):
        ret = self.instruction_id()
        ret += '\n'
        ret += '\t'.join(map(lambda x: '%s=%s' % (x[0], str(x[1])), self.trace_stats().items()))
        ret += '\n'
        for step in self.path():
            ret += '%s,%s,%s;%s;%s;%s\n' % (step.x(), step.y(), step.direction(), step.act(), str(step.time()), repr(step.observation()))
        return ret
    def __str__(self, elegant = True):
        ret = '### Instruction: ' + self.instruction_id() + '\n'
        ret += '### ' + str(self.trace_stats()) + '\n'
        ret += '\n'.join(map(lambda x: x.__str__(elegant), self.path()))
        return ret
    @staticmethod
    def parse(text):
        lines = filter(lambda x: not x.startswith('//'), text.split('\n'))
        instruction_id = lines[0]
        trace_stats = dict(map(lambda x: x.split('=', 2), lines[1].split('\t')))
        path = []
        for line in lines[2:]:
            s = line.split(';')
            x, y, direction = s[0].split(',')
            act = s[1]
            time = float(s[2])
            if len(s) > 3:
                observation = eval(s[3])
            else:
                observation = []
            path.append(PathStep(x, y, direction, act, time, observation))
        return Trace(instruction_id, trace_stats, path)


def read_instructions(file):
    chunks = filter(lambda x: x != '', open(file).read().split('\n\n'))
    insts = {}
    for chunk in chunks:
        try:
            inst = Instruction.parse(chunk)
            insts[inst.id()] = inst
        except Exception as e:
            print >> sys.stderr, chunk
            raise e
    return insts

def read_follower(file):
    chunks = filter(lambda x: x != '', open(file).read().split('\n\n'))
    traces = {}
    for chunk in chunks:
        trace = Trace.parse(chunk)
        traces[trace.instruction_id()] = trace
    return traces

def get_tokenizer():
    import nltk
    return nltk.tokenizer.RegexpTokenizer(r'\w+|[^\w\s]+')

