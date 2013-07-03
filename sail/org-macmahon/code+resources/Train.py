from Navigator import *
from VisualCues import *
import Movement, HotSpots, Joystick, SoundQueue
from Directions import DirectionDialog, getFiles
import time, viz

MAX_PLAT_SIZE   = 81
MAX_PLAT_HEIGHT = 25
MAX_PLAT_WIDTH  = 25
ATTENTION="********************************************\n"
SCALE = 40.0
RADIUS = int(SCALE/8*1.41)

def CoordsToPlat(x,y):
    return (int(round(x/SCALE)),int(round(-y/SCALE)))
def PlatToCoords(x,y):
    return (x*SCALE,-y*SCALE)

def ReadInDistances(filename):
    dist={}
    FILE = open(filename,'r')
    for line in FILE.readlines():
        try:
            words = line.split()
            dist[(int(words[0]),int(words[1]))]=int(words[2])
            dist[(int(words[1]),int(words[0]))]=int(words[2])
            dist[(int(words[0]),int(words[0]))]=0
            dist[(int(words[1]),int(words[1]))]=0
        except:
            pass
    FILE.close()
    return dist

#self.mode:
#  Training mode 'BoundedWander' (explore with hotspots for n moves)      -     VIZ option1 not selected 
#  Training mode 'Explore' (explore with hotspots)      -     
#  Testing mode 'HotspotQuiz'  (go from hotspot to hotspot) - VIZ option1 selected 
#  Testing mode 'EfficiencyTest'  (go from hotspot to hotspot w/in a certain efficiency)
#  Testing mode 'TurnAround'  (Turn in place without moving)

