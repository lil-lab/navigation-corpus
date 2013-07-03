# Joystick.py
# $Revision: 1.14 $
# $Date: 2007/04/25 23:40:41 $

import viz, sid, math
import Movement

# Constants for distance measurement
DISTANCE_BUFFER = 32000
NUM_BEAMS = 20
DEGREES_BETWEEN_BEAMS = 1

# Constants for joystick movement
VERTICAL_POS = 0.0
DEFAULT_MAX_SPEED = 5.0
REAL_MAX_ROTSPEED = 150.0

# Utility functions
def findEndPoint( startPoint, angle, distance ):
    xBuffer = distance * math.sin(math.pi * angle / 180)
    zBuffer = distance * math.cos(math.pi * angle / 180)
    return [startPoint[0] + xBuffer, startPoint[1], startPoint[2] + zBuffer]

# This is the class used to handle joystick movement;
# it is hidden from users (a variable name with '__' in front of it is the
# closest thing in Python to a private variable).
# Functions for the user interface are defined below.
class InputHandler:
    def __init__( self, callbackFrequency, maxSpeed = DEFAULT_MAX_SPEED, 
                    joyCalFile = None, 
                    joystick = True, keyboard = False, mouse = False,
                    forward = True, backward = True, turn = True):
        self.JOY_MOVE_FREQUENCY = callbackFrequency
        self.REAL_MAX_SPEED = maxSpeed
        self.COLLISION_BUFFER = 5.0 * maxSpeed * callbackFrequency
        self.joystick = joystick
        self.keyboard = keyboard
        self.mouse = mouse
        self.forward = forward
        self.backward = backward
        self.turn = turn

        if joystick:
            if joyCalFile: self.LoadJoyCalFile( joyCalFile )
            else: self.LoadJoyCalFile()

        self.lastObjectIntersected = None
        viz.eyeheight(0.15)
        #viz.setfov(70,1)
        viz.mouse(viz.OFF) # don't want mouse input
        self.MoveTo([0,0,0])
        self.CONVERT_SPEED = maxSpeed
        self.CONVERT_ROTSPEED = REAL_MAX_ROTSPEED

    def UpdateCallbackFrequency( self, callbackFrequency ):
        self.JOY_MOVE_FREQUENCY = callbackFrequency
        self.COLLISION_BUFFER = 1.5 * self.REAL_MAX_SPEED * \
                                    self.JOY_MOVE_FREQUENCY

    def UpdateMaxSpeed( self, maxSpeed ):
        self.REAL_MAX_SPEED = maxSpeed
        self.COLLISION_BUFFER = 1.5 * self.REAL_MAX_SPEED * \
                                    self.JOY_MOVE_FREQUENCY

    def LoadJoyCalFile( self, joyCalFile = None ):
        if joyCalFile == None:
            # Set the default calibration file.
            # Find the path to this module.
            endpath = 1 + __file__.rfind('\\')
            path = __file__[:endpath]
            # Build the filename.
            joyCalFile = path + "joycal.dat"

        try:
            RUNFILE = open(joyCalFile, 'r')
        except:
            print "\n\n********************************************\n"\
                "Cannot open:\n\t%s\n"\
                "********************************************\n" % (joyCalFile)
            raise

        try:
            lines = RUNFILE.readlines()
        finally:
            RUNFILE.close()

        cal = lines[0].split()

        self.JOYSTICK_LEFT_X = float(cal[0])
        self.JOYSTICK_CENTER_X = float(cal[1])
        self.JOYSTICK_RIGHT_X = float(cal[2])
        self.JOYSTICK_FORWARD_Y = float(cal[3])
        self.JOYSTICK_CENTER_Y = float(cal[4])
        self.JOYSTICK_BACK_Y = float(cal[5])
        self.JOYSTICK_MIN_USEABLE = float(cal[6])
        self.JOYSTICK_MAX_USEABLE = float(cal[7])

        usableDiff = self.JOYSTICK_MAX_USEABLE - self.JOYSTICK_MIN_USEABLE
        self.CONVERT_SPEED = self.REAL_MAX_SPEED / usableDiff
        self.CONVERT_ROTSPEED = REAL_MAX_ROTSPEED / usableDiff

    # move to a new location
    def MoveTo( self, state ):
        f,b,t = self.forward, self.backward, self.turn
        self.forward = self.backward = self.turn = False
        viz.reset( viz.HEAD_POS )
        viz.translate( viz.HEAD_POS, state[0], VERTICAL_POS, state[1] )
        viz.reset( viz.BODY_ORI )
        viz.rotate( viz.BODY_ORI, state[2], 0, 0 )
        self.ResetNumMoves()
        self.forward, self.backward, self.turn = f,b,t
    
    def ResetNumMoves(self):
        self.fwdDistance = 0.0
        self.bwdDistance = 0.0
        self.rtDistance = 0.0
        self.ltDistance = 0.0

    def NormalizeJoystickPosition( self, pos ):
        if pos > self.JOYSTICK_MIN_USEABLE:
            if pos > self.JOYSTICK_MAX_USEABLE:
                pos = self.JOYSTICK_MAX_USEABLE
            return pos - self.JOYSTICK_MIN_USEABLE
        elif pos < -1 * self.JOYSTICK_MIN_USEABLE:
            if pos < -1 * self.JOYSTICK_MAX_USEABLE:
                pos = -1 * self.JOYSTICK_MAX_USEABLE
            return pos + self.JOYSTICK_MIN_USEABLE
        else:
            return 0

    epsilon = 0.0001
    def GetInput(self):
        input = None
        if self.joystick:
            delta_x,delta_y,buttons = sid.get()
            if abs(delta_x)>self.epsilon or abs(delta_y)>self.epsilon:
                input = 'JS'
                speed = self.NormalizeJoystickPosition( self.JOYSTICK_CENTER_Y - delta_y )
                rotspeed = self.NormalizeJoystickPosition( self.JOYSTICK_CENTER_X - delta_x )
        if not input and self.mouse and viz.buttonstate()&viz.MOUSEBUTTON_LEFT:
            delta_y,delta_x = viz.mousepos()
            if delta_x or delta_y:
                input = 'MS'
                speed = 2 * (delta_x - 0.5)
                rotspeed = -1 * (delta_y - 0.5)
        if not input and self.keyboard:
            delta_x = delta_y = 0
            if viz.iskeydown(viz.KEY_LEFT): delta_y = 1
            if viz.iskeydown(viz.KEY_RIGHT): delta_y = -1
            if viz.iskeydown(viz.KEY_DOWN): delta_x = -1
            if viz.iskeydown(viz.KEY_UP): delta_x = 1
            if delta_x or delta_y:
                input = 'KB'
                speed = delta_x * 2.0
                rotspeed = delta_y * 0.75
        if not input: return 0,0
        #print 'JoyStick.GetInput::', input, speed, rotspeed,
        #print self.fwdDistance,self.bwdDistance,self.rtDistance,self.ltDistance
        speed *= self.CONVERT_SPEED
        rotspeed *= -self.CONVERT_ROTSPEED
        return speed,rotspeed

    def UpdateLocation( self, state, slideAngle = 40 ):
        # Reset the record of the last object run into.
        self.lastObjectIntersected = None

        speed,rotspeed = self.GetInput()
        if speed == 0 and rotspeed == 0:
            return state
        newState = list(state)

        if speed != 0:
            startPos = [state[0], VERTICAL_POS, state[1]]
            if speed > 0: colBuf = self.COLLISION_BUFFER
            elif speed < 0: colBuf = -1 * self.COLLISION_BUFFER

            for angleOffset in range(0, slideAngle):
                driftAngle = state[2] + angleOffset
                intersObj = viz.intersect(startPos, findEndPoint( startPos, driftAngle, colBuf ))
                if not intersObj.intersected:
                    break;

                driftAngle = state[2] - angleOffset
                intersObj = viz.intersect(startPos, findEndPoint( startPos, driftAngle, colBuf ))
                if not intersObj.intersected:
                    break;
                elif not self.lastObjectIntersected:
                    # We've run into an object, record which object.
                    self.lastObjectIntersected = intersObj.object
            else: driftAngle = state[2]
        
        if (((speed > 0 and self.forward) or (speed < 0 and self.backward))
             and not intersObj.intersected):
            # Compute the new position.
            distance = speed * self.JOY_MOVE_FREQUENCY
            if distance > 0: self.fwdDistance += distance
            else: self.bwdDistance += distance
            newPosition = findEndPoint( startPos, driftAngle, distance )

            # Update the state.
            newState[0] = newPosition[0]
            newState[1] = newPosition[2]
            # Move to the new position.
            viz.reset( viz.HEAD_POS )
            viz.translate( viz.HEAD_POS, *newPosition )

        # rotation
        if rotspeed != 0 and self.turn:
            rotDistance = rotspeed * self.JOY_MOVE_FREQUENCY
            if rotDistance > 0: self.rtDistance += rotDistance
            else: self.ltDistance += rotDistance
            newState[2] = (state[2] + rotDistance) % 360
            viz.reset(viz.BODY_ORI)
            viz.rotate(viz.BODY_ORI, newState[2], 0, 0)

        return newState

