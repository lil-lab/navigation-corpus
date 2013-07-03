#!/usr/bin/env python
Percepts = ['PomdpSimViewVector', 'PomdpSimSmallScaleStar']
CrossValidations = ['Directors', 'Maps', 'MapNext', 'MapPrev', 'Positions', 'Random']
from SubjectLogs.SubjectGroups import *

__doc__ ="""Run the follower through the instruction corpus.

Usage: Harness.py [options]

Options:
    -h / --help
        Print this message and exit.

    -v / --verbose
        Be more verbose.

    -e mapname/ --env=mapname
        Run on the environment with given mapname.
        mapname must be one of %(Maps)s.

    -g / --gui
        Show the Graphical User Interface.

    -r / --route
        Follow this route, of form GIVER_ENV_START_DEST.

    -i / --instruction
        Follow this instruction text.

    -s / --start
        Specify start position.
        Must be one of %(Positions)s.

     -t / --target
        Specify target position.
        Must be one of %(Positions)s.

     -d / --director
        Specify director.
        Must be one of %(Directors)s.

    -m / --mapset
        Specify goal position set.
        Must be one of %(PositionSets)s.

     -p / --percepts
        Specify perceptual model to use.
        Must be one of %(Percepts)s.

     -a / --ablate
        Specify option to flip.

     -b / --ablation
        Run full ablation suite.

     -o / -- orient
        Specify direction to face at the begining from 0,1,2,3

     -c / --crossvalidate=%(CrossValidations)s
         Use parser trained on cross-validation based on the parameter.

    -u / --uncorrected
          Use uncorrected saved parse trees, instead of hand corrected gold-standard. 
""" % globals()

import os.path, time
from Marco import Follower
from Utility import logger

logs={}
def setLogs(id):
    logger.TraceDir = 'SubjectLogs/Marco_DirectionAll0_%d' % (Orientation)
    if not os.path.exists(logger.TraceDir): os.mkdir(logger.TraceDir)
    if 'State' in logs: logs['State'].close()
    logs['State'] = file(os.path.join(logger.TraceDir,'MotTrace-%s' % id), 'w')
    if 'Action' in logs: logs['Action'].close()
    logs['Action'] = file(os.path.join(logger.TraceDir,'ActTrace-%s' % id), 'w')

def trace(log,value):
    logs[log].write('%s\n'%repr(value))

class TimedFollower(Follower):
    def follow(self,instructions):
        now = time.time()
        result = instructions
        print 'Instructions =', instructions
        if '-' in instructions:
            prefix,instructionID = instructions.split('-')
        else: instructionID = instructions
        setLogs(instructionID)
        logger.runComplete('Following %s',instructionID)
        RunResults = []
        for label,step in self.stages:
            startTime = now
            logger.stageComplete('Starting %s',label)
            result,CaughtError,CaughtErrorTxt = step(result,instructionID)
            if self.NLUQueue: self.NLUQueue.put((label,result))
            logger.stageComplete('Ending %s',label)
            if isinstance(result,list):
                for rst in result: logger.stageComplete("%r",rst)
            else: logger.stageComplete('%r',result)
            now = time.time()
            logger.info('%s took %d', label, now - startTime)
            RunResults.append(result)
            if CaughtError == 'EOFError':
                return RunResults,CaughtError,CaughtErrorTxt
        logger.flush()
        return RunResults,CaughtError,CaughtErrorTxt
    
    def run(self,files,instructionQ=None,successes=0,attempts=0,Results={},Conditions=[]):
        global InstructionText
        for file in files:
            while (instructionQ and not instructionQ.empty()):
                type,message = instructionQ.get()
                print 'TimedFollower.run :: got', type,message
                if type == 'State': print 'Got state message'
                elif type == 'ID' : file = message
                elif type == 'Text': InstructionText = message
                else:
                    logger.error('TimedFollower.run::instructionQ:'
                              '  Unknown message type: %s %s.',
                              type,message)
            Options.reset()
            results,error,resultTxt = self.follow(file)
            if Options.Statistics:
                logger.runComplete('Statistics: %s', Options.stats())
                name = file.split('-')[1]
                stats = open('MarcoLogs/Statistics/'+'-'.join(Conditions)+'-'+logger.timeStamp+'-'+name,'w')
                for opt,count in Options.stats().items(): stats.write('%s: %d\n'%(opt,count))
                stats.close()
            attempts += 1
            if resultTxt == Success:
                successList = Results.setdefault(resultTxt,[])
                successList.append((resultTxt,file))
                Results[resultTxt] = successList
                successes += 1
            else:
                errorList = Results.setdefault(error,[])
                errorList.append((resultTxt,file))
                Results[error] = errorList
        return successes,attempts

