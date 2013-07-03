from navigationutils import *
import sys
from optparse import OptionParser, OptionGroup
from collections import defaultdict
from operator import itemgetter

'''
    Compute co-occurrence statistics (using PMI) for all n-grams vs. observations and actions.
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

def get_ngrams(tokens, n):
    global stopwords
    ngrams = []
    for i in range(len(tokens)):
        for l in range(1, n + 1):
            if i + 1 >= l:
                ngram = tuple(tokens[i + 1 - l:i + 1])
                drop_ngram = False
                for word in ngram:
                    if word in stopwords or len(word) < 3: drop_ngram = True
                if not drop_ngram:
                    ngrams.append(ngram)
    return ngrams

def jaccard(count_x, count_y, count_xy):
    return float(count_xy) / (float(count_x) + float(count_y) - float(count_xy))

def pmi(p_x, p_y, p_xy):
    return math.log(float(p_xy) / (float(p_x) * float(p_y)))

def ratio_near_one(count_y, count_xy):
    return -abs(1 - float(count_y) / float(count_xy))

if __name__ == '__main__':
    # Command line argument
    parser = OptionParser(usage = 'usage: %prog [options] -i INSTRUCTIONS_FILE TRACE_FILES')
    parser.add_option('-i', '--instructions', dest = 'instructions', help = 'Instructions file.')
    group = OptionGroup(parser, 'Optional')
    group.add_option('-n', '--ngram', dest = 'ngram', type = 'int', default = 2, help = 'Size of ngrams to use. Default: 2.')
    group.add_option('-o', '--output', dest = 'output', help = 'Output file')
    group.add_option('-t', '--top2err', dest = 'top2err', type = 'int', help = 'Output top-k to stderr for each symbol')
    parser.add_option_group(group)
    (options, args) = parser.parse_args()

    if options.instructions is None:
        parser.error('Missing instructions file')

    N = options.ngram
    tokenizer = get_tokenizer()

    instructions = read_instructions(options.instructions)
    followers_traces = {}
    for f in args:
        followers_traces[f] = read_follower(f)

    # Collect all ngrams
    ngrams = defaultdict(int)
    for instruction in instructions.values():
        count_used = 0
        for f in args:
            follower_traces = followers_traces[f]
            if follower_traces.has_key(instruction.id()):
                count_used += 1
        tokens = tokenizer.raw_tokenize(instruction.text().lower())
        for ngram in get_ngrams(tokens, N):
            ngrams[ngram] += count_used

    # Filter out ngrams that appear less than X times
    ngrams = dict(filter(lambda x: x[1] > 9, ngrams.items()))

    # Collect all count of actions and observations
    observations = defaultdict(int)
    observations_ngrams = defaultdict(int)
    for f in args:
        follower_traces = followers_traces[f]
        for trace in follower_traces.values():
            if instructions.has_key(trace.instruction_id()):
                trace_ngrams = set(filter(lambda x: ngrams.has_key(x), get_ngrams(tokenizer.raw_tokenize(instructions[trace.instruction_id()].text().lower()), N)))
                # Collect all items into a set
                items = set()
                for step in trace.path():
                    items.add(step.act())
                    for horizon in step.observation():
                        for item in horizon:
                            items.add(item)
                # Count all items, each item is counted once, trying to keep things balanced
                for item in items:
                    observations[item] += 1
                    for ngram in trace_ngrams:
                        observations_ngrams[(item, ngram)] += 1

    # Compute PMI for each pair which has a count larger than 1
    # x = observation
    # y = ngram
    X = observations
    Y = ngrams
    XY = observations_ngrams
    total_x = float(sum(X.values()))
    total_y = float(sum(Y.values()))
    total_xy = float(sum(XY.values()))
    pmis = []
    for x_y, xy_count in XY.items():
        x = x_y[0]
        y = x_y[1]
        p_x = float(X[x]) / total_x
        p_y = float(Y[y]) / total_y
        p_xy = float(xy_count) / total_xy
        # pmi_value = ratio_near_one(Y[y], xy_count)
        # pmi_value = jaccard(X[x], Y[y], xy_count) * pmi(p_x, p_y, p_xy)
        pmi_value = pmi(p_x, p_y, p_xy)
        pmis.append((x_y, pmi_value))

    # Sort PMIs
    pmis.sort(key = itemgetter(1), reverse = True)

    # Write to file or stdout
    if options.output is None:
        out = sys.stdout
    else:
        out = open(options.output, 'w')
    for x_y_pmi_value in pmis:
        x_y = x_y_pmi_value[0]
        pmi_value = x_y_pmi_value[1]
        out.write('%s\t%s\t%.20f\t%d\t%d\t%d\n' % (repr(x_y[0]), ' '.join(x_y[1]), pmi_value, X[x_y[0]], Y[x_y[1]], XY[x_y]))

    if not options.top2err is None:
        k = options.top2err
        symbol_to_word_conf = defaultdict(list)
        for x_y_pmi_value in pmis:
            x_y = x_y_pmi_value[0]
            pmi_value = x_y_pmi_value[1]
            symbol = x_y[0]
            ngram = ' '.join(x_y[1])
            symbol_to_word_conf[symbol].append((ngram, pmi_value))
        for symbol, word_conf in sorted(symbol_to_word_conf.items(), key = lambda x: str(x[0])):
            word_conf.sort(key = itemgetter(1), reverse = True)
            for word, score in word_conf[:k]:
                print >> sys.stderr, '%s\t%s\t%.20f' % (word, repr(symbol), score)
            print >> sys.stderr








