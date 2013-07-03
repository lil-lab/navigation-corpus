from navigationutils import *
import sys
from optparse import OptionParser, OptionGroup
from collections import defaultdict
from operator import itemgetter


'''
    Pre-process instructions and traces for GIZA++ over observations and instructions.
'''


stopwords = ['i',
 'me',
 'my',
 'myself',
 'we',
 'our',
 'ours',
 'ourselves',
 'you',
 'your',
 'yours',
 'yourself',
 'yourselves',
 'he',
 'him',
 'his',
 'himself',
 'she',
 'her',
 'hers',
 'herself',
 'it',
 'its',
 'itself',
 'they',
 'them',
 'their',
 'theirs',
 'themselves',
 'what',
 'which',
 'who',
 'whom',
 'this',
 'that',
 'these',
 'those',
 'am',
 'is',
 'are',
 'was',
 'were',
 'be',
 'been',
 'being',
 'have',
 'has',
 'had',
 'having',
 'do',
 'does',
 'did',
 'doing',
 'a',
 'an',
 'the',
 'and',
 'but',
 'if',
 'or',
 'because',
 'as',
 'until',
 'while',
 'of',
 'at',
 'by',
 'for',
 'with',
 'about',
 'against',
 'between',
 'into',
 'through',
 'during',
 'before',
 'after',
 'above',
 'below',
 'to',
 'from',
 'up',
 'down',
 'in',
 'out',
 'on',
 'off',
 'over',
 'under',
 'again',
 'further',
 'then',
 'once',
 'here',
 'there',
 'when',
 'where',
 'why',
 'how',
 'all',
 'any',
 'both',
 'each',
 'few',
 'more',
 'most',
 'other',
 'some',
 'such',
 'no',
 'nor',
 'not',
 'only',
 'own',
 'same',
 'so',
 'than',
 'too',
 'very',
 's',
 't',
 'can',
 'will',
 'just',
 'don',
 'should',
 'now']


symbol_index_counter = 0
def next_symbol_index():
    global symbol_index_counter
    symbol_index_counter += 1
    return symbol_index_counter

word_index_counter = 0
def next_word_index():
    global word_index_counter
    word_index_counter += 1
    return word_index_counter

symbol_voc = defaultdict(next_symbol_index)
symbol_counters = defaultdict(int)
word_voc = defaultdict(next_word_index)
word_counters = defaultdict(int)


if __name__ == '__main__':
    parser = OptionParser(usage = 'usage: %prog -i INSTRUCTIONS -o OUTPUT_REPFIX TRACE_FILES')
    parser.add_option('-i', '--instructions', dest = 'instructions', help = 'Instructions file')
    parser.add_option('-o', '--output-prefix', dest = 'output_prefix', help = 'Output prefix')
    (options, args) = parser.parse_args()

    if options.instructions is None or options.output_prefix is None:
        parser.error('Instructions file and output prefix are missing')

    tokenizer = get_tokenizer()

    instructions = read_instructions(options.instructions)

    # Collect all 1grams and filter them
    word_counts = defaultdict(int)
    for instruction in instructions.values():
        instruction_words = tokenizer.raw_tokenize(instruction.text().lower())
        for word in instruction_words:
            word_counts[word] += 1

    words_to_use = set(map(itemgetter(0), filter(lambda x: x[1] > 9 and len(x[0]) >= 3 and not x[0] in stopwords, word_counts.items())))

    bitext_counts = defaultdict(int)
    for f in args:
        traces = read_follower(f)
        for trace in traces.values():
            # Convert the traces to a set of symbols
            trace_symbols = set()
            for step in trace.path():
                trace_symbols.add(step.act())
                for horizon in step.observation():
                    for item in horizon:
                        trace_symbols.add(item)

            # Add the symbols to the symbols vocabulary
            for symbol in trace_symbols:
                symbol_voc[symbol]
                symbol_counters[symbol] += 1

            # Get the trace's instruction
            instruction = instructions[trace.instruction_id()]

            # Add the instruction's words to the vocabulary
            instruction_words = filter(lambda x: x in words_to_use, tokenizer.raw_tokenize(instruction.text().lower()))
            for word in instruction_words:
                word_voc[word]
                word_counters[word] += 1

            # Create pair of instruction and trace and add to dictionary
            bitext_counts[(' '.join(map(lambda x: str(word_voc[x]), instruction_words)),
                           ' '.join(map(lambda x: str(symbol_voc[x]), trace_symbols)))] += 1

    # Write vocabulary files
    out = open(options.output_prefix + '.symbols.voc', 'w')
    for symbol, index in sorted(symbol_voc.items(), key = itemgetter(1)):
        out.write('%d %s %d\n' % (index, repr(symbol), symbol_counters[symbol]))
    out.close()

    out = open(options.output_prefix + '.words.voc', 'w')
    for word, index in sorted(word_voc.items(), key = itemgetter(1)):
        out.write('%d %s %d\n' % (index, str(word), word_counters[word]))
    out.close()

    # Write bitext file
    out = open(options.output_prefix + '.bitext', 'w')
    for bitext_pair, count in bitext_counts.items():
        print >> out, count
        print >> out, bitext_pair[1]
        print >> out, bitext_pair[0]
    out.close()