Success = 'Success'
def printResults(Results,startTime,successes,attempts,Conditions=[]):
    endTime = time.time()
    blank = 0
    for result,explanations in Results.items():
        logger.runComplete("Result: %s %d", result, len(explanations))
        if result == 'EOFError':
            blank = len(explanations)
            continue
        # Sort by exception
        explanations.sort(lambda a,b: cmp(a[1],b[1]))
        count = {}
        for explanation,riSet in explanations:
            exceptText = str(explanation)
            exceptText = exceptText.replace(' field structure\\n\\n',':')
            exceptText = exceptText.replace('  ',' ')
            exceptText = exceptText.replace('\t',' ')
            exceptText = exceptText.replace('\\','')
            if len(exceptText)>85: exceptText=exceptText[:85]+'...'
            logger.runComplete('%s\t%s\t%s', result,exceptText,riSet)
            director = riSet.split('-')[1].split('_')[0]
            count.setdefault(director,0)
            count[director] += 1
        logger.runComplete("Result: %s %s", result, ''.join(['%s: %d; '%(d,c) for d,c in count.items()]))
    recordResults(Results, time.strftime("%Y-%m-%d-%H-%M",time.localtime(startTime)), Conditions)
    logger.runComplete('Failures on %d of %d', sum([len(l) for res,l in Results.items() if res != Success])-blank, attempts-blank)
    count = attempts-blank
    if count:
        logger.runComplete('Success on %d of %d: %3.1f%%', successes, count, 100.0*successes/count)
    logger.runComplete('Tests took %.2f seconds', endTime-startTime)
    logger.runComplete('Time Stamp %s-%d',logger.timeStamp, Orientation)

resultCodes = {
    Success : '#',
    None : '_',
    'ArithmeticError' : '*',
    'AttributeError' : 'a',
    'EOFError' : '0',
    'IndexError' : 'I',
    'KeyError' : 'k',
    'LookupError' : '%',
    'NotImplementedError' : 'i',
    'RuntimeError' : 'r',
    'TypeError' : 't',
    'ValueError' : 'v',
    'None' : '_',
    'exceptions.AttributeError' : 'a',
    'exceptions.ArithmeticError' : '*',
    'exceptions.EOFError' : '0',
    'exceptions.IndexError' : 'I',
    'exceptions.KeyError' : 'k',
    'exceptions.LookupError' : '%',
    'exceptions.NotImplementedError' : 'i',
    'exceptions.RuntimeError' : 'r',
    'exceptions.TypeError' : 't',
    'exceptions.ValueError' : 'v',
    }
def recordResults(Results, timeStamp='', Conditions=[]):
    if Conditions: Condition = '-'.join(Conditions)+'-'
    else: Condition = ''
    if not timeStamp: timeStamp = logger.timeStamp
    file_prefix = os.path.join('MarcoLogs','Follower-Results-%s%s-%d'%(Condition,timeStamp,Orientation))
    
