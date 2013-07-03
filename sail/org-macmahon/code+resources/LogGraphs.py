import os, math, Numeric, pylab
#Plotting setup
figure = 1
graph = 1
import LogAnalyzer
from Utility import runningAverage

Formats = ['bo', 'g<',   'r>',   'cs',  'm^',   'kp']

def simpleGraph(X, Y, Title, Filename,
                Legend=None, Caption=None, Line='', Labels=['',''], Grid=False, Ticks=None, Formats=Formats,
                Fig=None):
    if not graph: return
    Fig = pylab.figure(Fig)
    if Line: Formats = [fmt+Line for fmt in Formats]
    for x,y,fmt in zip(X,Y,Formats):
        pylab.plot(x,y,fmt)
    if Caption: pylab.text(0,-1.2,Caption)
    if Grid or Ticks:
        if Ticks:
            if type(Ticks[0]) is tuple: pylab.xticks(*Ticks[0])
            else: pylab.xticks(Ticks[0])
            pylab.yticks(Ticks[1])
        else:
            pylab.xticks(X[0])
            pylab.yticks(min([min(y) for y in Y]), max([max(y) for y in Y]))
    adornGraph(Title,Filename,Labels[0],Labels[1],Legend,Fig,Grid)
    return Fig

def graphStats(results,FollowerID,TestName,F1,F2):
	if not graph: return
	if FollowerID[0] == '(': FollowerID = 'AllFollowers'
	Fig=pylab.figure()
	pylab.plot(results[F1],'bo')
	pylab.plot(results[F2],'g+')
	pylab.axis([0,7,0,7])
	Axes = pylab.gca()
	Axes.set_yticks([0,1,2,3,4,5,6,7])
	Axes.set_xticks(range(len(results[F1])))
	adornGraph(Title = FollowerID + ' Confidence and Rating over time',
		   Filename = FollowerID+'_'+TestName+'_TimeSeries',
		   Legend = ('Navigation Confidence','Direction Rating'))
	pylab.figure()
	#pylab.scatter(results['NavConf'],results['DirRtng'])
	pylab.pcolor(LogAnalyzer.occurences(results[F1],results[F2]))
	pylab.axis([0,7,0,7])
	for i in range(1,7):
		pylab.text(-.5,i-.5,str(i))
		pylab.text(i-.5,-.5,str(i))
	Axes = pylab.gca()
	#Axes.set_yticks([0,1,2,3,4,5,6,7])
	#Axes.set_xticks(range(len(results[F1])))
	adornGraph(Title = FollowerID + ' Confidence and Rating compared',
		   Filename = FollowerID+'_'+TestName+'_pcolor',
		   XLabel = 'Direction Rating', YLabel = 'Navigation Confidence')

def graphPer(StatTable, Fields=['_Efficiency', '_NavConf', '_DirRtng', '_TgtFound',],
             TestName='', StatType='A_', StdType=None, Range=None):
	if not graph: return
	Fig = pylab.figure()
	Names = []
	maxStat = 0
	if Range: l =len(Range)+1; FollowerNames = [StatTable['/FollowerID'][i] for i in Range]
	else: l = len(StatTable['/FollowerID'])+1;  FollowerNames = StatTable['/FollowerID']
	for field,Line in zip(Fields,['-.',':','-', '--',]):
		if len(FollowerNames) > 6:offset = .5
		else: offset = 1
		for Giver,Fmt in zip(LogAnalyzer.Directors, Formats):
			Name = StatType+Giver+field
			Names.append(Name)
			if Range:
				StatX = [StatTable[Name][i] for i in Range]
				if StdType: StatY = [StatTable[StdType+Giver+field][i] for i in Range]
			else:
				StatX = StatTable[Name]
				if StdType: StatY = StatTable[StdType+Giver+field]
			Length = len(StatX)
			if StdType: maxStat = max(maxStat,max(StatX+StatY))
			else : maxStat = max(maxStat,max(StatX))
			Xvals = [x + offset  for x in range(Length)] 
			if StdType: pylab.errorbar(Xvals,StatX,yerr=StatY,fmt=Fmt)#+Line)
			else: pylab.plot(Xvals,StatX,Fmt)#+Line)
			#pylab.semilogy(Xvals,StatX,Fmt+Line)
			if len(FollowerNames) < 6:offset += 0.1
	if Range: l =len(Range)+1; FollowerNames = [StatTable['/FollowerID'][i] for i in Range]
	else: l = len(StatTable['/FollowerID'])+1;  FollowerNames = StatTable['/FollowerID']
	if len(FollowerNames) > 6: 
		for num,Follower in zip(range(1,l),FollowerNames):
			pylab.text(num,-0.5,Follower[0:7],rotation='vertical')
			pylab.text(num,6.5,Follower[0:7],rotation='vertical')
	else:
		for num,Follower in zip(range(1,l),FollowerNames):
			pylab.text(num,-0.5,Follower,rotation='horizontal')
			pylab.text(num,6.5,Follower,rotation='horizontal')
	pylab.axis([0,Length*2,0,max(int(math.ceil(maxStat)),6)])
	pylab.grid(1)
	Axis = pylab.gca()
	Axis.set_yticks(range(int(math.ceil(maxStat+2))))
	#Axis.set_xticks([])
	adornGraph(Title =  'Results per direction giver: '+StatType+TestName,
		   Filename = 'Results_per_'+StatType+TestName,
		   Legend = Names,
			   )