####################################################################
__JOYSTICK_VAR = None # static __JOYSTICK_CLASS object

# User Interface functions defined below 

# Initialize the module, must call before using other functions
def Init( callbackFrequency, maxSpeed = DEFAULT_MAX_SPEED, joyCalFile = None, **kwargs ):
    global __JOYSTICK_VAR

    if not __JOYSTICK_VAR:
        __JOYSTICK_VAR = InputHandler( callbackFrequency, maxSpeed, joyCalFile, **kwargs)
    else:
        __JOYSTICK_VAR.UpdateMaxSpeed( maxSpeed )
        __JOYSTICK_VAR.UpdateCallbackFrequency( callbackFrequency )
        __JOYSTICK_VAR.LoadJoyCalFile( joyCalFile )
        for key,val in kwargs: setattr(__JOYSTICK_VAR,key,val)

def __CheckInit():
    global __JOYSTICK_VAR
    if __JOYSTICK_VAR == None:
        raise "\nJoystick.Init must be called before using this function.\n"

# move to a new location specified by (x,z,angle)
def MoveTo( state ):
    global __JOYSTICK_VAR
    __CheckInit()
    __JOYSTICK_VAR.MoveTo( state )

# Update the location based on the current joystick position.
def UpdateLocation( state ):
    global __JOYSTICK_VAR
    __CheckInit()
    return __JOYSTICK_VAR.UpdateLocation( state )

