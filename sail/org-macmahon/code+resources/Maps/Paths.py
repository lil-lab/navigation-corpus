from pylab import mean, median, std

GridLengths = [3,3,3,4,2,2,1,1,7,5,1,2,2,3,1]
GridInters  = [4,4,4,5,3,3,2,2,8,6,1,3,3,4,1]
GridRatio = sum(GridInters)/float(sum(GridLengths)+len(GridLengths))
GridRatios = [float(i)/(l+1) for l,i in zip(GridLengths, GridInters)]
print 'Grid','\tMean', '%4.2g'%GridRatio, 'Total', sum(GridLengths), 'Paths', len(GridInters),
print 'Mean len', '%4.2g'%mean(GridLengths), 'Median len', '%4.2g'%median(GridLengths),
print 'StdDev len', '%4.2g'%std(GridLengths)
#print 'Mean ratio', '%4.2g'%mean(GridRatios), 'Median ratio', '%4.2g'%median(GridRatios)

JellyLengths = [5,1,3,3,3,6,1,1,1,1,1,1,2,1,3,1,2,1,3,1]
JellyInters  = [2,2,3,2,3,4,1,1,2,2,2,2,3,2,2,2,3,2,3,1]
JellyRatio = sum(JellyInters)/float(sum(JellyLengths)+len(JellyLengths))
JellyRatios = [float(i)/(l+1) for l,i in zip(JellyLengths, JellyInters)]
print 'Jelly','\tMean', '%4.2g'%JellyRatio, 'Total', sum(JellyLengths), 'Paths', len(JellyInters),
print 'Mean len', '%4.2g'%mean(JellyLengths), 'Median len', '%4.2g'%median(JellyLengths),
print 'StdDev len', '%4.2g'%std(JellyLengths)
#print 'Mean ratio', '%4.2g'%mean(JellyRatios), 'Median ratio', '%4.2g'%median(JellyRatios)

LLengths = [1,3,1,2,9,5,2,1,4,4,4,1,1,3]
LInters  = [1,4,1,2,7,4,1,1,4,4,3,2,1,2]
LRatio = sum(LInters)/float(sum(LLengths)+len(LLengths))
LRatios = [float(i)/(l+1) for l,i in zip(LLengths, LInters)]
print 'L''\tMean', '%4.2g'%LRatio, 'Total', sum(LLengths), 'Paths', len(LInters),
print 'Mean len', '%4.2g'%mean(LLengths), 'Median len', '%4.2g'%median(LLengths),
print 'StdDev len', '%4.2g'%std(LLengths)
#print 'Mean ratio', '%4.2g'%mean(LRatios), 'Median ratio', '%4.2g'%median(LRatios)



