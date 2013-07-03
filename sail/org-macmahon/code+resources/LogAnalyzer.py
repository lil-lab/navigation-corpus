#!/usr/bin/python
import re, string, os, MLab, Numeric
import LogPatternLib
from Parser import parseLine, parseFile, debug
from Utility import *
from SubjectLogs.SubjectGroups import *

def constructSetOrRegexp(List): return '('+'|'.join(List)+')'

Prefixes = ('A','D','N','E')
def parseLogs( StatTable = {} ):
    """StatTable is the accumlation of summarized statistics over many direction/route/evaluation cycles.
    results holds the raw results, pre-processing, with lists of all direction/route/evaluation cycles."""
    
    Fields = ['A_Turns','A_FwdMoves','A_Moves','CorrTgt','IncrTgt', 'A_Efficiency', 'A_CorrTgt', 'A_NavConf', 'A_DirRtng', 'A_TgtFound',
              'RtngConfCorr', 'RtngCorrCorr', 'ConfCorrCorr', 'RtngEffcCorr', 'ConfEffcCorr', 'FollowerNumber', 'TtlTime','DirectionIDs']
    Stats = ['Turns','FwdMoves','Moves', 'Efficiency', 'NavConf', 'DirRtng', 'TgtFound']
    results = {}
    for GroupName in SubjGroups: results[GroupName] = {}
    printSummaryHeader(Fields)
    for Follower in All_Subjects:
        Logs = [file for file in os.listdir('SubjectLogs')
                if re.match(Follower+'_DirectionAll0_\d+\.out$',file)]
        if Logs: results['Current'] = processLogfiles(Logs,Fields,Stats,Follower,'All',StatTable)
        #print 'Adding', Follower,' to stats for groups: ',
        for GroupName, Group in SubjGroups.items():
            if Follower in Group:
                appendResults(results['Current'],Fields+Stats,results[GroupName])
                #print GroupName,
        #print
    #for k,v in results['Current'].items(): print '\t',k,':',v
    for Env in ['L', 'Jelly', 'Grid']:
        for Director in Directors:
            Logs = [file for file in os.listdir('SubjectLogs')
                    if re.match('%s_Direction%s[01]_\d+\.out$'%(Director,Env),file)]
            if Logs: results['Current'] = processLogfiles(Logs,Fields,Stats,Director,Env,StatTable)
            for GroupName, Group in SubjGroups.items():
                if Follower in Group: appendResults(results['Current'],Fields+Stats,results[GroupName])
    for GroupName, Group in SubjGroups.items():
        print '\n',GroupName
        results[GroupName]['FollowerID'] = GroupName
        #for k,v in results[GroupName].items(): print '\t',k,':',v
        results[GroupName]['DirectionIDs'] = [d for d in results[GroupName]
                                              if isinstance(d,str) and d.endswith('.txt')]
        processLogfiles(Logs,Fields,Stats,GroupName,'All',StatTable,0,results[GroupName])
    print
    printSummaryHeader(Fields)
    #printStatTable(StatTable)