def adornGraph(Title=None, Filename=None, XLabel=None, YLabel=None, Legend=None, Figure=None, Grid=False):
    if not Figure: pylab.figure()
    if Legend: pylab.legend(Legend,loc=0)
    if YLabel: pylab.ylabel(YLabel, fontsize='larger')
    if XLabel: pylab.xlabel(XLabel, fontsize='larger')
    if Title: pylab.title(Title)
    if Grid: pylab.grid(True)
    if Filename:
        pylab.savefig(os.path.join('Graphs',Filename))
        pylab.savefig(os.path.join('Graphs',Filename+'.eps'))

def graphPerDirection(StatTable,Fields):
	if not graph: return
	Fig = pylab.figure()
	Names = []
	maxStat = 0
	TestName = ''
	FieldNums={'Efficiency':0,'TgtFound':1,'NavConf':2,'DirRtng':3}
	for Field,Line in zip(Fields,['-.',':','--','-']):
		TestName += Field+'_'
		for Follower,Dirs,Fmt in zip(StatTable['/FollowerID'],StatTable['PerDirection'],
					     Formats[0:3]+(['b.', 'g.',   'r.',   'c.',  'm.',   'k.']*6)):
			if Follower == 'AllFollowers': continue 
			if Follower == '(BJS|MTM|JPR)': continue 
			Names.append(Follower+'_'+Field)
			XValues = []
			YValues = []
			xoffset = 1
			for Env in ['Grid']:#, 'L', 'Jelly']:
				for P1 in range(1,8):
					for P2 in range(1,8):
						if P1 is not P2:
							for dirNum in [2,1]:
								for Giver,yoffset in zip(LogAnalyzer.Directors, [-.1, -.05, 0, .05, .1, .15,]):
									Direction = Giver+'_'+Env+'[01]_'+str(P1)+'_'+str(P2)+'_Dirs_1.txt' ### FIXME handle Dirs_2.txts
									if Field is 'Efficiency': yoffset = -1
									try:
										YVal = Dirs[Direction][FieldNums[Field]]
										XValues.append( xoffset)
										YValues.append(YVal+yoffset )
										break
									except KeyError: pass #print 'ERROR: Missing key',Follower,Direction,Field,Dirs.get(Direction)
							xoffset += 1
			if XValues and YValues:
				maxStat = max(maxStat,max(YValues))+yoffset
				pylab.plot(XValues,YValues,Fmt)
			else: print 'Missing',Follower,Field
	pylab.axis([-1,xoffset+2,0,int(math.ceil(maxStat))])
	pylab.grid(0)
	Axis = pylab.gca()
	Axis.set_yticks(range(-1,maxStat+2))
	Axis.set_xticks(range(0,xoffset+2,20))
	adornGraph(Title =  'Results per direction set: '+TestName,
		   Filename = 'Results_dirs_'+TestName,
		   Legend = LogAnalyzer.Followers+LogAnalyzer.Directors,
			   Figure = Fig,
			   )
#graphPerDirection(s1,['Efficiency','NavConf','DirRtng'])

