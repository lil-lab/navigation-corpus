# HexMovement.py
# $Revision: 1.1 $
# $Date: 2006/08/11 17:46:57 $

# Standard modules
import time, random, copy, math
from threading import *

# Third party modules
import viz

# Navigation modules
import Navigator

def GetTranslation( direction, distance=1 ):
	if direction == 30:
		yDiff = 0.866 * distance
		xDiff = 0.5 * distance
	elif direction == 90:
		yDiff = 0
		xDiff = distance
	elif direction == 150:
		yDiff = -0.866 * distance
		xDiff = 0.5 * distance
	elif direction == 210:
		yDiff = -0.866 * distance
		xDiff = -0.5 * distance
	elif direction == 270:
		yDiff = 0
		xDiff = -distance
	elif direction == 330:
		yDiff = 0.866 * distance
		xDiff = -0.5 * distance
	return (xDiff, yDiff)


# This is the class used to handle movement;
# it is hidden from users (a variable name with '__' in front of it is the
# closest thing in Python to a private variable).
# Functions for the user interface are defined below.
class __MOVEMENT_CLASS:
	def __init__(self,_x,_z,_angle,_scale,_speed,_center_offset):
		self.GO_FORWARD	    = -1 # GO_FORWARD, GO_SPIN, MISSKEY, NORMALIZE are constants
		self.GO_SPIN		= -2 # passed to the timer handler to specify the action
		self.MISSKEY		= -100
		self.NORMALIZE      = -500 
		self.FORWARD_SPEED 	= _speed / 60.0  # speed used for moving forward (meters/sec) (constant)
		self.BACKWARD_SPEED = self.FORWARD_SPEED  # speed used for moving backward (meters/sec) (constant)
		self.TURN_SPEED		= 2         # speed used for rotations (constant)
		self.EVENTS=[]  # timer callback functions
		self.doRotate=0 # i think this variable is not used, but i dont want to delete it just in case
		self.x = _x  # current x-coordinate
		self.y = 0.0 # current y-coordinate
		self.z = _z  # current z-coordinate
		self.angle = _angle # current angle
		self.currX = self.x
		self.currY = self.y
		self.currZ = self.z
		self.currAngle = 0
		self.center_offset = _center_offset
		self.scale = _scale # forward movement distance
		self.turnSpeed = 0.0 # rotation speed variable
		self.xSpeed = 0.0    # x-speed variable
		self.zSpeed= 0.0     # z-speed variable
		self.lastTime = 0 # time of last timer handling
		self.newTime = 0 # time of current timer handling
		self.moveDistance = 0 # measure distance moved during current action
		# move viz camera to proper position
		viz.reset(viz.HEAD_POS)
		viz.translate(viz.HEAD_POS, self.x, self.y, self.z)
		viz.reset(viz.BODY_ORI)
		viz.rotate(viz.BODY_ORI, self.angle, 0, 0)
		self.forwardmoves = 0 # number of forward actions
		self.backwardmoves = 0 # number of backward actions
		self.leftturns = 0 # number of left turn actions
		self.rightturns = 0 # number of right turn actions
		self.okMove = Lock() # is it okay for subject to make an action (i.e. are we currently moving)
		self.callback = None # callback function called at end of action
	# return total number of actions
	def GetNumTotalMoves(self):
		return self.forwardmoves + self.backwardmoves + \
				self.leftturns + self.rightturns
	# return total number of forward actions
	def GetNumForwardMoves(self):
		return self.forwardmoves
	# return total number of backward actions
	def GetNumBackwardMoves(self):
		return self.backwardmoves
	# return total number of left turn actions
	def GetNumLeftTurns(self):
		return self.leftturns
	# return total number of right turn actions
	def GetNumRightTurns(self):
		return self.rightturns
	# reset the number of actions made
	def ResetNumMoves(self):
		self.forwardmoves = 0
		self.backwardmoves = 0
		self.leftturns = 0
		self.rightturns = 0
	# add a timer handler
	# since Movement uses viz timer callback function, any viz timer callbacks
	# unrelated to Movement must be registered through Movement.
	def AddTimerHandler(self,key,function):
		self.EVENTS.append((key,function))
	# handle a timer event (num is the event)
	def MovementTimer(self,num):
		self.newTime = time.time()
		deltaTime = (self.newTime-self.lastTime)/(1./60.)
		self.lastTime = self.newTime
		if num == self.GO_FORWARD:
			# going forward 
			xDistance=self.xSpeed * deltaTime
			zDistance=self.zSpeed * deltaTime
			self.currZ = self.currZ + zDistance
			self.currX = self.currX + xDistance
			self.moveDistance=self.moveDistance+(((xDistance)**2+(zDistance)**2)**0.5)
			# move camera forward
			viz.reset(viz.HEAD_POS)
			viz.translate(viz.HEAD_POS, self.currX, self.currY, self.currZ)
			if  self.moveDistance < self.scale:
				# keep moving forward
				viz.starttimer(self.GO_FORWARD)
			else:
				# done moving forward, normalize current position
				(xDiff, zDiff) = GetTranslation( self.angle, self.scale )
				self.x += xDiff
				self.z += zDiff

				viz.reset(viz.HEAD_POS)
				viz.translate(viz.HEAD_POS, self.x, self.y, self.z)
				viz.starttimer(self.NORMALIZE)
		elif num == self.MISSKEY :
			print 'Misskey??????????????????'
		elif num == self.GO_SPIN:
			# do rotation
			if abs(self.currAngle) < 60:
				self.currAngle = self.currAngle + self.turnSpeed * deltaTime
				if abs(self.currAngle) < 60:
					viz.reset(viz.BODY_ORI)
					viz.rotate(viz.BODY_ORI, self.angle + self.currAngle, 0, 0)

					# Lazy Susan rotation:
					#   math's sin/cos use radians, so must convert from degrees.
					#   Also, math's angles are offset from viz's by 90 degrees, so use sin for x, cos for z
					radians = (self.angle + self.currAngle) * math.pi / 180.0
					xOff = -math.sin(radians) * self.center_offset
					zOff = -math.cos(radians) * self.center_offset
					viz.reset(viz.HEAD_POS)
					viz.translate(viz.HEAD_POS, self.currX + xOff, self.y, self.currZ + zOff)
					
				# keep rotating
				viz.starttimer(self.GO_SPIN)
			else:
				# done rotating, normalize angle
				self.angle += self.currAngle
				rounded = (self.angle + 30) / 60.0
				rounded = round( rounded ) * 60
				self.angle = (int( rounded ) - 30) % 360
				viz.reset(viz.BODY_ORI)
				viz.rotate(viz.BODY_ORI, self.angle, 0, 0)

				# Back the camera up a little to give a wider view.
				(xOff, zOff) = GetTranslation( self.angle, self.center_offset )
				self.x = self.currX - xOff
				self.z = self.currZ - zOff

				viz.reset(viz.HEAD_POS)
				viz.translate(viz.HEAD_POS, self.x, self.y, self.z)
				
				viz.starttimer(self.NORMALIZE)
		elif num == self.NORMALIZE:
			self.currAngle = 0
			self.currX = self.x
			self.currZ = self.z
			self.okMove.release()
			if self.callback:
				self.callback()
			self.callback = None
		else:
			# call handler for some other timer event
			for (key,func) in self.EVENTS:
				if num == key:
					func()
	# move to a new location
	def MoveTo(self,_x,_z,_angle):
		if  self.okMove.acquire(0):
			# Initialize the state from parameters.
			self.x = _x
			self.z = _z
			self.angle = _angle

			# Back the camera up a little to give a wider view.
			(xOff, zOff) = GetTranslation( self.angle, self.center_offset )
			self.x -= xOff
			self.z -= zOff

			# reset variables
			self.doRotate=0
			self.moveDistance = 0
			self.currAngle = 0
			self.currX = self.x
			self.currZ = self.z
			self.callback = None

			# Move the camera in Vizard.
			viz.reset(viz.HEAD_POS)
			viz.translate(viz.HEAD_POS, self.x, self.y, self.z)
			viz.reset(viz.BODY_ORI)
			viz.rotate(viz.BODY_ORI, self.angle, 0, 0)
			viz.starttimer(self.NORMALIZE)
	# Move Forward (call callback when done moving)
	def GoForward(self,callback=None):
		if self.okMove.acquire(0):
			self.forwardmoves+=1
			self.callback = callback
			self.lastTime = time.time()
			self.moveDistance=0

			(self.xSpeed, self.zSpeed) = GetTranslation( self.angle, self.FORWARD_SPEED )

			self.currX=self.x
			self.currZ=self.z
			viz.starttimer(self.GO_FORWARD)
			return 1
		else: return 0
