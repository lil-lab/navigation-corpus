#!/usr/bin/python
import re, string, os, math
import Numeric, MLab
try:
    import pychecker.checker
except ImportError: pass
import LogAnalyzer,LogGraphs,Tagger
import cPickle,pdb

Objects = ['aesal','bench','chair','coat rack','easel','empty','furniture','hat rack','hatrack','lamp','nothing','object','sofa','stool']
Structures = ['alley','corner','end','go right or left','intersect','movement','wall']
Appearances = ['bare','black','blue','brick','brown','buterfly','carpet','cement','concrete','dark','eiffel towers','fish','flowered','grass','gray','green','grey','hexagonal','octagon','pictures','pink','plain','red','rock','rose','stone','tile','wood','yellow']
Paths = ['alley','alley','carpet','corridor','floor','hall','path','road','street','-tiled','walkway', ]
Dists = ['a few','all of the way','all the way','block','five','four','movement','once','one','segments','six','space','the very end','three','times','times','twice','two']
Dirs = ['left','right']
Faces = ['face','facing','in the direction','look for','looking at','until you can see','until you see']
Finds = ['find','go to']
Orients = ['away from','put your back to','so that','with your back to','your back against']
Regions = ['area']
Travels = ['follow','go','head', 'move','take','walk']
Turns = ['face','go left','go right','make','orient','place your','take a','stand','turn',]
Alongs = ['along','down','on','onto']
Locs = ['at','here','in','there','when','where']
Towards = ['in the direction of','toward','towards']
Untils = ['down to','til','to','until']
Views = ['be visible','you can look','you see','you should be facing','you should be looking at','you should see']
Words = ['\w+']
DirTraitNames = ['Travels','Turns', 'Faces','Finds',  #Verbs
				'Objects','Structures','Paths','Regions', 'Locs','Views', #Nouns
				'Appearances', 'Dists','Dirs', #Adj
				'Alongs','Towards','Untils','Orients', #Adv
				 'Words']

def parseDirections(patterns,dirTexts,Ratings,results):
	for dirID,dirText in dirTexts.items():
		try: TraitList = [Ratings[dirID][2], Ratings[dirID][3], Ratings[dirID][4],
						  Ratings[dirID][5], Ratings[dirID][6]+Ratings[dirID][7]]
		except KeyError: TraitList = [None,None]
		for name in DirTraitNames:
			TraitList.append(len(patterns[name].findall(dirText)))
		results[dirID] = TraitList 

def printPerDir(Names,ValuesLists,Order):
	i = 0
	for dirName in Order:
		if i%10 == 0: print string.join([x[0:3] for x in Names],'\t'),i
		try:
			for Values in ValuesLists:
				print string.join([str(x)[0:3] for x in Values[dirName]],'\t'),'\t\t',
			print dirName
		except KeyError: pass
		i += 1

def scaleRatingsLex(x): return max((x[3]*100+x[2]*10+x[0]-110.0)/551.0, 0.0)
def cmpRatingsLex(x,y):
	if x[3] < y[3]: return -1	#Rating first
	if x[3] > y[3]: return 1
	if x[2] < y[2]: return -1 	#Confidence
	if x[2] > y[2]: return 1
	if x[0] < y[0]: return -1   #Efficiency
	if x[0] > y[0]: return 1
	return 0

def scaleRatingsSum(x): return max((x[3]+x[2]-2.0)/10.0, 0.0)
def cmpRatingsSum(x,y):
	return cmp(x[2]+x[3],y[2]+y[3])

def scaleRatingsDiscSum(x): return max(x[0]*(x[3]+x[2])/10.0, 0.0)
def cmpRatingsDiscSum(x,y):
	Comp = cmp(x[0]*(x[2]+x[3]),y[0]*(y[2]+y[3]))
	if Comp != 0: return Comp
	return cmp(x[3],y[3])

def scaleEfficiency(x): return x[0]
def cmpEfficiency(x,y):
	return cmp(x[0],y[0])

def cmpNull(x,y): return 0

ScaleFn = {}
for name,fn in zip(['Alpha','Lexical','Sum','DiscSum','Efficiency'],
                   [0,scaleRatingsLex,scaleRatingsSum,scaleRatingsDiscSum,scaleEfficiency]):
    ScaleFn[name] = fn

