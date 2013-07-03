# Movement.py
# $Revision: 1.4 $
# $Date: 2006/12/01 21:22:54 $
"""Move the subject through the environment.

Initialize by calling the Init function. If the LayoutFile parameter is specified during the
initialization, then the module will know the structure of the environment, and will be able to prevent
the subject from walking through walls and also be able to return the subject's view of the environment
from a given position (see CanMoveForward and GetView).

The Movement module uses the Vizard timer handler, so if you also need use the Vizard timer handler for
some reason, you must use the AddTimerHandler function to register the callback function and timer event
ID number.

GoForward, RotateRight, and RotateLeft move the subject's view through the environment. If a callback
function is given as a parameter when these functions are called, the callback function will be executed
when the action is completed.

MoveTo can be used to initialize the subject's state in the environment.
GetState can be used to get the subject's current state."""

import Navigator
import viz, time,string,random,copy,math
from threading import *

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
		#self.y = -1.8 # current y-coordinate
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
		self.xOffset = 0.0   # x-offset (used for Lazy Susan Rotation)
		self.zOffset = 0.0   # z-offset (used for Lazy Susan Rotation)  
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
		self.okMove = Lock() # 1 iff okay for subject to make an action (i.e. not currently moving)
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
				if self.zSpeed>0:
					self.z=self.z+self.scale
				elif self.zSpeed<0:
					self.z=self.z-self.scale
				elif self.zSpeed==0:
					self.z=self.z

				if self.xSpeed>0:
					self.x=self.x+self.scale
				elif self.xSpeed<0:
					self.x=self.x-self.scale
				elif self.xSpeed==0:
					self.x=self.x
					
				viz.reset(viz.HEAD_POS)
				viz.translate(viz.HEAD_POS, self.x, self.y, self.z)
				viz.starttimer(self.NORMALIZE)
		elif num == self.MISSKEY :
			print 'Misskey??????????????????'
		elif num == self.GO_SPIN:
			# do rotation
			if abs(self.currAngle) < 90:
				self.currAngle = self.currAngle + self.turnSpeed * deltaTime
				if abs(self.currAngle) < 90:
					viz.reset(viz.BODY_ORI)
					viz.rotate(viz.BODY_ORI, self.angle+self.currAngle, 0, 0)
					
					# Lazy Susan rotation:
					#   math's sin/cos use radians, so must convert from degrees.
					#   Also, math's angles are offset from viz's by 90 degrees, so use sin for x, cos for z
					radians = (self.angle+self.currAngle)*math.pi/180.0
					xoff = -math.sin(radians)*self.center_offset+self.xOffset
					zoff = -math.cos(radians)*self.center_offset+self.zOffset
					viz.reset(viz.HEAD_POS)
					viz.translate(viz.HEAD_POS, self.x+xoff, self.y, self.z+zoff)
					
				# keep rotating
				viz.starttimer(self.GO_SPIN)
			else:
				# done rotating, normalize angle
				self.angle+=self.currAngle
				self.angle=int(round(self.angle/90.0)*90) #Round to the nearest 90 degrees
				self.angle=self.angle%360
				viz.reset(viz.BODY_ORI)
				viz.rotate(viz.BODY_ORI, self.angle, 0, 0)

				if self.angle==0:
					self.x=self.currX
					self.z=self.currZ-self.center_offset
				elif self.angle==90:
					self.x=self.currX-self.center_offset
					self.z=self.currZ
				elif self.angle==180:
					self.x=self.currX
					self.z=self.currZ+self.center_offset
				elif self.angle==270:
					self.x=self.currX+self.center_offset
					self.z=self.currZ
				
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
			# reset variables
			self.doRotate=0
			self.x = _x
			self.z = _z
			self.angle = _angle
			if self.angle==0:
				self.z-=self.center_offset
			elif self.angle==90:
				self.x-=self.center_offset
			elif self.angle==180:
				self.z+=self.center_offset
			elif self.angle==270:
				self.x+=self.center_offset
			self.moveDistance = 0
			self.currAngle = 0
			self.currX = self.x
			self.currZ = self.z
			viz.reset(viz.HEAD_POS)
			viz.translate(viz.HEAD_POS, self.x, self.y, self.z)
			viz.reset(viz.BODY_ORI)
			viz.rotate(viz.BODY_ORI, self.angle, 0, 0)
			viz.starttimer(self.NORMALIZE)
			self.callback = None
	# Move Forward (call callback when done moving)
	def GoForward(self,callback=None):
		if self.okMove.acquire(0):
			self.forwardmoves+=1
			self.callback = callback
			self.lastTime = time.time()
			self.moveDistance=0
			if 0 == self.angle:
				self.xSpeed=0
				self.zSpeed=self.FORWARD_SPEED
			if 90 == self.angle:
				self.xSpeed=self.FORWARD_SPEED
				self.zSpeed=0
			if 180== self.angle:
				self.xSpeed = 0
				self.zSpeed=-self.FORWARD_SPEED
			if 270== self.angle:
				self.xSpeed=-self.FORWARD_SPEED
				self.zSpeed=0
			self.currX=self.x
			self.currZ=self.z
			viz.starttimer(self.GO_FORWARD)
			return 1
		else: return 0
	# Move Backward (call callback when done moving)
	def GoBackward(self,callback=None):
		if self.okMove.acquire(0):
			self.backwardmoves+=1
			self.callback = callback
			self.lastTime = time.time()
			self.moveDistance=0
			if 0 == self.angle:
				self.xSpeed=0
				self.zSpeed=-self.BACKWARD_SPEED
			if 90 == self.angle:
				self.xSpeed=-self.BACKWARD_SPEED
				self.zSpeed=0
			if 180== self.angle:
				self.xSpeed = 0
				self.zSpeed=self.BACKWARD_SPEED
			if 270== self.angle:
				self.xSpeed=self.BACKWARD_SPEED
				self.zSpeed=0
			self.currX=self.x
			self.currZ=self.z
			viz.starttimer(self.GO_FORWARD)
			return 1
		else: return 0
	def PerformTurn(self,callback=None):
		self.callback = callback
		self.moveDistance=0
		self.lastTime = time.time()
		self.currAngle=0
		if 0 == self.angle:
			self.xOffset=0
			self.zOffset=self.center_offset
		if 90 == self.angle:
			self.xOffset=self.center_offset
			self.zOffset=0
		if 180 == self.angle:
			self.xOffset=0
			self.zOffset=-self.center_offset
		if 270 == self.angle:
			self.xOffset=-self.center_offset
			self.zOffset=0
		self.currX=self.x + self.xOffset
		self.currZ=self.z + self.zOffset
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
__PLAT_VAR = None # PLAT object


