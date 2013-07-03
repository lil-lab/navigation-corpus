"""
LogPatternLib is a collection of patterns which extract named fields from a log line
and an associated function, to do any additional processing.
"""

import re, string, os, os.path
from Utility import nextFileSeq
patterns={}

beginHeaderPatt=re.compile('/-+')
def beginHeader(results):
    if results.has_key('Header') and results['Header'] == 1: print "ERROR:  Redundant header start."
    results['Header'] = 1
    results['DirectionID'] = None
    results['StartPos'] = None
    results['EndPos'] = None
    results['Competency'] = None
    results['Phase'] = ''
    directory = os.path.join('SubjectLogs',results['LogName'])
    if not os.path.exists(directory): os.mkdir(directory)
    results['Directory'] = directory
patterns[beginHeaderPatt] = beginHeader

endHeaderPatt=re.compile('[^/]-+')
def endHeader(results):
    if results.has_key('Header') and results['Header'] == 0: print "ERROR:  Redundant header end."
    results['Header'] = 0
patterns[endHeaderPatt] = endHeader

dateHeaderPatt = re.compile('\|Date:(?P<Date>\S+) Time:(?P<StartTime>\S+)')
def dateHeader(results):
    pass
patterns[dateHeaderPatt] = dateHeader

versionHeaderPatt = re.compile('\|\tVersion: (?P<Version>.+)')
def versionHeader(results):
    pass
patterns[versionHeaderPatt] = versionHeader

layoutHeaderPatt = re.compile('\|\tLayout: (?P<Layout>.+)')
def layoutHeader(results):
    pass
patterns[layoutHeaderPatt] = layoutHeader

modeHeaderPatt = re.compile('\|\tMode: (?P<Mode>.+)')
def modeHeader(results):
    pass
patterns[modeHeaderPatt] = modeHeader

goodTrialsHeaderPatt = re.compile('\|\tRequired Good Trials: (?P<GoodTrials>.+)')
def goodTrialsHeader(results):
    pass
patterns[goodTrialsHeaderPatt] = goodTrialsHeader

hotSpotsHeaderPatt = re.compile('\|\t(?P<HS_Num>\d+)\t+(?P<HS_Xpos>\d+)\t+(?P<HS_Ypos>\d+)')
def hotSpotsHeader(results):
    results['HotSpot'+results['HS_Num']] = (results['HS_Xpos'], results['HS_Ypos'])
patterns[hotSpotsHeaderPatt] = hotSpotsHeader

mapHeaderPatt = re.compile('\$(?P<Mapline>.*)')
def mapHeader(results):
    if not results.has_key('Map'): results['Map'] = ''
    results['Map'] += results['Mapline']
patterns[mapHeaderPatt] = mapHeader

def resetRouteCounters(results):
    if debug:
        print results['LogName'], results['DirectionID']
    results['RouteTurns'] = results['Left'] + results['Right']
    results.setdefault('Turns',[]).append(results['RouteTurns'])
    results['RouteMoves'] = results['RouteTurns'] + results['Forward']
    results.setdefault('Moves',[]).append(results['RouteMoves'])
    results['RouteFwdMoves'] = results['Forward']
    results.setdefault('FwdMoves',[]).append(results['RouteFwdMoves'])
    results.setdefault('ReDirects',[]).append(results['ReDirct'])

    results['Left'] = results['Right'] = results['Forward'] = results['ReDirct'] = 0
    if debug:
        print results['Turns'], ', ', results['FwdMoves'],', ',results['Moves'],
        print results['RouteTurns'], ', ', results['RouteFwdMoves'],', ',results['RouteMoves'],

def openPhaseFiles(Phase,results):
    for fileprefix in ('MotTrace','ActTrace','TimeTrace'):
        filename = os.path.join(results['Directory'], fileprefix+'-'+Phase)
        if fileprefix in results:
            results[fileprefix].close()
            if (('TurnAround' in results[fileprefix].name and results['Mode'] != 'TurnAround')
                or ('HotspotQuiz' in results[fileprefix].name and results['DirectionID'])):
                os.rename(results[fileprefix].name, filename)
        if results['Mode'] == 'TurnAround':
            results['DirectionID'] = ''
        results[fileprefix] = open(filename, 'a+')
    results['Phase'] = Phase

#actionBody is 'Mode;\t? Position triple;\t action;\t Time'
actionBodyPatt = re.compile('(?P<Mode>(?:>\w;\t| |> )?)(?P<Position>\d+,\d+,\d+); \t(?P<Action>[^;]+);?\t(?P<time>[^;]+);?')
Modes = {
    '>E;\t' : 'Explore',
    '> ' : 'Explore',
    '>W;\t' : 'BoundedWander',
    '>T;\t' : 'TurnAround',
    '>Q;\t' : 'HotspotQuiz',
    '>F;\t' : 'EfficiencyTest',
    }
