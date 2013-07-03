#!/usr/bin/env python
Maps = ['Grid','Jelly','L']
Positions = [str(i+1) for i in range(7)]
Routes = []

__doc__ ="""Run the follower through a series of routes.

Usage: RouteRunner.py [options]

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
        Follow this route, of form ENV_START_DEST.

    -s / --start
        Specify start position.
        Must be one of %(Positions)s.

     -t / --target
        Specify target position.
        Must be one of %(Positions)s.
""" % globals()

import Queue, thread, os.path, re, random
from Utility import logger,lstail
import WheelchairGUI, ShortestPath

def threaded_run(Executor,Robot,Routes,Pomdp,map_dir='Maps'):
    #dynamic functionality will only work in GUI mode
    return WheelchairGUI.run(Executor,Robot,Routes,Pomdp,map_dir='Maps',Instructions=not dynamic)

def run(executor,Robot,POMDPs):
    successes = 0
    attempts = 0l
    Results={}
    for mapname,pomdp in POMDPs.items():
        executor.setRobot(Robot(pomdp, mapname))
        successes,attempts = executor.run([r for r in Routes if mapname in r],
                                          successes, attempts, Results)
    return 0

Success = 'Success'
TurnLeft = 'TurnLeft'
TurnRight = 'TurnRight'
TravelFwd = 'TravelFwd'
DeclareGoal = 'DeclareGoal'

class RouteRunner(object):
    def __init__(self,Map=None):
        self.StatusQueue = None
        self.Map = Map
        self.Start = None
        self.Target = None
    
    def setRobot(self,Robot):
        self.robot = Robot
        self.Map = Robot.pomdp
    
    def initializeRoute(self,Mapname,Start,Target):
        if hasattr(self,'Start') and Start == self.Start and Target == self.Target:
            return
        self.Start = Start
        self.Target = Target
        if self.StatusQueue:
            self.StatusQueue.put(('Start Place',Start))
            self.StatusQueue.put(('Destination',Target))
        self.robot.setRoute(Start,Target)
    
    def planRoute(self):
        """plan Route from self.Start to self.Target in self.Map."""
        pathobject = ShortestPath.ShortestPath(self.Map, self.robot.currentState)
        (distance, Path) = pathobject.ReturnPath(self.Start, self.Target)
        #Path is a list of gateway and direction tuples
        (currentGateway,y) = Path[0]
        
        #determine list of commands from Path
        Route = []
        
        #added to keep the "start and random direction" functionality
        if self.robot.currentState == None:
            randomDir = random.randint(0,3)
            self.robot.currentState = (currentGateway,randomDir)
        (temp,mydir) = self.robot.currentState
        
        #determine turn & travel commands from list of gateways & directions
        for (x, desireddir) in Path:
            while(desireddir != mydir and desireddir != -1):
                if (mydir > desireddir) and abs(mydir - desireddir) == 1  or (mydir == 0 and desireddir==3):
                    Route.append(TurnLeft)
                    mydir -= 1
                else:
                    Route.append(TurnRight)
                    mydir += 1
                mydir %= 4
        if (desireddir != -1): Route.append(TravelFwd)
        Route.append(DeclareGoal)
        return Route

    def execute(self,(Map,Start,Target)):
        CaughtError = None
        self.initializeRoute(Map,Start,Target)
        try:
            self.executeRoute(self.planRoute())
        except (KeyError,LookupError,ValueError),e:#,AttributeError
            logger.error('%s on %s', e.__class__.__name__, e)
            CaughtError = e
        if not self.robot.completed:
            reward,obs = self.robot.declareGoal()
            logger.stageComplete(
                'Declared Goal to complete instruction execution %s',(reward,obs))
        ResultTxt = self.robot.completed and 'Success' or 'Failure'
        logger.runComplete("%s in direction following.", ResultTxt)
        return self.robot.completed, CaughtError, ResultTxt

    #handles dynamic functionality. not sure if this is the best place for this function
    def userInterface(self):
        #breaks when user inputs "AutoNav" only
        while self.instructionQ:
            if not self.instructionQ.empty():
                (ID, newCommand) = self.instructionQ.get()
                if ID == "NavID":
                    self.robot.previousMode = self.robot.userInterfaceMode
                    if newCommand == "AutoNav":
                        self.robot.userInterfaceMode = "AutoNav"
                        return
                    elif newCommand == "Stop":
                        self.robot.userInterfaceMode = "Stop"
                        self.robot.flushActions()
                        continue
                    else:
                         self.robot.userInterfaceMode = "Causal"
                         action = newCommand
                    self.robot.perform(action)
                    #observe action added to sync GUI avatar with simulated robot (hack)
                    self.robot.perform("Observe")
                elif ID == "State":
                    # the GUI is trying to send new start and end positions, the following code needs to be restructured (doesn't work)
                    (start, end) = newCommand
                    self.Start = start
                    self.Dest = end
                    (x,y) = self.robot.currentState
                    self.robot.currentState = (self.robot.pomdp.Positions[int(start)], y)
                    self.robot.teleport(self.robot.currentState)
                    return
    
    def checkQueue(self):
        #added for dynamic path change functionality
        if self.instructionQ and not self.instructionQ.empty(): ##user put something in instructionQ
            self.userInterface()
            if not (self.robot.previousMode == "AutoNav" and self.robot.userInterfaceMode == "AutoNav"):
                # recalculate route as AutoNav button press brought control back here
                # assume correct location is in self.robot.currentState, and planRoute() uses self.robot.currentState
                #start over
                Actions = self.planRoute()
                self.robot.flushActions()
                return True
        return False
    
    def executeRoute(self,Actions):
        action = "Observe"
        self.robot.teleport(self.robot.currentState)
        while (action != "Stop" or action != "DeclareGoal"):
            for i,action in enumerate(Actions):
                if dynamic and self.checkQueue():
                    break
                logger.info('<%d> %s',i,action)
                if self.StatusQueue: self.StatusQueue.put(('Executing',i))
                try:
                    results = self.robot.perform(action)
                    #self.robot.perform("Observe")
                    logger.info('<%d> %s => %r', i,action,results)
                except StopIteration,e:
                    results = e
                    logger.info('<%d> %s => %r', i,action,results)
                    logger.info('End of Instruction Execution after <%d>', i)
    
    def runRoute(self,Route,successes,attempts,Results):
        results,error,resultTxt = self.execute(Route)
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
    
    def run(self,Routes,successes=0,attempts=0,Results={}):
        for Route in Routes:
            successes,attempts = self.runRoute(Route,successes,attempts,Results)
            print str(successes)+" successes out of "+str(attempts) +" attempts."
        return successes,attempts