#	# Move Backward (call callback when done moving)
#	def GoBackward(self,callback=None):
#		if self.okMove.acquire(0):
#			self.backwardmoves+=1
#			self.callback = callback
#			self.lastTime = time.time()
#			self.moveDistance=0
#			if 0 == self.angle:
#				self.xSpeed=0
#				self.zSpeed=-self.BACKWARD_SPEED
#			if 90 == self.angle:
#				self.xSpeed=-self.BACKWARD_SPEED
#				self.zSpeed=0
#			if 180== self.angle:
#				self.xSpeed = 0
#				self.zSpeed=self.BACKWARD_SPEED
#			if 270== self.angle:
#				self.xSpeed=self.BACKWARD_SPEED
#				self.zSpeed=0
#			self.currX=self.x
#			self.currZ=self.z
#			viz.starttimer(self.GO_FORWARD)
#			return 1
#		else: return 0
	def PerformTurn(self,callback=None):
		self.callback = callback
		self.moveDistance=0
		self.lastTime = time.time()
		self.currAngle=0

		# Undo the camera offset to find the actual coordinates of the state.
		# These are the coordinates the camera will rotate around.
		(xOff, zOff) = GetTranslation( self.angle, self.center_offset )
		self.currX = self.x + xOff
		self.currZ = self.z + zOff

		viz.starttimer(self.GO_SPIN)
	# Rotate left (call callback when done moving)
	def RotateLeft(self,callback=None):
		if self.okMove.acquire(0):
			self.leftturns+=1
			self.turnSpeed = -self.TURN_SPEED
			#self.setLeftTurnSpeeds()
			self.PerformTurn(callback)
			return 1
		else: return 0
		# Rotate Right (call callback when done moving)
	def RotateRight(self,callback=None):
		if self.okMove.acquire(0):
			self.rightturns+=1
			self.turnSpeed = self.TURN_SPEED
			#self.setRightTurnSpeeds()   
			self.PerformTurn(callback)
			return 1
		else: return 0