def percentile(m,p):
    """percentile(m) returns the pth percentile of m along the first dimension of m.
    """
    if isinstance(m,list): a = Numeric.array(m)
    else: a = m
    sorted = MLab.msort(a)
    if a.shape[0] % 2 == 1:
        return sorted[int(a.shape[0]*p/100)]
    else:
        index=a.shape[0]*p/100
        return (sorted[index-1]+sorted[index])/2

def SplitPercentile(List,numCuts):
    L = MLab.msort(Numeric.array(List))
    Percentiles = []
    count = len(L)
    for i in range(1,numCuts):
        p = i * 100.0/numCuts
        Percentiles.append(percentile(L,int(p)))
    return Percentiles

class DirTraitInfo:
	"""Keys,Ratings,Stats,StatNames,lastStatNum"""
	pass # Empty 'struct' class

def sumOverStats(AccumNames,AccumStat,Keys,StatNames,Values,RouteLegs):
    Tmp = Values[:,StatNames.index(AccumNames[0])]
    for trait in AccumNames[1:]: Tmp = [x+y for x,y in zip(Tmp, Values[:,StatNames.index(trait)])]
    for key,count,routeLegCount in zip(Keys,Tmp,RouteLegs):
        AccumStat[key] = count/routeLegCount
    return [[random.gauss(AccumStat[key],.05) for key in Keys]]

import random 
def calculatePercentiles(TraitInfo,SortFunc=cmpNull,SortName='Sorted',SortCaption='',Bins=5,Legend=[],Margin=25):
	"""TraitInfo.Stats is a hashtable of lists of statistics per direction set."""
	if not TraitInfo.lastStatNum: TraitInfo.lastStatNum = len(TraitInfo.StatNames)
	TraitInfo.Keys.sort(lambda x,y:SortFunc(TraitInfo.Ratings[x],TraitInfo.Ratings[y]))
	X = []
	Y = []
	Yerrs = []
	i = .5
	Words = []
	Redirs = []
	Forwards = []
	Turns = []
	Rating = []
	LandmarkOccur = []
	Landmarks = ['STRUCT','OBJ','PATH']
	DistDirOccur = []
	DistDirs = ['DIST', 'DIR']
	TraitInfo.LandmarksPerRouteLeg = {}
	TraitInfo.DistDirPerRouteLeg = {}
	numDirs = len(TraitInfo.Keys)
	Incr = numDirs/float(Bins)
	for low,high in zip(range(0,numDirs+1-Incr,Incr),range(Incr,numDirs+1,Incr)):
		if high+Incr > numDirs: high=numDirs
		Values = Numeric.array([TraitInfo.Stats[x] for x in TraitInfo.Keys[low:high]], Numeric.Float)
		X += [ Numeric.array([x+i for x in range(TraitInfo.lastStatNum)])]
		Y += [MLab.mean(Values)[0:TraitInfo.lastStatNum]] # or median
		Yerrs += [MLab.std(Values)]

		Redirs += [[random.gauss(x,.02) for x in Values[:,TraitInfo.StatNames.index('ReDirects')]]]
		Forwards += [[random.gauss(x,.02) for x in Values[:,TraitInfo.StatNames.index('FwdMoves')]]]
		Turns += [[random.gauss(x,.02) for x in Values[:,TraitInfo.StatNames.index('Turns')]]]
		RouteLegs = [max(float(rl),1.0) for rl in Values[:,TraitInfo.StatNames.index('ROUTE_LEG')]]
		DistDirOccur += sumOverStats(DistDirs,TraitInfo.DistDirPerRouteLeg,TraitInfo.Keys[low:high],TraitInfo.StatNames,Values,RouteLegs)
		LandmarkOccur += sumOverStats(Landmarks,TraitInfo.LandmarksPerRouteLeg,TraitInfo.Keys[low:high],TraitInfo.StatNames,Values,RouteLegs)
		#Words += [[random.gauss(x,.02) for x in Values[:,TraitInfo.StatNames.index('Words')]]]
		#i += 1.0/Bins
	Names = TraitInfo.StatNames[0:TraitInfo.lastStatNum]
	Yerrs = [x/math.sqrt(high-low-1) for x in Yerrs]
	LogGraphs.graphErrorbar(X, Y, Names, 'Traits_'+SortName+'_All', Yerrs,Legend,SortCaption)
	graphHighStats(TraitInfo,SortName,SortCaption,Bins,Legend,X,Y,Yerrs)
	LogGraphs.graphScatter(Forwards,Redirs,['Forwards','ReDirects'], 'FwdsRedirs_'+SortName+'_All',Legend,SortCaption)
	LogGraphs.graphScatter(Turns,Redirs,['Turns','ReDirects'], 'TurnsRedirs_'+SortName+'_All',Legend,SortCaption)
	analyzeDistanceVsLandmarks(DistDirOccur,LandmarkOccur,TraitInfo,SortName,SortCaption,Legend)