def actionBody(results):
    if results['Mode']:
        results['Mode'] = Modes[results['Mode']]
        if ('Phase' not in results
            or (results['DirectionID']
                and results['Mode'] not in ('HotspotQuiz','EfficiencyTest',))
            or (not results['DirectionID']
                and results['Mode'] != results['Phase'].split('_')[0])):
            Filename = 'MotTrace-'+results['Mode']
            Phase = '%s_%d.txt' % (results['Mode'], nextFileSeq(results['Directory'],Filename))
            openPhaseFiles(Phase,results)
    else: results['Mode'] = 'Follow'
    Action = results['Action']
    time = results['time']
    results.setdefault(Action,0)
    results[Action] += 1
    
    results.setdefault('Time',0.0)
    time = float(time)
    results['DiffTime'] = time - results['Time']
    results['Time'] = time

    if 'LastPose' in results and Action == 'ContMv':
        x,y,theta = [int(x) for x in results['Position'].split(',')]
        if ((x,y) == results['LastPose'][:2]):
            ContAction = 'Forward'
        elif (theta+120)%360 > results['LastPose'][3]:
            ContAction = 'Right'
        else:
            ContAction = 'Left'
        results.setdefault(ContAction,0)
        results[ContAction] += 1
        results['LastPose'] = x,y,theta

    if Action == 'JumpNxt':
        results['RouteTime'] = time
    else:
        try: results['RouteTime']
        except KeyError: results['RouteTime'] = time
        results['WithinDirTime'] = time - results['RouteTime']
        for file,stat in zip(('MotTrace','ActTrace','TimeTrace'),
                             ('Position','Action','WithinDirTime')):
            results[file].write('%s%s' % (results[stat], os.linesep))
    
    giver = results.setdefault('GiverID','UNK')
    #if 'JumpNxt' not in results or (results['JumpNxt'] % 10 == 0): print results['Mode']
    if results['Mode'] == 'Follow' or results['Mode'] == 'HotspotQuiz':
        if Action == 'IncrTgt':
            results.setdefault('Efficiency',[]).append(0.0)
            results.setdefault('TgtFound',[]).append(0)
            results.setdefault(giver+'_Efficiency',[]).append(0.0)
            results.setdefault(giver+'_TgtFound',[]).append(0)
            results[results['DirectionID']].setdefault('Efficiency',0.0)
            results[results['DirectionID']].setdefault('TgtFound',0)
            output = open(os.path.join(results['Directory'], 'Efficiency-'+results['DirectionID']), 'w')
            output.write('%s%s'%('0.0', os.linesep))
            output.close()
            output = open(os.path.join(results['Directory'], 'TgtFound-'+results['DirectionID']), 'w')
            output.write('%s%s'%('0',os.linesep))
            output.close()
            #print results['TgtFound'], 'TgtFound'
        elif Action == 'CorrTgt':
            results.setdefault('TgtFound',[]).append(1)
            results.setdefault(giver+'_TgtFound',[]).append(1)
            results[results['DirectionID']].setdefault('TgtFound',0)
            results[results['DirectionID']]['TgtFound'] += 1
            output = open(os.path.join(results['Directory'], 'TgtFound-'+results['DirectionID']), 'w')
            output.write('%s%s'%('1',os.linesep))
            output.close()
            #print results['TgtFound'], 'TgtFound'
    if Action == 'EffTest': resetRouteCounters(results)
patterns[actionBodyPatt] = actionBody

directionTimePatt = re.compile('(DT? Directions|> Following Directions [^;]+;) at time: (?P<DirectionTime>.+)')
def directionTime(results):
    resetRouteCounters(results)
patterns[directionTimePatt] = directionTime

# Embedded Regexp splits up DirectionID into parts
directionIDPatt = re.compile('DF: (?P<DirectionID>(?P<GiverID>\w+)_(?P<Env>\w+)\d_(?P<StartPos>\d+)_(?P<EndPos>\d+)_(?P<ExptID>\w+)_(?P<DirectNum>\d+).txt)')
def directionID(results):
    results['DirectionText'] = ''
    results.setdefault(results['DirectionID'],{})
    results.setdefault('DirectionIDs',[]).append(results['DirectionID'])
    openPhaseFiles(results['DirectionID'],results)
patterns[directionIDPatt] = directionID

directionTextPatt = re.compile('D: (?P<DirectionLine>.*)')
def directionText(results):
    if not results['DirectionLine']:
        results['DirectionText'] = ''
        results.setdefault('BlankDirs',0)
        results['BlankDirs'] += 1
        results['DirectionLength'] = 0
        return
    results.setdefault('DirectionText','')
    results['DirectionText'] += results['DirectionLine']
    results.setdefault('DirectionLength',0)
    results['DirectionLength'] = results['DirectionLine'].count(' ')