# Utility functions (hidden from user) defined below

# Convert an angle in degrees to the Plat direction format which just uses 
# the numbers 0 through 3 to represent the four cardinal directions.
def __DegreesToPlatDirection(angle):
	# If the angle is approximately 0 degrees
	if (angle > -10 and angle < 10) or (angle > 350 and angle < 370): 
		return 1
	# If the angle is approximately 90 degrees
	elif angle > 80 and angle < 100:
		return 2
	# If the angle is approximately 180 degrees
	elif angle > 170 and angle < 190:
		return 3
	# Default to 270 degrees
	else:
		return 0


# User Interface functions defined below 

def Init(LayoutFile=None,scale=4,speed=None,center_offset=0):
	"""
	Initialize the module. Must be called before any of the module functions can be called.

	Parameters:
	All parameters are optional.

	LayoutFile: <String> The name of the text file defining the map. If this parameter is
	provided, then the module will keep track of the subject's position in the layout and the subject will
	be prevented from moving through walls. This parameter must be given to use CanMoveForward and GetView.

	scale: <Float> The distance in meters between the center of two nodes in the environment. This is
	the distance that the subject will move when GoForward is called.

	speed: <Float> The speed that the subject will move forward in meters per second. If None, then
	the speed will be set to scale.

	center_offset: <Float> The distance in meters that the subject is separated from his axis of
	rotation. The axis of rotation is always the center of a node.

	Return Value: None.
	"""
	global __MOVEMENT_VAR, __PLAT_VAR
	if not speed: speed = scale
	__MOVEMENT_VAR = __MOVEMENT_CLASS(0,0,0,scale,speed,center_offset)
	viz.eyeheight(0.0)
	#viz.setfov(70,1)
	viz.mouse(viz.OFF) # don't want mouse input
	viz.callback(viz.TIMER_EVENT, TimerCallback)
	if LayoutFile:
		try:
			# use __PLAT_VAR to hold info about LayoutFile
			width, height, size = Navigator.getPlatDim(LayoutFile)
			__PLAT_VAR = Navigator.PLAT(width,height,size)
			__PLAT_VAR.ReadTextImage(LayoutFile)
			__PLAT_VAR.ComputeAllViews(100)
		except:
			__PLAT_VAR = None
			raise ("\n****** Error in Movement.Init ******\nUnable to initialize Plat Object with '%s'\n"%LayoutFile)