# Get the last object which was run into.  If an object UpdateLocation
def GetObjectIntersected():
    global __JOYSTICK_VAR
    __CheckInit()
    return __JOYSTICK_VAR.lastObjectIntersected

# returns the current version of the module
def GetVersion():
    import re
    m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.14 $')
    if m:
        return m.group(1)
    else:
        return None

def ExtractLayoutScale(wrlFile):
    try:
        WRLFILE = open(wrlFile, 'r')
        lines = WRLFILE.readlines()
        WRLFILE.close()
    except:
        print "\nCould not open layout wrl file: %s.\n" % (wrlFile)
        raise
    words = lines[1].split()
    width = float(words[1])
    length = float(words[3])
    return width + length

# Measure the distance to the end of the hall.
def getHallLength( state, hallScale, verticalOffset = 0.0 ):
    """Measure the distance to the end of the hall, rounded to the nearest
        number of hall lengths.  
        hallScale is the distance from the center of one intersection
        to the center of the next.
        verticalOffset is the offset from the head position at which the 
        measurement is taken."""

    # We compute the distance to the end of the hall by drawing a 
    # line straight in front of the camera and finding the first 
    # place it intersects a wall.  We use a horizontal spread of 
    # lines and take the max to account for the user possibly not 
    # facing straight down the hall.

    maxDist = 0
    startPos = [state[0], VERTICAL_POS + verticalOffset, state[1]]
    for i in range(0, NUM_BEAMS):
        curAngle = state[2] + (NUM_BEAMS/2 - i - 1/2) * DEGREES_BETWEEN_BEAMS
        endPos = findEndPoint( startPos, curAngle, DISTANCE_BUFFER )

        intersObj = viz.intersect(startPos, endPos)
        # dist = sqrt(x^2 + y^2 + z^2)  (y^2 isn't really needed for our case)
        dist = pow(pow(startPos[0] - intersObj.intersectPoint[0], 2) + 
                pow(startPos[2] - intersObj.intersectPoint[2], 2), 0.5)
        if dist > maxDist:
            maxDist = dist
            maxEndPos = intersObj.intersectPoint

    # Assume the camera is in the middle of the intersection.  It measures 
    # to the far edge of an intersection, so compensate for half an 
    # intersection.
    maxDist -= 0.45
    # Convert to the nearest number of intersections, then round to 
    # the nearest integer.
    maxDist = maxDist / hallScale
    maxDist = int((maxDist + 0.45))

    return maxDist