def parseLogsPer( StatTable = {}, graph = 0 ):
    import LogGraphs
    Fields = ['Efficiency', 'NavConf', 'DirRtng', 'TgtFound']
    StatTable['DirectionTexts']={}
    CumFields = ['A_Turns','A_FwdMoves','A_Moves','CorrTgt','IncrTgt', 'A_Efficiency', 'A_CorrPct', 'A_NavConf', 'A_DirRtng', 'A_TgtFound',
              'RtngConfCorr', 'RtngCorrCorr', 'ConfCorrCorr', 'RtngEffcCorr', 'ConfEffcCorr', 'FollowerNumber', 'TtlTime','DirectionIDs']
    results = {}
    indices = {}
    i = 0
    for GroupName in SubjGroups: results[GroupName] = {}
    print 'A_ =  Average, D_ = stddev, N_ = avg of tgt found, E_ =  stddev non-blank' 
    for Follower in All_Subjects:
        Logs = filter(lambda x: re.match(Follower+'_Direction(All|Grid|Jelly|L).*[01]_\d+\.out$',x),os.listdir('SubjectLogs'))
        if Logs:
            results['Current'] = parseLogfiles(Logs)
            printSummaryHeader(['%s_%s'%(prefix,field) for prefix in Prefixes for field in Fields])
            #print results['Current']
            for Director in Directors:
                if Follower not in Directors or Follower is Director:
                    DirectionIDs = [d for d in results['Current']
                                    if isinstance(d,str) and d.startswith(Director) and d.endswith('.txt')]
                    if not DirectionIDs: continue
                    DirectorStats = [Director +'_'+ field for field in Fields]
                    DirectorFields = ['_'.join((prefix,Director,field)) for prefix in Prefixes for field in Fields]
                    analyzeStats(results['Current'],DirectorFields,DirectorStats,Follower+'_'+Director,'_Per',StatTable,Director+'_TgtFound')
                    if graph: LogGraphs.graphStats(results['Current'],Follower+'_'+Director,'Per',Director+'_DirRtng',Director+'_NavConf')
                    #if Follower is Director: StatTable['DirectionTexts'].update(results['DirectionTexts'])
                    #print 'Adding', Follower,' to stats for groups:',
                    for GroupName, Group in SubjGroups.items():
                        if Follower in Group or Director in Group:
                            appendResults(results['Current'], Fields+CumFields+DirectorStats+DirectorFields+DirectionIDs, results[GroupName])
                            #print GroupName,
            for GroupName, Group in SubjGroups.items():
                if Follower in Group:
                    indices.setdefault(GroupName,[])
                    indices[GroupName].append(i)
            if Follower not in Directors:
                indices[Follower] = [i]
                i += 1
                calculatePerDirection(results['Current'],StatTable)
                print i,len(StatTable['PerDirection'])
    del results['Current']
    Groups = SubjGroups.keys()
    Groups.sort()
    for GroupName in Groups:
        results[GroupName]['FollowerID'] = GroupName
        StatTable['/FollowerID'].append(GroupName)
        indices[GroupName+'_Cum'] = [i]
        i += 1
        DirIDs = {}
        print '\n',GroupName, ' '.join(SubjGroups[GroupName])
        printSummaryHeader(['%s_%s'%(prefix,field) for prefix in Prefixes for field in Fields])
        #for k,v in results[GroupName].items(): print '\t',k,':',v
        for Director in Directors:
            DirectorStats = [Director + '_' + field for field in Fields]
            DirectorFields = ['_'.join((prefix,Director,field)) for prefix in Prefixes for field in Fields]
            analyzeStats(results[GroupName], DirectorFields, DirectorStats, GroupName+'_'+Director, '_Per', StatTable, Director+'_TgtFound', Director[:3])
            if graph: LogGraphs.graphStats(results[GroupName],GroupName+'_'+Director,'Per',Director+'_DirRtng',Director+'_NavConf')
            for d in results[GroupName]:
                if isinstance(d,str) and d.endswith('.txt'): DirIDs[d]=1
        Stats = ['_'.join((prefix,field)) for prefix in Prefixes for field in Fields]
        analyzeStats(results[GroupName], Stats, Fields, GroupName, '_Per', StatTable, 'TgtFound', 'All')

        results[GroupName]['DirectionIDs'] = DirIDs.keys()
        results[GroupName]['DirectionIDs'].sort()
        calculatePerDirection(results[GroupName],StatTable)
        #print GroupName, i,len(StatTable['PerDirection'])
        #print 'Got',len(DirIDs.keys()), 'Directions', len( StatTable['PerDirection'][len(StatTable['PerDirection'])-1])
        del results[GroupName]
    #StatTable['/FollowerID'] = Followers+SubjGroups.keys()
    #StatTable['/Test Name'] = ['Per']
    #printStatTable(StatTable)
    #print indices
    #for k in indices: print k, len(StatTable['PerDirection'][indices[k][0]])
    if graph:
        LogGraphs.graphPerStats(StatTable, 'All', Range=None, ErrorBars=1)
        LogGraphs.graphPerStats(StatTable, 'Followers', indices['Fol_All'], 1)
        LogGraphs.graphPerStats(StatTable, 'Lab_Low_Followers', indices['Lab_Followers']+indices['Low_Eff_Followers'], 1)
        LogGraphs.graphPerStats(StatTable, 'Sex', indices['Fol_1_Men_Cum']+indices['Fol_1_Wmn_Cum']+indices['Fol_2_Men_Cum']+indices['Fol_2_Wmn_Cum'])
        LogGraphs.graphPerStats(StatTable, 'Subj_Low_Lab', indices['Fol_All_Cum']+indices['Low_Eff_Followers_Cum']+indices['Lab_Followers_Cum'])
        LogGraphs.graphPerStats(StatTable, 'Lang', indices['Fol_Frgn_Lang_Cum']+indices['Fol_Eng_Prim_Cum'])
    return indices