####################################################################
__MOVEMENT_VAR = None # static __MOVEMENT_CLASS object
__MAP_SIZE = None # Map size


# Utility functions (hidden from user) defined below

# Convert an angle in degrees to the Hex direction format which just uses 
# the numbers 0 through 5 to represent the four cardinal directions.
#def __DegreesToHexDirection(angle):
#	
#	# If the angle is approximately 0 degrees
#	if (angle > -10 and angle < 10) or (angle > 350 and angle < 370): 
#		return 0
#	# If the angle is approximately 90 degrees
#	elif angle > 80 and angle < 100:
#		return 2
#	# If the angle is approximately 180 degrees
#	elif angle > 170 and angle < 190:
#		return 3
#	# Default to 270 degrees
#	else:
#		return 0


# User Interface functions defined below 

# Initialize the module, must call before using other functions
# LayoutFile is a text map of the layout (used so you can't go through walls)
# scale is the distance moved during one forward action (default is 40)
def Init(scale=4, speed=None, center_offset=0):
	global __MOVEMENT_VAR, __MAP_SIZE
	if not speed: speed = scale
	__MOVEMENT_VAR = __MOVEMENT_CLASS(0,0,0,scale,speed,center_offset)
	viz.eyeheight(0.7)
	viz.setfov(70,1)
	viz.mouse(viz.OFF) # don't want mouse input
	viz.callback(viz.TIMER_EVENT, TimerCallback)
	__MAP_SIZE = (5, 10)