class ContinuousMovement:
    def __init__(self, x=0, y=0, angle=0, scale=4, 
                 speed=DEFAULT_MAX_SPEED, center_offset=0, callback=None, **kwargs):
        print 'Initializing Joystick.movement'
        global __JOYSTICK_VAR
        frequency = 0.01
        timer_id = 1
        self.motion = __JOYSTICK_VAR = InputHandler(frequency, speed*scale/8, **kwargs)
        self.scale = float(scale)
        self.callbacks = {timer_id: self.UpdateLocation}
        self.coords = (x, y, angle)
        self.callback = callback
        self.center_offset = center_offset
        viz.eyeheight(0.0)
        viz.setfov(70,1)
        viz.mouse(viz.OFF) # don't want vizard mouse navigation
        viz.callback(viz.TIMER_EVENT, self.TimerCallback)
        viz.starttimer(timer_id, frequency, -1)
    
    def UpdateLocation(self):
        platcoords = self.GetPlatCoords()
        self.coords = self.motion.UpdateLocation(self.coords)
        if self.callback and platcoords != self.GetPlatCoords():
            self.callback()
    
    def TimerCallback(self,num):
        try:
            self.callbacks[num]()
        except IndexError,msg:
            print 'Unknown Callback number in Movement.TimerCallback()', msg
    
    def AddTimerHandler(self,event,function):
        self.callbacks[event] = function
    
    def OkMove(self):
        return not self.motion.lastObjectIntersected

    def AllowMotion(self, **kwargs):
        for key,val in kwargs.items(): setattr(self.motion,key,val)

    def GetState(self):
        return self.GetPlatCoords()+(self.GetOrientation(),)
    
    def GetPlatCoords(self):
        x,z = self.GetVizCoords()
        return (int(round(x/self.scale)),int(round(-z/self.scale)))
    
    def SetPlatCoords(self,(x, z)):
        return self.SetVizCoords( (x*self.scale, z*-self.scale))
    
    def GetPlatPose(self):
        return self.GetPlatCoords()+(self.GetOrientation(),)
    
    def GetOrientation(self):
        return self.coords[2]
    
    def GetVizCoords(self):
        return self.coords[:2]
    
    def SetVizCoords(self,(x, y)):
        self.motion.MoveTo((x,y,0))
        self.coords = (x,y,0)
    
    def MoveTo(self,x,y,angle):
        vx,vy = (x*self.scale, -y*self.scale)
#        if angle==0:
#            vy -= self.center_offset
#        elif angle==90:
#            vx -= self.center_offset
#        elif angle==180:
#            vy += self.center_offset
#        elif angle==270:
#            vx += self.center_offset
        self.coords = (vx,vy,angle)
        print 'Joystick.MoveTo',x,y,angle,self.coords
        self.motion.MoveTo(self.coords)
    
    def GetNumTotalMoves(self):
        return (self.GetNumForwardMoves() + self.GetNumBackwardMoves()
                + self.GetNumLeftTurns() + self.GetNumRightTurns())
    
    def GetNumForwardMoves(self):
        return int(self.motion.fwdDistance / self.scale)
    
    def GetNumBackwardMoves(self):
        return int(self.motion.bwdDistance / self.scale)
    
    def GetNumLeftTurns(self):
        return int(self.motion.ltDistance / 90.0)
    
    def GetNumRightTurns(self):
        return int(self.motion.rtDistance / 90.0)
    
    def ResetNumMoves(self):
        self.motion.ResetNumMoves()
    
    def GetView(self,pos=None):
        pass
    
    def GetPlatObj(self):
        pass
    
    def GetVersion(self):
        return GetVersion()
    
    def ExtractLayoutScale(self,wrlFile):
        return ExtractLayoutScale(wrlFile)