def TimerCallback(num):
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.AddTimerHandler ******\nMovement.Init must be called before using this function.\n"
	__MOVEMENT_VAR.MovementTimer(num)

def AddTimerHandler(event,function):
	"""
	Register a Timer Handler with Vizard: any timer events must be registered with this to avoid conflicts.

	Parameters:
	event: <Integer> The timer event's ID number. Must be an integer greater than or equal to zero.

	function: <Function Pointer> The function that is called when the timer event occurs.

	Return Value: None.
	"""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.AddTimerHandler ******\nMovement.Init must be called before using this function.\n"
	if event<0:
		raise "\n****** Error in Movement.AddTimerHandler ******\nEvent number must be greater than or equal to 0\n"
	__MOVEMENT_VAR.AddTimerHandler(event,function)

def OkMove():
	"""
	Return 1 if and only if the subject is allowed to make an action (if he is not currently executing some other action).
	"""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.OkMove ******\nMovement.Init must be called before using this function.\n"
	return not __MOVEMENT_VAR.okMove.locked()

def GetState():
	"""
	Return the subject's pose (x, y, orientiation). x and y are PLAT coordinates, orientation in degrees.
	"""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetState ******\nMovement.Init must be called before using this function.\n"
	x, y = GetPlatCoords()
	return (x,y,GetOrientation())

def GetPlatCoords():
	"""Return the subject's position as a tuple of PLAT coordinates (x, y)."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetPlatCoords ******\nMovement.Init must be called before using this function.\n"
	x,z = GetVizCoords()
	return (int(round(x/__MOVEMENT_VAR.scale)),int(round(-z/__MOVEMENT_VAR.scale)))

def SetPlatCoords( (x, z) ):
	"""Set the current position from a tuple of PLAT coordinates (x,y)."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.SetPlatCoords ******\nMovement.Init must be called before using this function.\n"
	SetVizCoords( (x * __MOVEMENT_VAR.scale, z * -__MOVEMENT_VAR.scale) )

def GetPlatPose():
	"""Return the subject's pose as a tuple of PLAT coordinates and orientation (x, y, t)."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetPlatCoords ******\nMovement.Init must be called before using this function.\n"
	return GetPlatCoords()+(GetOrientation(),)

def GetOrientation():
	"""Return the current orientation in degrees."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetCoords ******\nMovement.Init must be called before using this function.\n"
	if OkMove():
		return int(round(__MOVEMENT_VAR.angle))
	else:
		return int(round((__MOVEMENT_VAR.angle + __MOVEMENT_VAR.currAngle)%360))

def GetVizCoords():
	"""Return the current position in viz coordinates (x,z)."""
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
GetVrutCoords = GetVizCoords

