import sys, re, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../tiny/pysrc')
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../navigation/pysrc')
from navigationutils import *

'''
    Data structure equivalent to the SingleTrace and SingleTraceDataset in the Java code
'''

class SingleTrace:
    def __init__(self, nl, stats, steplist):
        self._nl = nl
        self._stats = stats
        self._steplist = steplist
    def nl(self): return self._nl
    def stats(self): return self._stats
    def steplist(self): return self._steplist
    def __str__(self): return self.to_file_string()
    def to_file_string(self):
        return self.nl() + '\n' + dict_to_line(self.stats()) + '\n' + ';'.join([str((x.x(), x.y(), x.direction())) if x.act() == 'NULL' else str(x) for x in self.steplist()])
    @staticmethod
    def parse(text):
        s = text.split('\n')
        nl = s[0]
        stats = line_to_dict(s[1])
        steplist = [PathStep.step_parse_no_observations('NULL' + x) if x.startswith('(') else PathStep.step_parse_no_observations(x) for x in s[2].split(';')]
        return SingleTrace(nl, stats, steplist)

class SingleTraceDataset(list):
    def __init__(self, sentences):
        super(SingleTraceDataset, self).__init__(sentences)
    def to_file_string(self):
        ret = ''
        for sentence in self:
            ret += sentence.to_file_string()
            ret += '\n\n'
        return ret
    @staticmethod
    def parse(text):
        chunks = filter(lambda x: x != '', text.split('\n\n'))
        sentences = []
        for chunk in chunks:
            sentence = SingleTrace.parse(chunk)
            sentences.append(sentence)
        return SingleTraceDataset(sentences)

def instruction_set_to_singletrace(inst):
    singletraces = []
    stats = inst.stats()
    for nl, lf, trace in inst.text():
        if len(trace) != 0:
            singletraces.append(SingleTrace(nl, stats, trace))
    return singletraces

def instruction_sets_to_singletrace(insts):
    singletraces = []
    for inst in insts.values():
        for st in instruction_set_to_singletrace(inst):
            singletraces.append(st)
    return SingleTraceDataset(singletraces)