def graphPerStats(StatTable,StatsName='',Range=None, ErrorBars=0):
	if not graph: return
	if ErrorBars: Bars = ['D_', 'E_']
	else: Bars = [None,None]
	for StatType, StdType in zip(['A_', 'N_'], Bars):
		graphPer(StatTable, ['_Efficiency', '_TgtFound',], StatsName+'_Efficiency-Correctness', StatType, StdType, Range)
		graphPer(StatTable, ['_NavConf', '_DirRtng',],     StatsName+'_Confidence-Rating', StatType, StdType, Range)
		graphPer(StatTable, ['_DirRtng', '_Efficiency',],  StatsName+'_Rating-Efficiency', StatType, StdType, Range)
		graphPer(StatTable, ['_NavConf', '_Efficiency',],  StatsName+'_Confidence-Efficiency', StatType, StdType, Range)
		graphPer(StatTable, ['_NavConf', '_Efficiency','_DirRtng',], StatsName+'_Confidence-Efficiency-Rating', StatType, StdType, Range)

def graphErrorbar(X,Y,Names=[],TestName='',Yerrs=[],Legend=[],Caption=''):
	if not graph: return
	Fig = pylab.figure()
	#for Fmt in Formats: pylab.plot(14,4,Fmt) #For legend
	Lines = []
	if len(X) == 6: Fmts = Formats
	else: Fmts = ['y<', 'k>', 'rs', 'b^', 'gx']
	for (x,y,yerr,Fmt) in zip(X,Y,Yerrs,Fmts):
		#print len(x),len(y),len(yerr[0]),len(yerr[1])
		#print x,'\n',y,'\n',yerr
		Lines += [pylab.plot(x,y,Fmt)]
		#Lines += [pylab.errorbar(x,y,yerr=yerr,fmt=Fmt)]
	TextLoc = -.3*max(y)
	for num,name in zip(range(len(Names)),Names):
		pylab.text(num+.5,TextLoc,name[0:7],rotation='vertical')
	if Caption: pylab.text(0,TextLoc-1.2,Caption)
	pylab.axis([0,max(x)+1,TextLoc,max(y)])
	pylab.grid(1)
	Axis = pylab.gca()
	R = [0, 1, 2]
	while R[-1] < max(y):
		R.append(R[-1]*2)
	Axis.set_yticks(R)
	#Axis.set_yticks(range(0,max(y)+1,100))
	Axis.set_xticks(range(max(x)+1))
	pylab.legend([l[0] for l in Lines],Legend)
	adornGraph(Title =  'Occurrences: '+TestName,
			   Filename = 'Errorbar_'+TestName,
			   Figure = Fig,
			   )

def graphScatter(X,Y,Names=['X','Y'],TestName='',Legend=[],Caption='',LogX=0,RunningAvg=0,Lines=None,Colors=[None]):
	if not graph: return
	Fig = pylab.figure()
	if len(X) == 6: Fmts = Formats
	else: Fmts = ['k>', 'go', 'b^', 'rs', 'y<',]
	if Colors[0]: pylab.jet()
	else: Colors = [f[0] for f in Fmts]
#	LegendKey = []
	if Legend:
		for fmt in Fmts: pylab.plot([0],[0],fmt)
	if Lines:
		for x1,y1,x2,y2 in Lines:
			pylab.plot([x1,x2],[y1,y2],'-')
	dot = 0.1*min(max([max(y) for y in Y]),max([max(x) for x in X]))
	for (x,y,color,fmt) in zip(X,Y,Colors,Fmts):
		pylab.scatter(x, y, c=color,marker=fmt[1])
#		pylab.plot(x, y, fmt)
		if RunningAvg:
			pylab.plot(runningAverage(x,10), runningAverage(y,10), '.y-')
			pylab.plot(runningAverage(x,20), runningAverage(y,20), '.g-')
		#LegendKey.append(pylab.plot(10, 10, Fmt[0]))
	Axes = pylab.gca()
	if LogX:
		for i in [1,2,3,4,5,6,7,8,9,10,11,16,26,36,51,76,101,151,201]:
			pylab.text(math.log(i),-1.2,str(i-1))
	adornGraph(Title =  'Scatter: '+TestName,
			   Filename = 'Scatter_'+TestName,
			   Figure = Fig,
			   XLabel = Names[0],
			   YLabel = Names[1],
			   Legend = Legend,
			   )