def analyzeDistanceVsLandmarks(DistanceOccur,LandmarkOccur,TraitInfo,SortName,SortCaption,Legend):
    Dists = []
    for list in DistanceOccur: Dists += list
    Landmarks = []
    for list in LandmarkOccur: Landmarks += list
    bins = 3
    SplitLines = []
    DistCuts = SplitPercentile(Dists,bins)
    maxLndm = max(Landmarks)
    minLndm = min(Landmarks)
    for d in DistCuts: SplitLines.append([d,minLndm,d,maxLndm])
    LandmarkCuts = SplitPercentile(Landmarks,bins)
    maxDist = max(Dists)
    minDist = min(Dists)
    for lm in LandmarkCuts: SplitLines.append([minDist,lm,maxDist,lm])
    numDirs = len(TraitInfo.Keys)
    Incr = numDirs/float(len(DistanceOccur))
    Scaled = []
    for low,high in zip(range(0,numDirs+1-Incr,Incr),range(Incr,numDirs+1,Incr)):
        if high+Incr > numDirs: high=numDirs
        if ScaleFn[SortName]: Scaled.append([ScaleFn[SortName](TraitInfo.Ratings[k]) for k in TraitInfo.Keys[low:high]])
        else: Scaled = [None]
#     print len(DistanceOccur),[len(i) for i in DistanceOccur]
#     print len(LandmarkOccur),[len(i) for i in LandmarkOccur]
#     print len(Scaled), [len(i) for i in Scaled if i], Scaled
    LogGraphs.graphScatter(DistanceOccur,LandmarkOccur,['Distance and Direction Occurences','Landmark Occurences'],
                           'Distance_Landmark_'+SortName+'_All',Legend,SortCaption,Lines=SplitLines,)
                           #Colors=Scaled)
    TraitInfo.Keys.sort(lambda x,y:cmp(TraitInfo.LandmarksPerRouteLeg[x],TraitInfo.LandmarksPerRouteLeg[y]))
    LandmarkSplit = []
    Len=len(TraitInfo.Keys)
    for i in range(1,bins+1):
        LandmarkSplit += [TraitInfo.Keys[(i-1)*Len/bins:i*Len/bins]]
    Split = []
    for list in LandmarkSplit:
        for l,h in zip([minDist]+DistCuts,DistCuts+[maxDist]):
            Split.append([x for x in list if TraitInfo.DistDirPerRouteLeg[x] >= l and TraitInfo.DistDirPerRouteLeg[x] <= h])
    Split.append(TraitInfo.Keys) #All
    StatStr = '\t'.join(['Label','Dist','Lndm','Effc','CEff','Corr','Conf','Ratg','Numb']+[x[0:3] for x in LogAnalyzer.Directors])+'\n'
    Labels =['L-L','M-L','H-L','L-M','M-M','H-M','L-H','M-H','H-H','All']
    Ratgs = []; Dists = []; Lndms = []
    for Label,list in zip(Labels,Split):
        Dist = MLab.mean(Numeric.array([TraitInfo.DistDirPerRouteLeg[x] for x in list], Numeric.Float))
        Lndm = MLab.mean(Numeric.array([TraitInfo.LandmarksPerRouteLeg[x] for x in list], Numeric.Float))
        Effc = MLab.mean(Numeric.array([TraitInfo.Ratings[x][0] for x in list], Numeric.Float))
        Corr = MLab.mean(Numeric.array([TraitInfo.Ratings[x][1] for x in list], Numeric.Float))
        Conf = MLab.mean(Numeric.array([TraitInfo.Ratings[x][2] for x in list], Numeric.Float))
        Ratg = MLab.mean(Numeric.array([TraitInfo.Ratings[x][3] for x in list], Numeric.Float))
        CEff = Effc/Corr
        for stat in [Label,Dist,Lndm,Effc,CEff,Corr,Conf,Ratg,len(list),]:
            StatStr += str(stat)[0:6].ljust(6)+'\t'
        GiverOccur={}
        for g in LogAnalyzer.Directors: GiverOccur[g[0:3]] = 0
        for name in list:
            GiverOccur[name[0:3]] += 1
        for g in LogAnalyzer.Directors: StatStr += str(GiverOccur[g[0:3]])+'\t'
        StatStr += '\n'
        Dists.append(Dist); Ratgs.append(Ratg); Lndms.append(Lndm)