class LogRouteRunner(RouteRunner):
    def __init__(self, directory, **kwargs):
        self.directory = directory
        self.Director = '.*'
        self.route = ''
        RouteRunner.__init__(self,**kwargs)
    
    def getOrientation(self):
        motionLog = file(os.path.join(self.directory,'MotTrace-'+self.route))
        x,y,theta = motionLog.readline()[:-1].split(',')
        motionLog.close()
        return int(theta)
    
    def getRoute(self):
        regexp = re.compile('MotTrace-%s_%s[01]_%s_%s_Dirs_.\.txt'%(
            self.Director,self.Map.name,self.Start,self.Target))
        files = lstail(self.directory, regexp)
        if not files: 
            logger.critical('Cannot find route trace %s/%s', self.directory, regexp.pattern)
            self.route = ''
        else:
            self.route = files[0].split('-')[1]
        return self.route
    
    Actions = {
        'Left\n' : TurnLeft,
        'Forward\n' : TravelFwd,
        'Right\n' : TurnRight,
        'CorrTgt\n' : DeclareGoal,
        'IncrTgt\n' : DeclareGoal,
        }
    def planRoute(self):
        self.getRoute()
        logger.runComplete('Replaying route trace %s/%s', self.directory, self.route)
        return [self.Actions[act]
                for act in file(os.path.join(self.directory,'ActTrace-'+self.route))
                if act in self.Actions]
    
    def executeRoute(self,Actions):
        if not Actions: return
        self.robot.teleport(self.Start)
        self.robot.teleport('_%d'%self.getOrientation())
        return super(LogRouteRunner,self).executeRoute(Actions)