def TimerCallback(num):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.AddTimerHandler ******\nMovement.Init must be called before using this function.\n"
	__MOVEMENT_VAR.MovementTimer(num)

# register a timer callback function. event must be an integer >= 0.
def AddTimerHandler(event,function):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.AddTimerHandler ******\nMovement.Init must be called before using this function.\n"
	if event<0:
		raise "\n****** Error in Movement.AddTimerHandler ******\nEvent number must be greater than or equal to 0\n"
	__MOVEMENT_VAR.AddTimerHandler(event,function)

# returns 1 if subject can make an action, 0 otherwise
def OkMove():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.OkMove ******\nMovement.Init must be called before using this function.\n"
	return not __MOVEMENT_VAR.okMove.locked()

# returns the current state as a triple of (x,y,angle) (x,y are Hex coordinates)
def GetState():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetState ******\nMovement.Init must be called before using this function.\n"
	x, y = GetHexCoords()
	return (x,y,GetOrientation())

# return the current as a tuple of Hex coordinates (x,y)
def GetHexCoords():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetHexCoords ******\nMovement.Init must be called before using this function.\n"
	x,z = GetVizCoords()
	return (int(round(x/__MOVEMENT_VAR.scale)),int(round(-z/__MOVEMENT_VAR.scale)))

# set the current as a tuple of Hex coordinates (x,y)
def SetHexCoords( (x, z) ):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.SetHexCoords ******\nMovement.Init must be called before using this function.\n"
	SetVizCoords( (x * __MOVEMENT_VAR.scale, z * -__MOVEMENT_VAR.scale) )

# return the current orientation in degrees
def GetOrientation():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetCoords ******\nMovement.Init must be called before using this function.\n"
	if OkMove():
		return int(round(__MOVEMENT_VAR.angle))
	else:
		return int(round((__MOVEMENT_VAR.angle + __MOVEMENT_VAR.currAngle)%360))

# return the current position in viz coordinates (x,z)
def GetVizCoords():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetCoords ******\nMovement.Init must be called before using this function.\n"
	if OkMove():
		return (__MOVEMENT_VAR.x,__MOVEMENT_VAR.z)
	else:
		return (__MOVEMENT_VAR.currX,__MOVEMENT_VAR.currZ)

# return the current position in vrut (viz) coordinates (x,z)
# This function is deprecated and is provided only for backwards compatibility.
# GetVizCoords() should be used instead.
def GetVrutCoords():
	return GetVizCoords()

# set the current position in Vizard coordinates (x,z)
def SetVizCoords( (x, z) ):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.SetVizCoords ******\nMovement.Init must be called before using this function.\n"
	__MOVEMENT_VAR.x = x
	__MOVEMENT_VAR.z = z

# move to a new location specified by (x,y,angle) (x,y are Hex coordinates)
def MoveTo(x,y,angle):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.MoveTo ******\nMovement.Init must be called before using this function.\n"
	__MOVEMENT_VAR.ResetNumMoves()
	# Todo: don't hardcode this
	__MOVEMENT_VAR.MoveTo( \
			0.866 * \
			x*__MOVEMENT_VAR.scale,-y*__MOVEMENT_VAR.scale,angle)