#  prefix:    string identifying the subject to prefix to data files, e.g. initials
#  env:        string of the name of the environment to run in
#  numRuns:    integer of the number of sucessful tests to achieve before competency is reached and subject can continue
#  exptName: string of the code for the experiment
#  mapDir:    string of relative path to the maps directory
#  onFinish: function to run when test run is complete
#  init_mode: string of initial mode of subject: BoundedWander|Explore|HotspotQuiz|TurnAround (see above)
#  group:    integer of which group subject was assigned to
#  PositionList: List of form [[i1,j1], [i2,j2],...,[in,jn]] of [start, target] positions, by hotspot number
#  numMoves: integer for the number of moves for BoundedWander mode
#  accuracy: movement efficiency to terminate HotspotQuiz
class Train:
    def __init__(self, prefix, env, numRuns=0, exptName="", mapDir="Maps/",
                onFinish=None, init_mode='Explore', group=0, positionList=[], numMoves=100,
                efficiency=0.65, directionDir="Directions/", movie=None, movement='Discrete'):
        self.mode = init_mode
        self.prefix = prefix
        self.layout = exptName+env
        self.exptName= exptName
        self.outfile = prefix+"_"+self.layout+`group`+"_"
        self.mapdir=mapDir
        self.logdir='SubjectLogs/'
        self.directionDir=directionDir
        matches=getFiles(self.outfile,self.logdir)
        self.outfile +=`len(matches)+1`+".out"
        self.currVersion="Train $Revision: 1.86 $"
        print "Using layout:",(self.layout+".wrl")
        print "Using outfile:",self.outfile
        self.numGoodTrials = numRuns
        self.numSuccess = 0
        self.numFailures = 0
        self.numOK = 0
        self.onFinish = onFinish
        self.group=group
        self.positionList=positionList
        self.directions=None
        self.moveBound=numMoves
        self.jump=0
        self.group=group
        self.trialAccuracy=efficiency
        self.movie = movie
        if movement == 'Discrete': self.movement = Movement
        elif movement == 'Continuous':
            self.movement = Joystick.ContinuousMovement(scale=SCALE, center_offset=SCALE/10,
                                    keyboard=True, joyCalFile='NavigationModules/joyCal.dat',
                                    callback=self.fwdMovementCallback, backward=False, speed=7.5)
        else: raise ValueError, 'Unknown movement type requested: ', movement
        if (self.mode=='Directions'): HotSpots.SoundOn(0)
        self.cues = VisualCueList()
        self.envs={}
        self.envCues={}
        self.VisitedHotSpots = HotSpotList()
        if env == 'All':
            self.loadAllEnvs()
            env = 'Grid'
        else:
            print 'Loading env'
            self.room = viz.addchild(self.mapdir+self.layout+".wrl")
            print 'Setting appearance'
            self.room.appearance(viz.DECAL)
            self.envs[self.layout] = self.room
            print 'Loading cues'
            self.cues.readInCues(self.mapdir+self.layout+".obj")
            self.envCues[self.layout] = self.cues.CueList
        print 'Switching to env'
        self.switchLayout(env, self.group)
        for cues in self.envCues.values():
            for cue in cues:
                cue.Object.enable(viz.LIGHTING)
                cue.Object.disable(viz.COLLISION)
        self.outputHeader()
        self.starttime=time.time()
        self.closeCurtain()
        SoundQueue.RegisterWithMovementModule(self.movement)
    
    def loadAllEnvs(self):
        self.envs['DirectionGrid'] = viz.addchild(self.mapdir+'DirectionGrid'+".wrl")
        self.envs['DirectionL'] = viz.addchild(self.mapdir+'DirectionL'+".wrl")
        self.envs['DirectionJelly'] = viz.addchild(self.mapdir+'DirectionJelly'+".wrl")
        for env in self.envs.values(): env.appearance(viz.DECAL)
        self.cues.readInCues(self.mapdir+'DirectionGrid'+".obj")
        gridNumCues=len(self.cues.CueList)
        self.envCues['DirectionGrid'] = self.cues.CueList[0:gridNumCues]
        self.cues.readInCues(self.mapdir+'DirectionL'+".obj")
        lNumCues=len(self.cues.CueList)
        self.envCues['DirectionL'] = self.cues.CueList[gridNumCues:lNumCues]
        self.cues.readInCues(self.mapdir+'DirectionJelly'+".obj")
        jellyNumCues=len(self.cues.CueList)
        self.envCues['DirectionJelly'] = self.cues.CueList[(gridNumCues+lNumCues):jellyNumCues]
        self.room=self.envs['DirectionGrid'] 

    def switchLayout(self, env, groupid):
        self.layout = self.exptName+env
        filebase = self.mapdir+self.layout+str(groupid)
        print "Resetting hotspot distances", filebase+".eff"
        self.hotspotdist = ReadInDistances(filebase+".eff")
        print "Resetting movement", self.mapdir+self.layout+'.txt'
        if self.movement == Movement:
            self.movement.Init(self.mapdir+self.layout+'.txt', center_offset=SCALE/10, scale=SCALE)
        print "Resetting hotspots", filebase+".poi"
        HotSpots.ReadInHotSpots(filebase+".poi", scale=SCALE, radius=RADIUS, movement=self.movement)
        HotSpots.__FINISHED_WAV_FILE = 'SharedMedia/Sounds/Finished.wav'
        self.VisitedHotSpots.reset(HotSpots.InHotSpot())
        self.room=self.envs[self.layout]
        self.closeCurtain()
        for name in self.envs.keys():
            if name == self.layout:
                self.envs[name].enable(viz.COLLISION)
            else:
                self.envs[name].visible(viz.OFF)
                self.envs[name].disable(viz.COLLISION)
                for cue in self.envCues[name]:
                    cue.Object.visible(viz.OFF)
        
    def outputHeader(self):
        OUTFILE = open(self.logdir+self.outfile,'a')
        OUTFILE.write('\n/-------------------------------------------------\n')
        OUTFILE.write("|%s\n" % time.strftime("Date:%x Time:%X",time.localtime(time.time())))
        OUTFILE.write('|\tVersion: %s\n' % (self.currVersion))
        OUTFILE.write('|\tLayout: %s\n' % (self.layout))
        if self.mode=='Explore':
            OUTFILE.write('|\tMode: Explore with Hotspots\n')
        elif self.mode=='BoundedWander':
            OUTFILE.write('|\tMode: Explore with Hotspots for %d moves \n' %(self.moveBound))
        elif self.mode=='HotspotQuiz':
            OUTFILE.write('|\tMode: Hotspot Quiz\n')
        elif self.mode=='EfficiencyTest':
            OUTFILE.write('|\tMode: Efficiency Test\n')
        else:
            OUTFILE.write('|\tMode: Random Drop\n')
        OUTFILE.write('|\tRequired Good Trials: %d\n'%self.numGoodTrials)
        OUTFILE.write('|\tSpot\tXPos\tYPos\n')
        num = 0
        for (x,z) in HotSpots.GetHotSpots():
            num += 1
            _x,_z = CoordsToPlat(x,z)
            OUTFILE.write('|\t%d\t\t%d\t\t%d\n'%(num,_x,_z))
        if self.layout != 'DirectionAll':
            platobj = PLAT(MAX_PLAT_WIDTH,MAX_PLAT_HEIGHT,MAX_PLAT_SIZE)
            platobj.ReadTextImage(self.mapdir+self.layout+".txt")
            platobj.DisplayTextImage(OUTFILE)
        if self.mode=='Explore' or self.mode=='BoundedWander':
            OUTFILE.write('\n| (X,Y,Angle)\t Action\t Time\n')
        elif self.mode=='HotspotQuiz' or self.mode=='EfficiencyTest':
            OUTFILE.write('\n| (X,Y,Angle)\t Target\t Human Action\t Time\n')
        else:
            OUTFILE.write('\n| (X,Y,Angle)\t Query\n')
        OUTFILE.write('\\-------------------------------------------------\n')
        OUTFILE.close()
    def setMode(self,mode):
        self.mode=mode
    def outputMove(self,move='Unknown'):
        x,z,t = self.movement.GetPlatPose()
        OUTFILE = open(self.logdir+self.outfile,'a')
        if self.mode=='Explore':         OUTFILE.write(">E;\t")
        elif self.mode=='BoundedWander': OUTFILE.write(">W;\t")
        elif self.mode=='TurnAround':    OUTFILE.write(">T;\t")
        elif self.mode=='HotspotQuiz':    OUTFILE.write(">Q;\t")
        elif self.mode=='EfficiencyTest':    OUTFILE.write(">F;\t")
        OUTFILE.write("%d,%d,%d; "%(x,z,t))
        OUTFILE.write("\t%s;\t%f;"%(move,time.time()-self.starttime))
        if self.mode=='HotspotQuiz' or self.mode=='EfficiencyTest':
            target = HotSpots.GetCurrentTarget()
            if target:
                targetcoords = HotSpots.GetCurrentTargetLocation()
                targetpos = CoordsToPlat(targetcoords[0],targetcoords[1])
                OUTFILE.write("\t(%d: %d,%d);"%(target,targetpos[0],targetpos[1]))
        if self.movie: viz.screencapture(self.layout+"_%d_%d_%d"%(x,z,t)+'.bmp')
        OUTFILE.write("\n")
        OUTFILE.close()

    def outputFinalState(self):
        _x,_z,_t = self.movement.GetPlatPose()
        OUTFILE = open(self.logdir+self.outfile,'a')
        OUTFILE.write("> FINAL STATE: %d,%d,%d; at time: %f\n\n"%(_x,_z,_t,time.time()-self.starttime))
        OUTFILE.close()
    def log(self,logmsg):
        OUTFILE = open(self.logdir+self.outfile,'a')
        OUTFILE.write(logmsg)
        OUTFILE.close()
    def outputDirections(self,directionFile):
        OUTFILE = open(self.logdir+self.outfile,'a')
        DIRS= open(os.path.join('Directions',directionFile),'r')
        OUTFILE.write("DF: %s\n"%directionFile)
        for line in DIRS.readlines():
            OUTFILE.write("D: %s"%line)
        OUTFILE.close()
    def fwdMovementCallback(self):
        if self.movement != Movement:
            self.outputMove('ContMv')
            print 'Continuous: Mode', self.mode, 'Moves = ', self.movement.GetNumForwardMoves()
        if self.mode=='Explore' and HotSpots.InHotSpot():
            self.VisitedHotSpots.mark(HotSpots.InHotSpot())
            if self.VisitedHotSpots.all():
                if not self.positionList:
                    endPos = None
                else:
                    positionPair = self.positionList.pop()
                    endPos = positionPair[1]
                    while endPos == HotSpots.InHotSpot() and self.positionList.count(endPos) < len(self.positionList):
                        #only get another position if the list contains a position other than endPos
                        self.positionList.insert(0,endPos)
                        s,endPos = self.positionList.pop()
                HotSpots.StartTrials(numtrials=1, callback=self.callback, targetHotspot=endPos, AnnounceLater=0)
        elif self.mode=='BoundedWander':
            if (self.movement.GetNumForwardMoves() > self.moveBound):
                SoundQueue.PlaySound('SharedMedia/Sounds/Finished.wav')
                viz.clearcolor (1, 1, 1)
                self.closeCurtain()
                self.openCurtain()
                viz.clearcolor (0,0,0)
                print "Finished BoundedWander after", self.movement.GetNumForwardMoves(), "moves"
                if self.onFinish: self.onFinish(self)

    def callback(self,event):
        return 0

    def efficiencyTest(self):
        start=HotSpots.GetCurrentStart()
        target=HotSpots.GetCurrentTarget()
        accuracy = float(self.hotspotdist[start,target])/float(self.movement.GetNumForwardMoves())
        success = (accuracy >= self.trialAccuracy)
        if self.mode=='EfficiencyTest':
            self.VisitedHotSpots.mark(HotSpots.InHotSpot())
            if success:
                self.numSuccess += 1
                viz.clearcolor (0,1,0)
            else:
                self.numOK += 1
                viz.clearcolor (0,0,1)
            if self.numOK >= 3:
                self.numSuccess = 0
                self.numOK = 0
        print "Efficiency: ", accuracy, " Succ: ", self.numSuccess, " OK: ", self.numOK, "Fail:",  self.numFailures
        print 'Visited HotSpots', self.VisitedHotSpots, self.VisitedHotSpots.all()
        OUTFILE = open(self.logdir+self.outfile,'a')
        OUTFILE.write(">E;\t%d to %d;\t"%(start,target))
        OUTFILE.write("%d / %d"%(self.movement.GetNumForwardMoves(),self.hotspotdist[start,target]))
        OUTFILE.write(" = %f;\t"%(accuracy))
        OUTFILE.write("Successes %d;\t" %(self.numSuccess))
        OUTFILE.write("OK %d;\t" %(self.numOK))
        OUTFILE.write("Failures %d;\t" %(self.numFailures))
        OUTFILE.write("\n")
        OUTFILE.close()
        return success
    
    def mykey(self,key):
        if self.curtain:
            if key != ' ': return
            print "Mode:", self.mode, " jump: ", self.jump
            if self.jump:
                self.jump = 0
                if self.mode == 'TurnAround':
                    HotSpots.AnnounceHotSpots(1)
                    HotSpots.SayCurrentHotSpot('SharedMedia/Sounds/TurnAround.wav')
            else:
                if not self.starttime: self.starttime=time.time()
                if self.mode in ('Explore', 'BoundedWander'):
                    HotSpots.ResetHotSpots()
                    self.MoveToNext(random.randint(1,len(HotSpots.GetHotSpots())), self.mode)
                    self.jump = 0
                    self.VisitedHotSpots.reset(HotSpots.InHotSpot())
                elif self.mode in ('HotspotQuiz', 'EfficiencyTest'):
                    self.endTrial()
            if self.mode in ('Directions', ):
                if self.onFinish: return self.onFinish(self)
            else:
                HotSpots.AnnounceHotSpots(1)
                self.openCurtain()
        elif key in ('0', 'm', 'M',' ') and self.mode == 'TurnAround' and self.onFinish:
            return self.onFinish(self)
        elif not self.movement.OkMove(): return
        
        print key, self.movement.GetNumForwardMoves(), self.mode, 'HotSpot', HotSpots.InHotSpot()
        if key in ('w', 'W'):
            self.outputMove('WchHS')
            HotSpots.SayCurrentHotSpot()
        elif key in ('t', 'T','d', 'D') and self.mode in ('HotspotQuiz', 'EfficiencyTest'):
            self.outputMove('CurrTgt')
            HotSpots.SayCurrentTarget()
        elif key in ('d', 'D') and self.mode == 'Directions':
            self.outputMove('ReDirct')
            DirectionDialog(filename=self.directions, dir=self.directionDir)
        elif key == ' ':
            if self.mode in ('HotspotQuiz', 'EfficiencyTest', 'Directions'):
                done = 0
                if HotSpots.GetCurrentTarget() == HotSpots.InHotSpot():
                    self.outputMove('CorrTgt')
                    self.efficiencyTest()
                    if self.mode == 'EfficiencyTest':
                        #SoundQueue.PlaySound('SharedMedia/Sounds/correct.wav')
                        if (self.numSuccess >= self.numGoodTrials 
                            and (self.numGoodTrials == 1 or self.VisitedHotSpots.all())):
                            HotSpots.StopTrials()
                            self.closeCurtain()
                            done = 1
                else:
                    self.outputMove('IncrTgt')
                    if self.mode == 'EfficiencyTest': 
                        SoundQueue.PlaySound('SharedMedia/Sounds/Incorrect.wav')
                        self.numSuccess = 0
                        self.numOK = 0
                        self.numFailures += 1
                        viz.clearcolor (1,0,0)
                self.movement.ResetNumMoves()
                self.endTrial(done)

        if self.movement != Movement:    # Are we using discrete motion keys?
            return
        
        if key in ('8','*'):
            if self.mode == 'TurnAround':
                SoundQueue.PlaySound('SharedMedia/Sounds/TurnAround.wav')
            elif self.movement.GoForward(self.fwdMovementCallback):
                self.outputMove('Forward')
        elif key in ('4',  'u',  'U'):
            if self.movement.RotateLeft():
                self.outputMove('Left')
        elif key in ('6',  'o',  'O'):
            if self.movement.RotateRight():
                self.outputMove('Right')
    
    def openCurtain(self):
        self.room.visible(viz.ON)
        self.cues.showAllCues(1)
        viz.visible(viz.ON)
        viz.clearcolor (0,0,0)
        self.curtain = 0
        if self.mode != 'TurnAround' and self.movement != Movement:
            self.movement.AllowMotion(forward=True)
        for name in self.envs.keys():
            if name != self.layout: 
                self.envs[name].visible(viz.OFF)
                for cue in self.envCues[name]:
                    cue.Object.visible(viz.OFF)

    def closeCurtain(self):
        self.room.visible(viz.OFF)
        self.cues.showAllCues(0)
        if self.mode != 'TurnAround' and self.movement != Movement:
            self.movement.AllowMotion(forward=False)
        viz.visible(viz.OFF)
        self.curtain = 1

    def resetTrain(self):
        self.movement.ResetNumMoves()
        HotSpots.ResetHotSpots(numtrials=None)

    def StartHotSpotQuiz(self,positionPair=None,directionFile=None,mode='HotspotQuiz'):
        self.mode=mode
        if self.mode=='EfficiencyTest': self.outputMove('EffTest')
        if self.mode=='HotspotQuiz': self.outputMove('HotSptQ')
        self.resetTrain()
        self.openCurtain()
        print 'StartHotSpotQuiz',positionPair,directionFile,mode
        if not positionPair:
            startPos = random.choice(HotSpots.GetHotSpots())+random.choice([0,90,180,270])
            endPos=None
        elif positionPair[0]==HotSpots.InHotSpot():
            startPos=self.movement.GetPlatPose()
            endPos=positionPair[1]
        else:
            startPos=HotSpots.GetHotSpot(positionPair[0])+random.choice([0,90,180,270])
            endPos=positionPair[1]
        print 'Moved to', self.movement.GetState(), 'Start:', startPos, 'End:',endPos
        self.directions=directionFile
        if directionFile:
            if not self.starttime: self.starttime=time.time()
            OUTFILE = open(self.logdir+self.outfile,'a')
            OUTFILE.write("DT Directions at time: %f\n"%(time.time()-self.starttime))
            OUTFILE.close()
            self.outputDirections(directionFile)
        if (self.mode=='Directions'):
            HotSpots.SoundOn(0)
        HotSpots.StartTrials(numtrials=1,callback=self.callback,startstate=startPos,targetHotspot=endPos,AnnounceLater=1)
        HotSpots.AnnounceHotSpots(0)

    def endTrial(self,done=0):
        HotSpots.SoundOn(1)
        if done or len(self.positionList)==0:
            if self.onFinish: self.onFinish(self)
            else:
                self.outputMove('HotSptQ')
                viz.quit()
        else: self.StartHotSpotQuiz(self.positionList.pop())
    
    def MoveToNext(self, hotspot, mode='TurnAround'):
        if mode == 'BoundedWander': HotSpots.StopTrials()
        self.closeCurtain()
        self.mode=mode
        x,y = HotSpots.GetHotSpot(hotspot)
        face = random.choice([0,90,180,270])
        print self.mode, "Moving to", x, y, face, self.numSuccess, self.numOK, self.numFailures
        self.outputMove('JumpNxt')
        self.movement.MoveTo(x, y, face)
        print self.mode, "Moved to", self.movement.GetVizCoords()
        self.jump=1