def processLogfiles(Logs,Fields,Stats,FollowerID,TestName,StatTable,parse=1,results={}):
	if parse: results = parseLogfiles(Logs)
	analyzeStats(results,Fields,Stats,FollowerID,TestName,StatTable,'TgtFound')
    # import LogGraphs
    # LogGraphs.graphStats(results,FollowerID,TestName,'NavConf','DirRtng')
	if parse: calculatePerDirection(results,StatTable)
	return results

def parseLogfiles(Logs):
	results = {}
	results['Left'] = results['Right'] = results['Forward'] = results['ReDirct'] = 0
	results['TtlTime'] = 0
	LogPatternLib.debug = debug
	if debug: print '\nParsing ',Logs
	for Log in Logs:
		results['LogName'] = Log.split('.')[0] # chop suffix
		parseFile(LogPatternLib.patterns, os.path.join('SubjectLogs',Log), results)
		if results.get('Time'): results['TtlTime'] += results['Time'] 
	return results

def analyzeStats(results, Fields, Stats, FollowerID, TestName, StatTable, Filter, Group=''):
	results['FollowerID'] = FollowerID
	results['/Test Name'] = TestName
	calculateStats(results, Stats, Filter)
	printSummary(results, Fields, StatTable, Group)
	appendResults(results, Fields+Stats, StatTable)

def calculateStats(results,Fields,Filter):
	""" Calculates S_ (Sum), A_ (Avg/mean), and D_ (std Deviation) for each field"""
	try:
		for field in Fields:
			#print field,field,results[field]
			parts = field.split('_')
			if len(parts) > 1: prefix = parts[0]+'_'
			else: prefix = ''
			if len(results[field]) > 1:
				results['S_'+field] = MLab.sum(results[field])
				results['A_'+field] = MLab.mean(results[field])
				results['D_'+field] = MLab.std(results[field])/(MLab.sqrt(len(results[field]))-1)
			else:
				results['S_'+field] = results[field][0]
				results['A_'+field] = results[field][0]
				results['D_'+field] = 0.0
			Filtered = MLab.nonzero(results[prefix+'TgtFound'][:len(results[field])-1])
			if len(Filtered) > 1:
				TgtFoundResults = MLab.choose(Filtered,results[field])
				results['N_'+field] = MLab.mean(TgtFoundResults)
				results['E_'+field] = MLab.std(TgtFoundResults)/(MLab.sqrt(len(TgtFoundResults))-1)
			else:
				results['N_'+field] = MLab.choose(Filtered,results[field])[0]
				results['E_'+field]= 0.0
		results['RtngConfCorr'] = calculateCorrelation(results['NavConf'],results['DirRtng'])
		results['RtngCorrCorr'] = calculateCorrelation(results['NavConf'],results['TgtFound'])
		results['ConfCorrCorr'] = calculateCorrelation(results['DirRtng'],results['TgtFound'])
		results['RtngEffcCorr'] = calculateCorrelation(results['NavConf'],results['Efficiency'])
		results['ConfEffcCorr'] = calculateCorrelation(results['DirRtng'],results['Efficiency'])
		results['A_CorrTgt'] = results['CorrTgt'] / float(results['IncrTgt']+results['CorrTgt'])
	except IndexError: pass #print 'ERROR: Missing keys when calculating stats for', field, Filter
	except KeyError: pass #print 'ERROR: Missing keys when calculating stats for', field, Filter
	except ValueError: print 'ERROR: Invalid entry in choice array',field,Filtered,len(results[field]),'\n',results[field]

