from user import *
import re, os, cmd , readline
from optparse import OptionParser
from collections import defaultdict
from navigationutils import *

position_pattern = '\(([0-9]+),\s*([0-9]+),\s*(0|90|180|270)\)'
maps = defaultdict(dict)
maps_numbered_positions = defaultdict(dict)

class CMD(cmd.Cmd):
    def __init__(self, instructions, output_file):
        cmd.Cmd.__init__(self)
        self._instructions = list(instructions)
        self._current_instruction_set_index = -1
        self._current_instruction_set = None
        self._currrent_instruction_index = -1;
        self._last_position = None
        self._output_file = output_file
        self._current_instruction_index = 0
        self.__next__()

    def __update_current_position__(self, position):
        self._last_position = position
        cmd.Cmd.prompt = '(%2d, %2d, %3dD) > ' % (position[0], position[1], position[2])

    def __load_next_instruction_set__(self):
        if self._current_instruction_set is None:
            self._current_instruction_set_index = 0
        else:
            self._current_instruction_set.stats()['annotated'] = True
            self.__save__()
            self._current_instruction_set_index += 1

        while self._current_instruction_set_index < len(self._instructions) and self._instructions[self._current_instruction_set_index].stats().has_key('annotated') and self._instructions[self._current_instruction_set_index].stats()['annotated']:
             self._current_instruction_set_index += 1
        print colored('%d left' % (len(self._instructions) - self._current_instruction_set_index), 'yellow')

        if self._current_instruction_set_index >= len(self._instructions):
            print colored('All annotated', 'yellow')
            self.do_EOF('')
            return

        self._current_instruction_set = self._instructions[self._current_instruction_set_index]
        self._current_instruction_index = 0
        ## Parse the map name from the id and add it to the stats() map
        id = self._current_instruction_set.id()
        id_split = id.split('_')
        map_name = id_split[1][:-1].lower()
        end_position_num = int(id_split[3])
        init_position_num = int(id_split[2])
        init_position = maps_numbered_positions[map_name][init_position_num]
        self._current_instruction_set.stats()['map'] = map_name
        self._current_instruction_set.stats()['y'] = init_position_num
        self._current_instruction_set.stats()['x'] = end_position_num
        self.__update_current_position__(init_position)
        self.__print_instruction_set__()
        print 'Currently annotating:'
        self.__print_instruction__()

    def __load_next_instruction__(self):
        if not self._current_instruction_set is None and len(self._current_instruction_set.text()) - 1 > self._current_instruction_index:
            self._current_instruction_index += 1
            return True
        else:
            return False

    def __save__(self):
        out = open(self._output_file, 'w')
        for inst in self._instructions:
            out.write(inst.to_file_string())
            out.write('\n\n')
        out.close()
        print colored('Data saved', 'yellow')

    def __print_instruction_set__(self):
        print colored(self._current_instruction_set, 'cyan')

    def __print_instruction__(self):
        print colored('[%d/%d]' % (self._current_instruction_index + 1, len(self._current_instruction_set.text())), 'green', attrs = ['reverse']),
        for line in self._current_instruction_set.text()[self._current_instruction_index]:
            print colored('\t' + ('null' if line is None else str(line)), 'green')

    def __next__(self):
        if self.__load_next_instruction__():
            print 'Currently annotating:'
            self.__print_instruction__()
        else:
            self.__load_next_instruction_set__()

    def do_EOF(self, line):
        print
        self.__save__()
        return True

    def do_v(self, line):
        return self.do_set('valid=T')

    def do_notv(self, line):
        return self.do_set('valid=F')

    def do_c(self, line):
        return self.do_set('correct=T')

    def do_notc(self, line):
        return self.do_set('correct=F')

    def do_imp(self, line):
        return self.do_set('implicit=T')

    def do_notimp(self, line):
        return self.do_set('implicit=F')

    def do_save(self, line):
        self.__save__()

    def do_skip(self, line):
        self.__next__()

    def do_skipset(self, line):
        self.__load_next_instruction_set__()

    def do_l(self, line):
        ''' Left '''
        global maps
        step = PathStep(self._last_position[0], self._last_position[1], self._last_position[2], 'LEFT', -1, None, line == 'i')
        self._current_instruction_set.text()[self._current_instruction_index][2].append(step)
        self.__update_current_position__(maps[self._current_instruction_set.stats()['map']][self._last_position]['l'])
        print colored('%s -> %s' % (step, self._last_position))

    def do_li(self, line):
        self.do_l('i')

    def do_fi(self, line):
        self.do_f('i')

    def do_clear(self, line):
        for text, lf, trace in self._current_instruction_set.text():
            while len(trace) != 0:
                trace.pop()
        self._current_instruction_index = 0
        init_position = maps_numbered_positions[self._current_instruction_set.stats()['map']][self._current_instruction_set.stats()['start']]
        self.__update_current_position__(init_position)
        self.__print_instruction_set__()
        print 'Currently annotating:'
        self.__print_instruction__()

    def do_ri(self, line):
        self.do_r('i')

    def do_r(self, line):
        ''' Right '''
        global maps
        step = PathStep(self._last_position[0], self._last_position[1], self._last_position[2], 'RIGHT', -1, None, line == 'i')
        self._current_instruction_set.text()[self._current_instruction_index][2].append(step)
        self.__update_current_position__(maps[self._current_instruction_set.stats()['map']][self._last_position]['r'])
        print colored('%s -> %s' % (step, self._last_position))

    def do_f(self, line):
        ''' Forward '''
        global maps
        if maps[self._current_instruction_set.stats()['map']][self._last_position].has_key('f'):
            step = PathStep(self._last_position[0], self._last_position[1], self._last_position[2], 'FORWARD', -1, None, line == 'i')
            self._current_instruction_set.text()[self._current_instruction_index][2].append(step)
            self.__update_current_position__(maps[self._current_instruction_set.stats()['map']][self._last_position]['f'])
            print colored('%s -> %s' % (step, self._last_position))
        else:
            print colored('Invalid step', 'red')

    def do_print(self, line):
        self.__print_instruction_set__()

    def do_printi(self, line):
        self.__print_instruction__()

    def do_set(self, line):
        ''' Set a property '''
        line_split = line.split('=', 1)
        value = True if line_split[1] == 'T' else (False if line_split[1] == 'F' else eval(line_split[1]))
        self._current_instruction_set.stats()[line_split[0]] = value
        print colored('Set: %s=%s' % (line_split[0], value), 'yellow', 'on_cyan')

    def do_n(self, line):
        ''' NULL step, also moving to the next instruction '''
        global maps
        step = PathStep(self._last_position[0], self._last_position[1], self._last_position[2], 'NULL', -1, None, line == 'i')
        self._current_instruction_set.text()[self._current_instruction_index][2].append(step)
        self.__print_instruction__()
        self.__next__()

    def do_x(self, line):
        ''' Temporary placeholder for X steps (should be replaced with null steps later on) '''
        global maps
        step = PathStep(self._last_position[0], self._last_position[1], self._last_position[2], 'X', -1, None, line == 'i')
        self._current_instruction_set.text()[self._current_instruction_index][2].append(step)