##    import cPickle, gzip
##    resultsFile = gzip.open(file_prefix+'.log.gz', 'w')
##    cPickle.dump(Results,resultsFile)
##    resultsFile.close()
    
    rowFile = open(file_prefix+'-Row.csv', 'w')
    if Condition: rowFile.write("%s-%s," % (timeStamp,Condition))
    else: rowFile.write("%s," % (timeStamp))
    colFile = open(file_prefix+'-Col.txt', 'w')
    colFile.write("time\t%s\n" % (timeStamp))
    if Condition: colFile.write("condition\t%s\n" % (Condition))
    
    riSetResults = {}
    for result,explanations in Results.items():
        for explanation,riSet in explanations:
            riSetResults[riSet] = result
    riSetList = [(riSet,result) for riSet,result in riSetResults.items()]
    # Sort by Route Instruction ID
    riSetList.sort()
    for riSet,result in riSetList:
        if isinstance(result,Exception): result = result.__class__.__name__
        colFile.write("%s\t%s\n" % (riSet.split('-')[1],result))
        rowFile.write("%s," % (resultCodes[result]))
    rowFile.close()
    colFile.close()
    if not Condition:
        fileList = open(os.path.join('MarcoLogs','Formatted-Results.txt'),'a')
        fileList.write('Follower-Results-'+timeStamp+'-Col.txt'+'\n')
        fileList.close()
        makeAllCSV()

from LogAnalyzer import PerDirectionFields
def makeAllCSV(filelist='Formatted-Results.txt',csvfile='Follower-All-Results.csv',logdir='MarcoLogs'):
    """Make a comma-separated values spreadsheet,complete with equations."""
    import string
    def col(colNum):
        alphabet = string.uppercase
        colIdx = colNum-1
        id = colIdx % 26
        overflow = (colIdx / 26)-1
        if colIdx < 26: return alphabet[id]
        else: return alphabet[overflow]+alphabet[id]
    
    allFile = open(os.path.join(logdir,csvfile),'w')
    # Collect Input Files and Write Names
    MarcoResultFiles = []
    allFile.write(',')
    for run in open(os.path.join(logdir,filelist)):
        MarcoResultFiles.append(open(os.path.join(logdir,run[:-1])))
        allFile.write("%s," %('-'.join(run.split('-')[2:-1])))
    allFile.write("Regression,Candidate,")
    for field in PerDirectionFields:
        allFile.write("%s," %(field))
    allFile.write('\n')
    
    # Print Time Stamps
    allFile.write("time,")
    for file in MarcoResultFiles:
        line = file.next()
        time,timeStamp = line.split('\t')
        allFile.write("%s," %(timeStamp[:-1]))
    allFile.write('\n')
    
    # Print Result Summaries
    results = [x for x in resultCodes if isinstance(x,str) and '.' not in x]
    results.sort()
    successes,totals,empties = 5+results.index(Success),4,5+results.index('EOFError'),
    accuracyCodeLine=','.join(['=%s%d*100/(%s%d-%s%d)'
                               % (col(n+2),successes,col(n+2),totals,col(n+2),empties)
                               for n,file in enumerate(MarcoResultFiles)])
    allFile.write('%s,%s\n' % ('% Correct', accuracyCodeLine))
    #allFile.write(',,,=%s%d/(%s%d-%s%d)\n' % (col(n+5),successes,col(n+5),totals,col(n+5),empties))

    numInstructions = 770
    firstID = 5+len(results)
    lastID = firstID + numInstructions
    allFile.write('%s,%s\n'
                  % ('Total', ','.join(['=counta(%s%d:%s%d)' % (col(n+2),firstID,col(n+2),lastID)
                                        for n,file in enumerate(MarcoResultFiles)])))
    for result in results:
        if '.' in result: errName = result.split('.')[1]
        else: errName = result
        countCodeLine = ','.join(['"=countif(%s%d:%s%d,\'%s\')"'
                                  % (col(n+2),firstID,col(n+2),lastID+2,resultCodes[result])
                                  for n,file in enumerate(MarcoResultFiles)])
        allFile.write('%s %s,%s\n' % (resultCodes[result],errName, countCodeLine))

    HumanResultFiles = []
    for i,Stat in enumerate(PerDirectionFields):
        file = open(os.path.join(logdir,'-'.join(('Follower','Results','Followers',Stat,'Col.txt'))))
        file.next() # Skip ID line
        HumanResultFiles.append(file)
    humanLineID = ''
    
    # Print Per Direction Set Results
    n = len(MarcoResultFiles)
    for row,set in enumerate(open(os.path.join(logdir,
                                               'Follower-Results-2005-05-21-01-22-Col.txt'))):
        if set.startswith('time'): continue
        lineID,result = set.split('\t')
        allFile.write("%s," % (lineID))
        for file in MarcoResultFiles:
            line = file.next()
            if line.startswith('condition'): line = file.next()
            id,result = line.split('\t')
            allFile.write("%s," % (resultCodes[result[:-1]]))

        while humanLineID < lineID:
            humanLineID, timesFollowed = HumanResultFiles[-1].next().split('\t')
        if humanLineID == lineID:
            regressionCodeLine=('"=if(and(countif(%s%d:%s%d,\'%s\')>0,not(exact(%s%d,\'%s\'))),\'xxxxx\',\'\')"'
                                % (col(2),row+firstID-1,col(n),row+firstID-1,resultCodes[Success],
                                   col(n+1),row+firstID-1,resultCodes[Success]))
            allFile.write("%s," %(regressionCodeLine))
            
            candidateCodeLine=('"=if(and(%s%d>=%1.2f,%s%d>=%1.2f,not(exact(%s%d,\'%s\'))),\'*****\',\'\')"'
                          % (col(n+4),row+firstID-1,0.75,
                             col(n+6),row+firstID-1,5.0,
                             col(n+1),row+firstID-1,resultCodes[Success]))
            allFile.write("%s," %(candidateCodeLine))
            
            for file in HumanResultFiles[:-1]:
                line = file.next()
                id,result = line.split('\t')
                allFile.write("%s," % (result[:-1])) #chomp newline
            allFile.write("%s," % (timesFollowed[:-1])) #chomp newline
        allFile.write('\n')
    allFile.close()