def calculateCorrelation(A,B):
    if len(A) > 2:
        try:
            return pylab.corrcoef(pylab.swapaxes(Numeric.array([A,B]),0,1))[0,1]
        except OverflowError: return 0.0
        except TypeError: pass
    return 0.0

PerDirectionFields = ('Efficiency','TgtFound','NavConf','DirRtng','ReDirect','FwdMove','RTurns','LTurns','TimesFollowed')
def calculatePerDirection(results, StatTable):
##	print 'in calculatePerDirection'
	StatTable.setdefault('/FollowerID',[]).append(results['FollowerID'])
	StatTable.setdefault('/Test Name',[]).append(results['/Test Name'])
	StatTable.setdefault('DirectionIDs',[]).append(results['DirectionIDs'].sort())
	StatTable.setdefault('PerDirection',[]).append({})
	PerDirection = StatTable['PerDirection'][len(StatTable['PerDirection'])-1]
	for dir in results['DirectionIDs']:
#		print '.',; 
		v = results[dir];
		PerDirection[dir] = [v.get(x) for x in PerDirectionFields[:-1]]
		TimesFollowed =  v.get(PerDirectionFields[-1])
		if isinstance(TimesFollowed,int):
		    if TimesFollowed > 1: PerDirection[dir] = [float(x) / TimesFollowed for x in PerDirection[dir]]
		    PerDirection[dir].append(TimesFollowed)
		elif isinstance(TimesFollowed,list):
		    PerDirection[dir] = [MLab.mean(x) for x in PerDirection[dir]]
		#    PerDirection[dir+'_Std'] = [MLab.std(x) for x in PerDirection[dir]]
		    PerDirection[dir].append(MLab.sum(TimesFollowed))
		#except TypeError:
		#else: print 'TypeError',dir,v, '\n',PerDirection[dir]
##		print 'calculatePerDirection',dir,':',PerDirection[dir]
##	print '\ncalculated per dir stats for # dirs', len(results['DirectionIDs']), len(PerDirection.keys()), len( StatTable['PerDirection'][len(StatTable['PerDirection'])-1]),

def printPerDirection(StatTable):
	print ' '.join(PerDirectionFields)
	for follower,set in zip(StatTable['/FollowerID'],StatTable['PerDirection']):
		print follower
		dirs = set.items()
		dirs.sort()
		for k,v in dirs: print k,v
		print

def makePerDirectionCSV(StatTable,Group):
    GroupStats = StatTable['PerDirection'][StatTable['/FollowerID'].index(Group)]
    dirs = GroupStats.keys()
    dirs.sort()
    for i,Stat in enumerate(PerDirectionFields):
        rowFile = open(os.path.join('MarcoLogs','-'.join(('Follower','Results',Group,Stat,'Row.csv'))), 'w')
        rowFile.write("%s-%s," % (Group,Stat))
        colFile = open(os.path.join('MarcoLogs','-'.join(('Follower','Results',Group,Stat,'Col.txt'))), 'w')
        colFile.write("Stat\t%s-%s\n" % (Group,Stat))
        for riSet in dirs:
            result = GroupStats[riSet][i]
            colFile.write("%s\t%1.2g\n" % (riSet,result))
            rowFile.write("%1.2g," % (result))
        rowFile.close()
        colFile.close()