def parse_position(pstr):
    global position_pattern
    p_re = re.match(position_pattern, pstr)
    if p_re is None:
        raise Exception(pstr)
    else:
        return (int(p_re.group(1)), int(p_re.group(2)), int(p_re.group(3)))

if __name__ == '__main__':
    parser = OptionParser(usage = 'usage: %prog -m ALL_POSITION_FILE instructions_file')
    parser.add_option('-m', '--maps', dest = 'all_position_file', help = 'TSV file including all positions')
    (options, args) = parser.parse_args()

    ## Read all positions
    for line in open(options.all_position_file):
        s = line.split('\t')
        map_name = s[0]
        position = parse_position(s[1])
        position_dict = dict([(estr.split('=', 1)[0], parse_position(estr.split('=', 1)[1]) if estr.split('=', 1)[1].startswith('(') else int(estr.split('=', 1)[1])) for estr in s[2:]])
        maps[map_name][position] = position_dict
        if position_dict.has_key('num'):
            maps_numbered_positions[map_name][position_dict['num']] = position

    ## Read instructions
    instructions = sorted(read_instructions(args[0]).values(), key = lambda x: x.id())

    print colored('Loaded %d instruction sets' % (len(instructions)), 'yellow')

    CMD(instructions, args[0]).cmdloop()


