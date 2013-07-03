from nltk.probability import FreqDist
import re, pylab

import DirectionCorpus, Utility
from SubjectLogs.SubjectGroups import *

def count_words(reader, group, directorSet):
    fdist = FreqDist()
    dirRegexp = DirectionCorpus.constructItemRegexp(directorSet, Maps, mapversions='[01]')
    Instructions = [item for item in reader.items(group) if re.match(dirRegexp,item)]
    Instructions.sort()
    # Delete duplicate director routes, keep last
    Remove = []
    for i in range(1,len(Instructions)):
        if Instructions[i][:-5] == Instructions[i-1][:-5]: Remove.append(Instructions[i-1])
    for i in Remove:
        Instructions.remove(i)
    
    for item in Instructions:
        for token in reader.read(item)['WORDS']:
            if token['TEXT'].isalnum():
                fdist.inc(token['TEXT'])
            elif token['TEXT'] == '.':
                fdist.inc('<SENTENCES>')
    return fdist, len(Instructions)

def tfidf(word, fdist, Documents, DocGroup):
    """
    returns the text frequency - inverse document frequency.
    Takes a word, a FreqDist, a dictionary of FreqDists, and a Group of FreqDist names to form the document.
    """
    text_freq = fdist.count(word)
    inv_doc_freq = pylab.log(len(DocGroup)/sum([word in Documents[subgroup] for subgroup in DocGroup]))
    return text_freq*inv_doc_freq

def abbrev(w, maxlen=12):
    if len(w) <= maxlen: return w
    return w[:maxlen]+'.'

class latex_table:
    def __init__(self, filename, dataformat, ColLabels, RowData=[]):
        self.file = open(filename+'.tex', 'w')
        self.file.write(r'\begin{tabularx}{\textwidth}{X%s}'%('r'*len(ColLabels)) + '\n')
        self.file.write(' & '.join(ColLabels)+'\\\\\n')
        print '\t', filename, '\n', '\t'.join(ColLabels)
        self.list_formats = dataformat.split(' ')
        if RowData:
            for data in RowData: self.row(*data)
            self.close()
    def row(self, *row):
        formatted = [df%datum for df,datum in zip(self.list_formats,row)]
        print '\t'.join(formatted)
        self.file.write(' & '.join(formatted)+'\\\\\n')
    def write(self, latex_txt):
        self.file.write(latex_txt)
    def close(self):
        self.file.write(r'\end{tabularx}')
        print
        self.file.close()

class language_stats:
    def __init__(self, n, words, vocabulary, uniq_voc, sentences, instructions):
        self.n = n
        self.words = words
        self.vocabulary = vocabulary
        self.uniq_voc = uniq_voc
        self.sentences = sentences
        self.instructions = instructions
    def __str__(self):
        strs = []
        for attr in ('words', 'vocabulary', 'uniq_voc', 'sentences', 'instructions'):
            strs.append('%s: %s' % (attr,getattr(self,attr)))
        return ', '.join(strs)