# move forward (if you won't go through a wall); call callback when action finished
# returns 1 if can move forward, 0 otherwise
def GoForward(callback=None):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GoForward ******\nMovement.Init must be called before using this function.\n"
	if CanMoveForward()!=0:
		return __MOVEMENT_VAR.GoForward(callback)
	else:
		return 0

# move backward (if you won't go through a wall); call callback when action finished
# returns 1 if can move backward, 0 otherwise
def GoBackward(callback=None):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GoBackward ******\nMovement.Init must be called before using this function.\n"
	if CanMoveBackward()!=0:
		return __MOVEMENT_VAR.GoBackward(callback)
	else:
		return 0

# rotate right; call callback when action finished     
def RotateRight(callback=None):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.RotateRight ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.RotateRight(callback)

# rotate left; call callback when action finished	
def RotateLeft(callback=None):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.RotateLeft ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.RotateLeft(callback)

# return 1 if can move forward from pos (x,y,angle), 0 otherwise
# pos should be None if pos is the current position
# pos should be in Hex coordinates
def CanMoveForward(pos=None):
#	global __MOVEMENT_VAR, __PLAT_VAR
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.CanMoveForward ******\nMovement.Init must be called before using this function.\n"
	try:
		if pos:
			(x, z, t) = pos
		else:
			(x, z, t) = GetState()
		# Check if we're moving out of bounds.
		#   Todo

		# If there's a move in progress, we can't start another.
		return not __MOVEMENT_VAR.okMove.locked()
	except:
		return None

# return 1 if canmove backward from pos (x,y,angle), 0 otherwise
# pos should be None if pos is the current position
# pos should be in PLAT coordinates
#def CanMoveBackward(pos=None):
#	global __MOVEMENT_VAR, __PLAT_VAR
#	if __MOVEMENT_VAR==None:
#		raise "\n****** Error in Movement.CanMoveBackward******\nMovement.Init must be called before using this function.\n"
#	try:
#		if pos:
#			x,z,t = pos
#		else:
#			x,z = GetHexCoords()
#			t = int(__MOVEMENT_VAR.angle)
#		# To see if we can move backward, 
#		# test if we can rotate 180 degrees, then move forward.
#		t = (t + 180) % 360
#		HexPos = ( x, z, __DegreesToHexDirection(t) )
#		return __PLAT_VAR.CheckIfValidMove(HexPos, 'Forward') and not __MOVEMENT_VAR.okMove.locked()
#	except:
#		return None

# return total number of actions    
def GetNumTotalMoves():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumTotalMoves ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumTotalMoves()

# return total number of forward actions
def GetNumForwardMoves():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumForwardMoves ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumForwardMoves()

# return total number of backward actions
def GetNumBackwardMoves():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumBackwardMoves ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumBackwardMoves()

# return total number of left turns
def GetNumLeftTurns():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumLeftTurns ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumLeftTurns()

# return total number of right turns
def GetNumRightTurns():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumRightTurns ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumRightTurns()

# reset number of actions
def ResetNumMoves():
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Movement.ResetNumMoves ******\nMovement.Init must be called before using this function.\n"
	__MOVEMENT_VAR.ResetNumMoves()

## return view from pos (current position if pos==None)
## pos should be (x,y,theta) (x,y are Hex coordinates)
#def GetView(pos=None):
#	global __MOVEMENT_VAR, __PLAT_VAR
#	if __MOVEMENT_VAR==None:
#		raise "\n****** Error in Movement.GetView ******\nMovement.Init must be called before using this function.\n"
#	try:
#		if pos:
#			x,z,t = pos
#		else:
#			x,z = GetHexCoords()
#			t = int(__MOVEMENT_VAR.angle)
#		HexPos = ( x, z, __DegreesToHexDirection(t) )
#		return copy.deepcopy(__PLAT_VAR.Nodes[HexPos[0]][HexPos[1]].View[HexPos[2]])
#	except:
#		return None

# returns the current version of the module
def GetVersion():
	import re
	m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.1 $')
	if m:
		return m.group(1)
	else:
		return None