class HotSpotList:
    def __init__(self):
        self.reset()

    def __str__(self):
        return str([hs for hs in self.hotspots])

    def reset(self, hs=0):
        self.hotspots = {}
        if hs: self.mark(hs)

    def mark(self,hotspot):
        self.hotspots[hotspot] = True

    def __eq__(self,hotspots):
        for hs in hotspots:
            if hs not in self.hotspots: return False
        return True

    def all(self):
        return self == range(1,len(HotSpots.GetHotSpots())+1)

def generatePairs():
    # Constructed to have eash place as start and end
    # in each row, but not repeated within one set.
    Pairs=[[2,1],[4,3],[6,5],[1,7],[3,2],[5,4],[7,6],
           [1,5],[6,3],[4,1],[2,6],[7,4],[5,2],[3,7],
           [2,4],[1,3],[7,2],[4,6],[3,5],[6,1],[5,7],
           [6,4],[7,5],[3,1],[2,7],[4,2],[5,3],[1,6],
           [4,7],[6,2],[1,4],[3,6],[5,1],[7,3],[2,5],
           [7,1],[2,3],[4,5],[6,7],[1,2],[3,4],[5,6]]
    randint = random.randint(0,len(Pairs))
    Pairs = Pairs[randint:]+Pairs[:randint]
    if random.randint(0,1): Pairs.reverse()
    print Pairs
    return Pairs