if __name__ == '__main__':
    from SubjectLogs.SubjectGroups import *
    StopWords = dict.fromkeys(['a', 'and', 'the', 'of', '<SENTENCES>'])
    maxwords = 7
    
    DirectorSets = {'All' : Directors+Directors3,
                    'Exp.1' : Directors1,
                    'Exp.2' : Directors2,
                    'Exp.3' : Directors3,
                    'Discrete' : Directors1+Directors2,
                    'Male' : Director_Men,
                    'Female' : Director_Wmn}
    for director in Directors+Directors3:
        DirectorSets[director] = [director]
    DirectorOrder = (['All', '|', 'Exp.1', 'Exp.2', 'Exp.3', '|', 'Discrete', '|', 'Male', 'Female', '|']
                     +Directors1+['|']+Directors2+['|']+Directors3)
    
    InstructionSets = {}
    GroupStats = {}
    TopWords = {}
    reader = DirectionCorpus.DirectionCorpusReader(DirectionCorpus.constructItemRegexp(Directors, Maps, '[01]'))
    StatsTable = latex_table('Graphs/Table_Corpora_Director_Stats', '%s %d %4d %3d %6d %5.1f %4.1f ',
                             ['Name', 'Instructions', 'Vocabulary', 'Unique Voc.',
                              'Mean Words', 'Mean Sentences'])
    row_written = False
    for name in DirectorOrder:
        if name == '|':
            if row_written: StatsTable.write('\\hline\n')
            continue
        fdist,doccount = count_words(reader, 'CleanDirs', DirectorSets[name])
        InstructionSets[name] = fdist
        sentences = fdist.count('<SENTENCES>')
        numwords = fdist.N() - sentences
        vocsize = fdist.B() - 1
        if name == 'All': uniq_voc = vocsize
        else: # Count items appearing only in this set.
            uniq_voc = len([w for w in InstructionSets[name].samples()
                            if InstructionSets['All'].count(w) - InstructionSets[name].count(w) == 0])
        if name in Directors+Directors3:
            StatsTable.row(name, doccount, vocsize, uniq_voc,
                           numwords/float(doccount), sentences/float(doccount))
            row_written = True
        GroupStats[name] = language_stats(len(DirectorSets[name]), numwords/float(doccount),
                                          vocsize, uniq_voc, sentences/float(doccount), doccount)
        count = 0
        TopWords[name] = []
        for word in fdist.sorted_samples():
            if word not in StopWords:
                TopWords[name].append(word)
                count += 1
                if count >= maxwords: break
    StatsTable.close()

    top_words_table = latex_table('Graphs/Table_Corpora_Top_Words', '%s '*(maxwords+1),
                ['Group']+['Word '+str(i) for i in range(1,maxwords+1)])
    for name in DirectorOrder:
        if name == '|':
            top_words_table.write('\\hline\n')
            continue
        top_words_table.row(*([name]+[r'{\small %s}'%abbrev(w) for w in TopWords[name]]))
    top_words_table.close()

    tfidf_table = latex_table('Graphs/Table_Corpora_TFIDF', '%s '*(maxwords),
                              ['Group']+['Word '+str(i) for i in range(1,maxwords)])
    for group in [('Exp.1','Exp.2','Exp.3'),
                  ('Discrete', 'Exp.3'),
                  ('Male', 'Female'),
                  Directors1,
                  Directors2,
                  Directors3,
                  ]:
        for name in group:
            tfidfs = [(tfidf(word, InstructionSets[name], InstructionSets, group), word)
                     for word in InstructionSets[name].sorted_samples()]
            tfidfs.sort()
            tfidf_table.row(*([name]+[r'{\small %s}'%abbrev(w) for s,w in tfidfs[-1:-maxwords:-1]]))
        tfidf_table.write('\\hline\n')
    tfidf_table.close()

    corpus_means = latex_table('Graphs/Table_Corpora_RIMeans', '%s '*6,
                               ['Group', 'n', 'Words', 'Vocabulary', 'Sentences', 'Instructions'])
    for group in 'Exp.1','Exp.2','Exp.3', 'Discrete', 'Male', 'Female':
        print group, 'Statistics',
        Stats = [GroupStats[subgroup] for subgroup in DirectorSets[group]]
        Row = [group, str(GroupStats[group].n)]
        for statname in 'words','vocabulary','sentences','instructions':
            Row.append('%4.1f, SEM = %4.1f' % (pylab.mean([getattr(stat,statname) for stat in Stats]),
                                             Utility.stderr([getattr(stat,statname) for stat in Stats])))
        corpus_means.row(*Row)
    corpus_means.close()

    CleanedInsts = [ri.split('-')[1] for ri in reader.items('CleanDirs')]
    CleanedInsts.sort()
    Matches = open('MarcoLogs/Matches','w')
    for ri in CleanedInsts:
        Matches.write(ri+'\n')
    Matches.close()