def test():
    import doctest
    doctest.testmod()

def getFollowerTestSet(follower, Instructions):
    if not CrossValidate:
        for mapname in Maps:
            for posset in PositionSets:
                mapsig = '_%s%s_' % (mapname,posset)
                yield follower, mapname, posset, [i for i in Instructions if mapsig in i]
        return
    
    import ParseDirections, DirectionCorpus
    if CrossValidate.startswith('Map'):
        for mapname in Maps:
            for posset in PositionSets:
                mapsig = '_%s%s_' % (mapname,posset)
                if CrossValidate == 'MapNext': TrainMaps = Maps[(Maps.index(mapname)+1)%len(Maps)]
                elif CrossValidate == 'MapPrev': TrainMaps = Maps[(Maps.index(mapname)-1)%len(Maps)]
                else: TrainMaps = [m for m in Maps if m != mapname]
                parser = ParseDirections.getDirParser(Directors, TrainMaps,
                                                      PcfgFile='', SenseTaggerFile='', collectStats=False)
                follower.parse.cannedFn = parser.parse
                yield follower, mapname, posset, [i for i in Instructions if mapsig in i]
        return
    
    def getParserTestSet():
        if CrossValidate == 'Directors':
            for director in Directors:
                instRegexp = DirectionCorpus.constructItemRegexp([director])
                TestSet = DirectionCorpus.DirectionCorpusReader(instRegexp).items('CleanDirs')
                parser = ParseDirections.getDirParser([d for d in Directors if d != director], Maps,
                                                      PcfgFile='', SenseTaggerFile='', collectStats=False)
                yield parser, TestSet
        elif CrossValidate == 'Positions':
            for position in range(1,8):
                instRegexp = DirectionCorpus.constructItemRegexp(starts=[str(position)])
                TestSet = DirectionCorpus.DirectionCorpusReader(instRegexp).items('CleanDirs')
                parser = ParseDirections.getDirParser(Directors, Maps,
                                                      PcfgFile='', SenseTaggerFile='', collectStats=False,
                                                      Starts=[str(p) for p in range(1,8) if p != position])
                yield parser, TestSet
        elif CrossValidate == 'Random':
            for i in range(6):
                yield ParseDirections.getDirParser(Directors, Maps,
                                                   PcfgFile='', SenseTaggerFile='', collectStats=False,
                                                   cv=1/6.0)
    
    for parser, TestSet in getParserTestSet():
        for mapname in Maps:
            for posset in PositionSets:
                mapsig = '_%s%s_' % (mapname,posset)
                follower.parse.cannedFn = parser.parse
                yield follower, mapname, posset, [i for i in TestSet if mapsig in i]