def SetVizCoords( (x, z) ):
	"""Set the current position in vrut coordinates (x,z)."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.SetVizCoords ******\nMovement.Init must be called before using this function.\n"
	__MOVEMENT_VAR.x = x
	__MOVEMENT_VAR.z = z

def MoveTo(x,y,angle):
	"""Move to a new location specified by (x,y,angle) (x,y are PLAT coordinates, angle is degrees)."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.MoveTo ******\nMovement.Init must be called before using this function.\n"
	__MOVEMENT_VAR.ResetNumMoves()
	__MOVEMENT_VAR.MoveTo(x*__MOVEMENT_VAR.scale,-y*__MOVEMENT_VAR.scale,angle)

def GoForward(callback=None):
	"""Move the subject forward by `scale' units.  Returns 1 if the action was successful and 0 otherwise.

	Will fail if another action is being executed, or if the LayoutFile parameter was specified and the
	subject attempted to walk through a wall.

	If a callback function is provided, it will be invoked once the action is successfully completed."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GoForward ******\nMovement.Init must be called before using this function.\n"
	if CanMoveForward():
		return __MOVEMENT_VAR.GoForward(callback)
	else:
		return 0

def GoBackward(callback=None):
	"""Move the subject backward by `scale' units.  Returns 1 if the action was successful and 0 otherwise.

	Will fail if another action is being executed, or if the LayoutFile parameter was specified and the
	subject attempted to walk through a wall.

	If a callback function is provided, it will be invoked once the action is successfully completed."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GoBackward ******\nMovement.Init must be called before using this function.\n"
	if CanMoveBackward():
		return __MOVEMENT_VAR.GoBackward(callback)
	else:
		return 0

def RotateRight(callback=None):
	"""Rotate the subject clockwise by 90 degrees.  Returns 1 if the action was successful and 0 otherwise.

	Will fail if another action is being executed.

	If a callback function is provided, it will be invoked once the action is successfully completed."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.RotateRight ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.RotateRight(callback)

def RotateLeft(callback=None):
	"""Rotate the subject counter-clockwise by 90 degrees.  Returns 1 if the action was successful and 0 otherwise.

	Will fail if another action is being executed.

	If a callback function is provided, it will be invoked once the action is successfully completed."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.RotateLeft ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.RotateLeft(callback)

def CanMoveForward(pos=None):
	"""Test whether or not the subject can move forward from position `pos' or subject's current state if pos is None.

	The subject cannot move forward if an action is currently being executed or if LayoutFile was
	specified in Init and there is a wall directly in front of pos.

	Parameters:
	pos: <Tuple (x, y, angle)>, x and y are PLAT coordinates, angle is orientation in degrees.
	"""
	global __MOVEMENT_VAR, __PLAT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.CanMoveForward ******\nMovement.Init must be called before using this function.\n"
	try:
		if pos:
			x,z,t = pos
		else:
			x,z = GetPlatCoords()
			t = int(__MOVEMENT_VAR.angle)
		platPos = ( x, z, __DegreesToPlatDirection(t) )
		return __PLAT_VAR.CheckIfValidMove(platPos, 'Forward') and not __MOVEMENT_VAR.okMove.locked()
	except:
		return None

def CanMoveBackward(pos=None):
	"""Test whether or not the subject can move backward from position `pos' or subject's current state if pos is None.

	The subject cannot move backward if an action is currently being executed or if LayoutFile was
	specified in Init and there is a wall directly behind pos.

	Parameters:
	pos: <Tuple (x, y, angle)>, x and y are PLAT coordinates, angle is orientation in degrees.
	"""
	global __MOVEMENT_VAR, __PLAT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.CanMoveBackward******\nMovement.Init must be called before using this function.\n"
	try:
		if pos:
			x,z,t = pos
		else:
			x,z = GetPlatCoords()
			t = int(__MOVEMENT_VAR.angle)
		# To see if we can move backward, 
		# test if we can rotate 180 degrees, then move forward.
		t = (t + 180) % 360
		platPos = ( x, z, __DegreesToPlatDirection(t) )
		return __PLAT_VAR.CheckIfValidMove(platPos, 'Forward') and not __MOVEMENT_VAR.okMove.locked()
	except:
		return None

def GetNumTotalMoves():
	"""Return total number of actions since Init or ResetNumMoves was last called."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumTotalMoves ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumTotalMoves()

def GetNumForwardMoves():
	"""Return number of forward moves since Init or ResetNumMoves was last called."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumForwardMoves ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumForwardMoves()

def GetNumBackwardMoves():
	"""Return number of backward moves since Init or ResetNumMoves was last called."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumBackwardMoves ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumBackwardMoves()

def GetNumLeftTurns():
	"""Return number of left turns since Init or ResetNumMoves was last called."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumLeftTurns ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumLeftTurns()

def GetNumRightTurns():
	"""Return number of right turns since Init or ResetNumMoves was last called."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetNumRightTurns ******\nMovement.Init must be called before using this function.\n"
	return __MOVEMENT_VAR.GetNumRightTurns()

def ResetNumMoves():
	"""Reset the number of forward, left-turn, and right-turn actions the subject has made to 0."""
	global __MOVEMENT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Movement.ResetNumMoves ******\nMovement.Init must be called before using this function.\n"
	__MOVEMENT_VAR.ResetNumMoves()

def GetView(pos=None):
	"""Return the subject;s view of the structure of the environment from pose `pos' or subject's current state if pos is None.

	The LayoutFile parameter must have been set in Init to get the view, otherwise return None.

	The view is described by a string composed of the following:
	'Fc'=forward corridor, 'Fw'=forward wall, 'Rc'=right corridor, 'Rw'=right wall, 'Lc'=left corridor, 'Lw'=left wall

	Starting with the structure directly in front of the subject and describing each junction and corridor
	along the hall in front until it reaches a wall ('Fw') obstructing the subject's view.  For example,
	if the subject is standing in front of a T-junction, the view will be described as 'FcRcLcFw'.
	"""
	global __MOVEMENT_VAR, __PLAT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetView ******\nMovement.Init must be called before using this function.\n"
	try:
		if pos:
			x,z,t = pos
		else:
			x,z = GetPlatCoords()
			t = int(__MOVEMENT_VAR.angle)
		platPos = ( x, z, __DegreesToPlatDirection(t) )
		return copy.deepcopy(__PLAT_VAR.Nodes[platPos[0]][platPos[1]].View[platPos[2]])
	except:
		return None

def GetPlatObj():
	"""Return the PLAT object used by the Movement module. This is the actual PLAT object, not a copy, so be careful."""
	global __MOVEMENT_VAR, __PLAT_VAR
	if __MOVEMENT_VAR==None:
		raise "\n****** Error in Movement.GetPlatObj ******\nMovement.Init must be called before using this function.\n"
	return __PLAT_VAR

def GetVersion():
	"""Return the current version of the module."""
	import re
	m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.4 $')
	if m:
		return m.group(1)
	else:
		return None

def ExtractLayoutScale(wrlFile):
	"""Return the scale of the wrl file, from the filename `wrlFile'.
    
	The scale is the distance in meters between the centers of two nodes in the environment."""
	if wrlFile:
		try:
			WRLFILE = open(wrlFile, 'r')
			line = WRLFILE.readlines()[1]
			WRLFILE.close()
		except:
			raise "\n****** Error in Movement.ExtractLayoutScale ******\n"\
				"Could not open layout wrl file: %s.\n" % (wrlFile)
	else:
		raise "\n****** Error in Movement.ExtractLayoutScale ******\n"\
			"Must provide a layout wrl file.\n"
	words = line.split()
	width = string.atof(words[1])
	length = string.atof(words[3])
	return width + length