#         if ScaleFn[SortName]: Scaled= [ScaleFn[SortName](TraitInfo.Ratings[k]) for k in list]
#         else: Scaled = range(len(list))
#         LogGraphs.graphScatter([Scaled],
#                                [[TraitInfo.DistDirPerRouteLeg[x] for x in list]],
#                                ['Relative Rating','DistDir'],
#                                'Traits_Rating_DistDir_'+Label+'_'+SortName+'_All',Legend,SortCaption,LogX=1)
#         LogGraphs.graphScatter([Scaled],
#                                [[TraitInfo.LandmarksPerRouteLeg[x] for x in list]],
#                                ['Relative Rating','Landmarks'],
#                                'Traits_Rating_Landmarks_'+Label+'_'+SortName+'_All',Legend,SortCaption,LogX=1)
    LogGraphs.simpleGraph([Dists,Lndms],
                          [Ratgs,Ratgs],
                          'Directions & Distances, Landmarks vs. Relative Rating',
                          'Rating_DistLandm_'+Label+'_'+SortName+'_All',['Distances and Directions','Objects,Appearaces,Paths'],
                          SortCaption,Labels=['Directions & Distances, Landmarks','Relative Rating'])
    print StatStr
    FILE = open(os.path.join('Graphs','DistDirVsLandmarks_'+SortName+'_Results.tsv'),'w')
    FILE.write(StatStr)
    FILE.close()

def graphHighStats(TraitInfo,SortName,SortCaption,Bins,Legend,X,Y,Yerrs):
	XH = []
	YH = []
	YHerrs = []
	for i in range(Bins):
		XH += [[]]
		YH += [[]]
		YHerrs += [[]]
	numDirs = len(TraitInfo.Keys)
	Incr = numDirs/float(Bins)
	NamesH = []
	TurnSpecOcc = Numeric.array([0.0] * numDirs)
	TurnSpecifiers = ['DIST','LOC','UNTIL']
	count = 0
	route_legs = TraitInfo.StatNames.index('ROUTE_LEG')
	for stat in range(TraitInfo.lastStatNum):
		vals = [group[stat] for group in Y]
		if max(vals) > 0.5:
			NamesH += [TraitInfo.StatNames[stat]]
			for i in range(Bins):
				YH[i] += [Y[i][stat]]
				XH[i] += [count+.1+float(i)/Bins]
				YHerrs[i] += [Yerrs[i][stat]]
			count += 1
			#Normalize counts by #ROUTE_LEG
			if TraitInfo.StatNames[stat] in ['ROUTE_LEG','NavConf','DirRating']: Stat = Numeric.array([random.gauss(TraitInfo.Stats[k][stat],.02) for k in TraitInfo.Keys])
			else: Stat = Numeric.array([random.gauss(TraitInfo.Stats[k][stat]/float(max(TraitInfo.Stats[k][route_legs],1)),.02) for k in TraitInfo.Keys])
			if TraitInfo.StatNames[stat] in TurnSpecifiers: TurnSpecOcc += Stat
			#print SortName,TraitInfo.StatNames[stat],stat,numDirs,len(Stat),'\n',Stat
			XS = []; YS = []
			for low,high in zip(range(0,numDirs+1-Incr,Incr),range(Incr,numDirs+1,Incr)):
				if ScaleFn[SortName]: Scaled= [ScaleFn[SortName](TraitInfo.Ratings[k]) for k in TraitInfo.Keys[low:high]]
				else: Scaled = range(low,high)
				YS += [[Stat[x] for x in range(low,high)]]
				XS += [Scaled]
			LogGraphs.graphScatter(XS,YS,['Relative Rating',TraitInfo.StatNames[stat]],
									'Rating_'+TraitInfo.StatNames[stat]+'_'+SortName+'_All',Legend,SortCaption,RunningAvg=1)
	if ScaleFn[SortName]: Scaled= [ScaleFn[SortName](TraitInfo.Ratings[k]) for k in TraitInfo.Keys]
	else: Scaled = range(numDirs)
	LogGraphs.graphScatter([Scaled],[TurnSpecOcc],['Relative Rating','TurnSpec'],
							'Traits_Rating_TurnSpec_'+SortName+'_All',Legend,SortCaption,LogX=1,RunningAvg=1)
	LogGraphs.graphErrorbar(XH, YH, NamesH, 'Traits_High_'+SortName+'_All', YHerrs,Legend,SortCaption)

