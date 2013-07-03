#!/usr/bin/env python
import pylab,glob
allLengths = []
print 'Shortest route statistics'
print 'Env\t mean\t median'
for file in glob.glob('*.eff'):
    lengths = []
    for line in open(file):
        if line.startswith('#'): continue
        s,d,l = line.split(' ')[:3]
        lengths.append(int(l))
    name = file.split('.')[0][len('Direction'):]
    print name, pylab.mean(lengths), pylab.median(lengths)
    allLengths.extend(lengths)
print 'All', pylab.mean(allLengths[21:]), pylab.median(allLengths[21:])