patterns[directionTextPatt] = directionText

directionRatingsPatt = re.compile('# Direction confidence (?P<DirectionMode>following|giving) (?P<RatedDirID>[^#]+)# Goodness: (?P<DirectionGoodness>\d) Confidence: (?P<DirectionConfidence>\d)')
def directionRatings(results):
    if results['DirectionID'] != results['RatedDirID']:
        print 'ERROR: DirectionID for Ratings (', results['RatedDirID'], ') '
        print 'does not match directions being followed (', results.get('DirectionID'), ').'
    results.setdefault('DirectionTexts',{})[results['DirectionID']] = results['DirectionText']
    results[results['DirectionID']].setdefault('TimesFollowed',0)
    results[results['DirectionID']]['TimesFollowed'] += 1
    
    for abbrev,stat in zip(['NavConf','DirRtng','DirLngt','ReDirect','FwdMove','RTurns','LTurns'],
                           ['DirectionConfidence','DirectionGoodness','DirectionLength','ReDirct','Forward','Right','Left']):
        statistic = int(results[stat])
        results.setdefault(abbrev,[]).append(statistic)
        results.setdefault(results['GiverID']+'_'+abbrev,[]).append(statistic)
        results[results['DirectionID']].setdefault(abbrev,0)
        results[results['DirectionID']][abbrev] += statistic
    
    for abbrev,stat in zip(['NavConf','DirRtng'],
                           ['DirectionConfidence','DirectionGoodness']):
        output = open(os.path.join(results['Directory'], abbrev+'-'+results['DirectionID']), 'w')
        output.write('%s%s'%(results[stat],os.linesep))
        output.close()
patterns[directionRatingsPatt] = directionRatings

directionEfficiencyPatt = re.compile('>E;\t(?P<EffStartPos>\d+) to (?P<EffEndPos>\d+);\t(?P<RecMoves>\d+) / (?P<MinMoves>\d+) = (?P<RecEfficiency>[\d.]+);\t(?:;\t )?Successes (?P<Successes>\d+);(?:\tOK (?P<OK>\d+);\tFailures (?P<Failures>\d+);)?')
def directionEfficiency(results):
    if results.get('StartPos'):
        if results['StartPos'] != results['EffStartPos'] or results['EndPos'] != results['EffEndPos']:
            print 'ERROR: Efficiency start - end (', results['EffStartPos'],' - ', results['EffEndPos'],
            print ') does not match directions being followed (', results['StartPos'], ' - ', results.get('EndPos'), ').'
        if int(results['Forward']) != int(results['RecMoves']):
            print 'ERROR: Forward moves from efficiency (', results['RecMoves'], '),'
            print ' does not match forward move count (', results['Forward'], ').'
    results.setdefault('Efficiency',[]).append(float(results['RecEfficiency']))
    results.setdefault(results['GiverID']+'_Efficiency',[]).append(float(results['RecEfficiency']))
    results.setdefault(results['DirectionID'],{}).setdefault('Efficiency',0)
    results.setdefault(results['DirectionID'],{})['Efficiency'] += float(results['RecEfficiency'])
    output = open(os.path.join(results['Directory'], 'Efficiency-'+results['DirectionID']), 'w')
    output.write('%s%s'%(results['RecEfficiency'],os.linesep))
    output.close()
patterns[directionEfficiencyPatt] = directionEfficiency

blankLinePatt = re.compile('^\s*$')
def blankLine(results):
    pass
patterns[blankLinePatt] = blankLine

hotSpotSetupHeaderPatt = re.compile('\|\tSpot')
def hotSpotSetupHeader(results):
    pass
patterns[hotSpotSetupHeaderPatt] = hotSpotSetupHeader

formatHeaderPatt = re.compile('\| \(X,Y,Angle\)\t')
def formatHeader(results):
    if debug: print 'Parsed: Format Header'
    return results
patterns[formatHeaderPatt] = formatHeader

competencyPatt = re.compile('### (?P<Competency>(Achieved|Failed)) competency')
def competency(results):
    pass
patterns[competencyPatt] = competency

dirSeriesPatt = re.compile('### Direction Series: (?P<DirectionSeries>\[.*\])')
def dirSeries(results):
    pass
patterns[dirSeriesPatt] = dirSeries

dirFollowerNumPatt = re.compile('# Direction Follower number (?P<FollowerNumber>\d+)')
def dirFollowerNum(results):
    pass
patterns[dirFollowerNumPatt] = dirFollowerNum