CrossValidate = None # 'Maps' # 'Directors' # 'Positions' #  'Random'
def run(executor,follower,POMDPs,Robot,Recognizer,Instructions,Conditions=[]):
    successes = 0
    attempts = 0l
    Results={}
    instructionQ = None
    startTime = time.time()
    if CrossValidate: Conditions = Conditions + ['CV_'+CrossValidate]
    for follower, mapname, PosSet, TestSet in getFollowerTestSet(follower, Instructions):
        POMDPs[mapname].PosSet = int(PosSet)
        POMDPs[mapname].Positions = POMDPs[mapname].PositionSet[int(PosSet)]
        executor.setRobot(Robot(POMDPs[mapname], mapname, Recognizer))
        successes,attempts = follower.run(TestSet, None, successes, attempts, Results, Conditions)
    printResults(Results,startTime,successes,attempts,Conditions)
    return 0

def spawn(commandline, pids):
    if 'uname' in dir(os) and os.stat('/sys/devices/system/cpu'):
        numcpus = len(os.listdir('/sys/devices/system/cpu'))
    else: numcpus = 1
    if numcpus > 1:
        threads = numcpus - 1
        needwait = os.P_NOWAIT
    else:
        threads = 1
        needwait = os.P_WAIT
        
    status = os.spawnv(needwait, './Harness.py', commandline)
    if needwait == os.P_WAIT: return
    pids.append(status)
    for pid in pids[:]:
        pid,status = os.waitpid(pid,os.WNOHANG)
        print pid,status
        if os.WIFEXITED(status) and pid in pids:
            pids.remove(pid)
    if len(pids) <= threads: return
    pid,status = os.waitpid(-1,0)
    pids.remove(pid)

def grabInput(source):
    if source.startswith('INPUT'): return InstructionText
    else: DirectionCorpus.readCleaned(source,source.split('-')[1])

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