def printStatTable(StatTable):
	print '========================================='
	orderedStats =  StatTable.items()
	orderedStats.sort()
	DirNames = []
	for name,list in orderedStats:
		if name.endswith('.txt'):
			DirNames.append(name)
			continue
		if not isinstance(name,str):
		    print 'Name isn\'t string in printStatTable', name
		    continue
		try:
		   print name[0:16].rjust(16),'#',len(list),'#',
		   for i in list[0:60]: print str(i)[0:6].rjust(6),'\t',
		except: print 'List isn\'t list in printStatTable', list
		print
	for name in DirNames:
		print name,':'
		for StatName, Vals in StatTable[name].items(): print '\t',StatName,':',Vals

def printSummaryHeader(Fields):
	print 'SubjectID','\t', 
	#print 'TstNme','\t', 
	for field in Fields:
		print field[0:6].rjust(6), "\t",
	print
	print ' '*len('SubjectID'),
	for field in Fields:
		print field[6:12].rjust(6), "\t",
	print

def printSummary(results, Fields, StatTable, Group):
	for field in Fields:
		if field not in results: return
	print Group[:3],results['FollowerID'][:8].rjust(8),'\t',
	#print results['/Test Name'].rjust(6),'\t',
	for field in Fields:
		try:
			print str(results[field])[0:6].rjust(6),'\t',
		except: print '   N/A\t',
	print
	#except KeyError: print 'ERROR: Missing keys when printing stats for', field

def appendResults(results,Fields,StatTable):
	for field in Fields:
		if field not in results: continue
		#results.setdefault(field,'N/A')
		if isinstance(field,str) and field.endswith('.txt'):
##			sumPerDirection(results,StatTable,field)
			StatTable.setdefault(field,{})
			for stat in results[field]:
				StatTable[field].setdefault(stat,[])
				if isinstance(results[field][stat],list):
					StatTable[field][stat]+=results[field][stat]
				else: StatTable[field][stat].append(results[field][stat])
		elif isinstance(results[field],list):
			StatTable.setdefault(field,[])
			StatTable[field] += results[field]
		elif isinstance(field,str) and field.endswith('Tgt'):
			StatTable.setdefault(field,0)
			StatTable[field] += results[field]
		else:
			StatTable.setdefault(field,[]).append(results[field])
		#except: print

def sumPerDirection(curr_results,sum_results,dir):
    sum_results.setdefault(dir,{})
    for dirStat in curr_results[dir]:
        sum_results[dir].setdefault(dirStat,0)
        sum_results[dir][dirStat] += curr_results[dir][dirStat]

def printStatTable(StatTable):
	print '========================================='
	orderedStats =  StatTable.items()
	orderedStats.sort()
	DirNames = []
	for name,list in orderedStats:
		if name.endswith('.txt'):
			DirNames.append(name)
			continue
		if not isinstance(name,str):
		    print 'Name isn\'t string in printStatTable', name
		    continue
		try:
		   print name[0:16].rjust(16),'#',len(list),'#',
		   for i in list[0:60]: print str(i)[0:6].rjust(6),'\t',
		except: print 'List isn\'t list in printStatTable', list
		print
	for name in DirNames:
		print name,':'
		for StatName, Vals in StatTable[name].items(): print '\t',StatName,':',Vals

import cPickle
def doAll( ):
	global s1,s2,indices
	print
	parseLogs( s1 )
	cPickle.dump(s1,open('s1.pyc','w'))
	del s1
	indices = parseLogsPer( s2 )
	cPickle.dump(s2,open('s2.pyc','w'))
	cPickle.dump(indices,open('indices.pyc','w'))
	del s2
	return indices

if __name__ == '__main__':
	s1 = {}
	s2  = {}
	indices = doAll()

#Logs = [file for file in os.listdir('SubjectLogs') if re.match('.*\d_\d.out',file) and file.split('_')[0] in All_Subjects]
#results = parseLogfiles(Logs)