class MultiLogRouteRunner(LogRouteRunner):
    def __init__(self, log_root, director='.*', directories=[], **kwargs):
        self.log_root = log_root
        self.directories = directories
        self.Director = director
        super(MultiLogRouteRunner,self).__init__('',**kwargs)
    
    def run(self,Routes,successes=0,attempts=0,Results={}):
        for Director in ['EDA','EMWC','KLS','KXP','TJS','WLH']:
            self.Director = Director
            for Route in Routes:
                self.initializeRoute(*Route)
                for directory in self.directories:
                    self.directory = os.path.join(self.log_root,directory)
                    if not self.getRoute(): continue
                    self.runRoute(Route,successes,attempts,Results)
                    successes,attempts = self.runRoute(Route,successes,attempts,Results)
        return successes,attempts

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

if __name__ == "__main__":
    import getopt,sys
    
    showGUI = False
    verbose = False
    Map = Maps[0]
    Start = 0
    Target = 0
    logdir = ''
    AllLogs = False
    
    #added for dynamic path change functionality
    dynamic = False
    
    if False:
        showGUI = True # False # 
        logdir = 'SubjectLogs'
        AllLogs = True
    
    try:
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'vhe:gl:Lo:r:s:t:d',
                                       ['verbose', 'help',
                                        'env=', 'gui', 'logdir=', 'Logs', 'orient=',
                                        'route=', 'start=', 'target=', 'dynamic'
                                        ])
        except getopt.error, msg:
             raise Usage(msg)
        for opt, arg in opts:
            if opt in ('-v', '--verbose'):
                verbose = True
            elif opt in ('-h', '--help'):
                print >>sys.stderr, __doc__
                sys.exit(0)
            elif opt in ('-e', '--env'):
                Map = arg
                if Map not in Maps:
                    raise Usage("map name '%s' not in map list: %s" %(Map,Maps))
            elif opt in ('-g', '--gui'):
                showGUI = True
            elif opt in ('-l', '--logdir'):
                logdir = arg
            elif opt in ('-L', '--Logs'):
                AllLogs = True
            elif opt in ('-o', '--orient'):
                Orientation = int(arg)
            elif opt in ('-r', '--route'):
                Routes = [arg]
            elif opt in ('-s', '--start'):
                Start = int(arg)
            elif opt in ('-t', '--target'):
                Target = int(arg)
            elif opt in ('-d', '--dynamic'):
                dynamic = True
            
            if opt in sys.argv: sys.argv.remove(opt)
            if arg in sys.argv: sys.argv.remove(arg)
            if opt+'='+arg in sys.argv: sys.argv.remove(opt+'='+arg)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        sys.exit(2)

    if not Routes:
        if Start and Target:
            Routes = [(Map,Start,Target)]
        elif showGUI:
            Routes = [(Map,Start,Target)
                      for Start in Positions
                      for Target in Positions
                      if Start != Target]
        else:
            Routes = [(Map,Start,Target)
                      for Map in Maps
                      for Start in Positions
                      for Target in Positions
                      if Start != Target]

    logger.shutdownLogger()
    logger.initLogger('RouteRunner', 26, LogDir='.')

    if logdir:
        if AllLogs:
            directories = lstail(logdir,re.compile('.*_Direction(All|%s)[01]_\d$'%(Map)))
            executor = MultiLogRouteRunner(logdir, directories=directories, Map=Map,)
        else: executor = LogRouteRunner(logdir, Map=Map,)
    else:
        executor = RouteRunner(Map)
        (temp,executor.Start, executor.Target) = Routes[0]
    
    from Robot.POMDP_Sim_Min import Robot_POMDP_Sim_Min as Robot
    from POMDP.MarkovLoc_Grid import pomdp as Grid_map
    from POMDP.MarkovLoc_Jelly import pomdp as Jelly_map
    from POMDP.MarkovLoc_L import pomdp as L_map
    POMDPs = {'Grid':Grid_map, 'Jelly':Jelly_map, 'L':L_map}

    if showGUI:
        threaded_run(executor,Robot,Routes,POMDPs[Map])
    else:
        run(executor,Robot,POMDPs)