Orientation = 0
def main(argv=None):
    import getopt
    showGUI = False
    verbose = False
    AblationRun = False
    Ablate = []
    pomdp_name = Maps[0]
    Instructions = []
    global InstructionText
    InstructionText = ''
    Director = ''
    Start = 0
    Target = 0
    PosSet = '0'
    Percept = Percepts[0]
    Uncorrected = False
    global Orientation, CrossValidate
    
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], 'vha:be:gp:o:c:r:i:s:t:m:d:u',
                                       ['verbose', 'help',
                                        'ablate=', 'ablation', 'env=', 'gui', 'percepts=', 'orient=','crossvalidate=','uncorrected',
                                        'route=', 'instruction=', 'start=', 'target=', 'mapset=', 'director=',])
        except getopt.error, msg:
             raise Usage(msg)
        for opt, arg in opts:
            if opt in ('-v', '--verbose'):
                verbose = True
            elif opt in ('-h', '--help'):
                print >>sys.stderr, __doc__
                sys.exit(0)
            elif opt in ('-a', '--ablate'):
                Ablate.append(arg)
                if arg not in dir(Options) and arg != 'Default':
                    raise Usage("Ablated option '%s' not in option list: %s" %(arg, dir(Options)))
            if opt in ('-b', '--ablation'):
                AblationRun = True
            elif opt in ('-e', '--env'):
                pomdp_name = arg
                if pomdp_name not in Maps:
                    raise Usage("map name '%s' not in map list: %s" %(pomdp_name,Maps))
            elif opt in ('-g', '--gui'):
                showGUI = True
            elif opt in ('-o', '--orient'):
                Orientation = int(arg)
            elif opt in ('-p', '--percepts'):
                if arg == 'vv': Percept = 'PomdpSimViewVector'
                elif arg == 'sss': Percept = 'PomdpSimSmallScaleStar'
                else: Percept = arg
                if Percept not in Percepts:
                    raise Usage("percept type '%s' not in percepts list: %s" %(Percept,Percepts))
            elif opt in ('-r', '--route'):
                Instructions = [arg]
            elif opt in ('-i', '--instruction'):
                InstructionText = arg
            elif opt in ('-s', '--start'):
                Start = arg
            elif opt in ('-t', '--target'):
                Target = arg
            elif opt in ('-m', '--mapset'):
                PosSet = arg
            elif opt in ('-d', '--director'):
                Director = arg
            elif opt in ('-c', '--crossvalidate'):
                if arg not in CrossValidations:
                    raise Usage("percept type '%s' not in CrossValidations list: %s" %(arg,CrossValidations))
                CrossValidate = arg
            elif opt in ('-u', '--uncorrected'):
                Uncorrected = True
            
            if opt in sys.argv: sys.argv.remove(opt)
            if arg in sys.argv: sys.argv.remove(arg)
            if opt+'='+arg in sys.argv: sys.argv.remove(opt+'='+arg)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

    if AblationRun:
        pids = []
        if Ablate: Ablation = Ablate
        else: Ablation = ['Default']+[o for o in dir(Options) if type(getattr(Options,o)) == bool]
        for option in Ablation:
            for pose in [str(p) for p in range(4)]:
                spawn(['Harness.py', '-o', pose, '-a', option], pids)
        return

    import DirectionCorpus, ParseDirections, Sense, CompoundAction, Executor
    CompoundAction.Options = Options

    if not Instructions:
        if Start and Target and (Director or InstructionText):
            if not Director and InstructionText: Director = 'INPUT'
            Instructions = ["%s_%s[01]_%s_%s_Dirs_1.txt" % (Director,pomdp_name,Start,Target)]
        elif Uncorrected:
            instRegexp = DirectionCorpus.constructItemRegexp(Directors, mapversions='[01]')
            Instructions = DirectionCorpus.DirectionCorpusReader(instRegexp).items('FullDirTrees')
        else:
            instRegexp = DirectionCorpus.constructItemRegexp(Directors, mapversions='[01]')
            Instructions = DirectionCorpus.DirectionCorpusReader(instRegexp).items('ContentFrames')

    import Robot.Recognizers_Compound
    Robot.Recognizers_Compound.Options = Options
    if Percept.startswith('PomdpSim'):
        from Robot.POMDP_Sim import Robot_POMDP_Sim as Robot
    if Percept == 'PomdpSimViewVector':
        from Robot import Recognizers_POMDP_Antie_Periph_Sim as RecognizerModule
        Recognizer = RecognizerModule.PomdpAntiePeriphSimRecognizer
    elif Percept == 'PomdpSimSmallScaleStar':
        from Robot import Recognizers_HSSH as RecognizerModule
        Recognizer = RecognizerModule.HsshRecognizer
        for option in ('FaceDistance','FaceUntil','FacePast'):
            setattr(Options, option, False)
    RecognizerModule.Options = Options
    
    logger.shutdownLogger()
    logger.initLogger('Follower-'+str(Orientation), 26, Ablate==[], LogDir='MarcoLogs')
    executor = Executor.InstructionQueueExecutor()

    parser = ParseDirections.getDirParser(Directors, Maps, collectStats=False)

    class wrapper(object):
        def __init__(self,liveFn,cannedFn=''):
            self.cannedFn = cannedFn
            self.liveFn = liveFn
        def __call__(self,input,id):
            if id.startswith('INPUT') or CrossValidate: return self.liveFn(input),None,''
            else: return self.cannedFn(input,id)

    if CrossValidate:
        follower = TimedFollower(DirectionCorpus.readCleaned, wrapper(parser.parse),
                                 wrapper(Sense.trees2frames), CompoundAction.model, executor)
    elif Uncorrected:
        follower = TimedFollower(DirectionCorpus.readCleaned,
                                 wrapper(parser.parse, ParseDirections.readUncorrParse),
                                 wrapper(Sense.trees2frames, Sense.readCorrFrame),
                                 CompoundAction.model, executor)
    else:
        follower = TimedFollower(wrapper(grabInput, DirectionCorpus.readCleaned),
                                 wrapper(parser.parse, ParseDirections.readCorrParse),
                                 wrapper(Sense.trees2frames, Sense.readCorrFrame),
                                 CompoundAction.model,
                                 executor)
    from POMDP.MarkovLoc_Grid import pomdp as Grid_pomdp
    from POMDP.MarkovLoc_Jelly import pomdp as Jelly_pomdp
    from POMDP.MarkovLoc_L import pomdp as L_pomdp
    POMDPs = {'Grid':Grid_pomdp, 'Jelly':Jelly_pomdp, 'L':L_pomdp}
    for pomdp in POMDPs.values():
        pomdp.trace = trace
        pomdp.PosSet = int(PosSet)
        pomdp.Positions = pomdp.PositionSet[pomdp.PosSet]

    if Ablate:
        logger.runComplete("Ablating condition: %s", ', '.join(Ablate))
        for ablateOpt in Ablate:
            if ablateOpt != 'Default':
                setattr(Options, ablateOpt, not getattr(Options, ablateOpt))
                ## ResetCache options are 3 choices for resetting the cache.
                ## At least one must be set, or memory will explode.
                if ablateOpt == 'TurnTermResetCache':
                    Options.TurnPostResetCache = True
                else: Options.TurnTermResetCache = False
                if ablateOpt+'List' in dir(Options):
                    for option in getattr(Options,ablateOpt+'List'):
                        setattr(Options, option, False)
        for pomdp in POMDPs.values():
            pomdp.getDirectionVal = Orientation
        if not Options.ViewMemory:
            from Robot.ViewCache import AmnesiacViewCache
            Recognizer.ViewCache = AmnesiacViewCache
    
    if Uncorrected:
        Ablate.append('Uncorrected')
        if 'Default' in Ablate: Ablate.remove('Default')
    
    if showGUI:
        import FollowerGUI
        return FollowerGUI.run(executor,follower,POMDPs,Robot,Recognizer,Instructions,pomdp_name)
    else: # Default
        return run(executor,follower,POMDPs,Robot,Recognizer,Instructions,Ablate)

def _profile():
    import hotshot, hotshot.stats
    prof = hotshot.Profile("harness.prof")
    prof.run('main(["Harness","-a","Default"])')
    prof.close()
    stats = hotshot.stats.load("harness.prof")
    stats.strip_dirs()
    stats.sort_stats('cumulative', 'calls')
    stats.print_stats(40)

if __name__ == "__main__":
    import sys
    import Options
    Options = Options.Options()
    sys.exit(main())

#from Harness import *
#main(['foo','-p','sss'])