def hueristicTags(Ratings,StatMatrix):
	DirTraits = {}
	DirTraitPatterns={}
	for Name in DirTraitNames:
		Val = locals()[Name]
		Val.sort()
		#print Name,'=',Val
		Patt = re.compile('(^|\W)(?P<'+Name+'>'+LogAnalyzer.constructSetOrRegexp(Val)+')(?=(\W|$))',re.I)
		DirTraitPatterns[Name] = Patt
	parseDirections(DirTraitPatterns,StatMatrix['DirectionTexts'],Ratings,DirTraits)
	return DirTraits

def getDirTraits(hueristic):
	indices = cPickle.load(open('indices.pyc'))
	s2 = cPickle.load(open('s2.pyc'))
	TraitInfo = DirTraitInfo()
	TraitInfo.Ratings = s2['PerDirection'][indices['All_Followers_Cum'][0]]
	TraitInfo.Keys=TraitInfo.Ratings.keys()
	if hueristic: TraitInfo.Stats = hueristicTags(TraitInfo.Ratings,StatMatrix)
	else: TraitInfo.Stats,DirTraitNames = Tagger.correlateRatingsTags(TraitInfo.Ratings)
	#for k,v in TraitInfo.Stats.items(): print k,v
	TraitInfo.lastStatNum = len(DirTraitNames)+5
	for item in TraitInfo.Stats.values():
		if item[0] and 'Words' in DirTraitNames:
			item[DirTraitNames.index('Words')] = math.log(item[DirTraitNames.index('Words')]+1) #Log normalize the # of words.
	TraitInfo.StatNames = ['NavConf','DirRating','ReDirects','FwdMoves','Turns']+DirTraitNames
	TraitInfo.Keys.sort()
	cPickle.dump(TraitInfo,open('TraitInfo.pyc','w'))
	return TraitInfo

def graphDirTraits(TraitInfo):
	TraitInfo.Keys.sort()
	calculatePercentiles(TraitInfo, cmpNull, 'Alpha', 'Sorted by Giver', 6, LogAnalyzer.Directors)
	for SortName,SortCaption,SortFunc in zip(['Lexical','Sum','DiscSum','Efficiency'],
						['Sorted by Direction Rating, then Navigation Confidence, then Efficiency',
						 'Sorted by the sum of the Direction Rating and Navigation Confidence',
						 'Sorted by the sum of the Direction Rating and Navigation Confidence, discounted by the efficiency',
						 'Sorted by Efficiency'
						 ],
						[cmpRatingsLex,cmpRatingsSum,cmpRatingsDiscSum,cmpEfficiency]):
		TraitInfo.Keys.sort()
		calculatePercentiles(TraitInfo,SortFunc,SortName,SortCaption,5,[x+' Quintile' for x in ['1st','2nd','3rd','4th','5th']])
	#DirTraitArray = Numeric.array(DirTraits.values())
	#EvaluatedDirs = Numeric.compress(Numeric.not_equal(DirTraitArray[:,0],None),DirTraitArray,0)

hueristic=0
if __name__ == '__main__':
    TraitInfo = getDirTraits(hueristic)
    #TraitInfo = cPickle.load(open('TraitInfo.pyc'))
    graphDirTraits(TraitInfo)
