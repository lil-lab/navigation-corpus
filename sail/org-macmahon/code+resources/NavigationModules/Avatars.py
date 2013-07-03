# Avatars.py
# $Revision: 1.3 $
# $Date: 2006/01/13 18:13:56 $

import random
import viz
import Joystick

WALK_SCALE = 1.7
VERTICAL_OFFSET = -0.48
DEFAULT_MOVE_PROBABILITY = (0.4, 0.25, 0.25, 0.1, 0)
LOITER_ONLY_MOVE_PROBABILITY = (0, 0, 0, 0, 1)
layoutScale = 4.0

# Takes an experiment "state" in the form, (x, z, angle), where x and z are 
# measured in intersections.  Converts this to a vizard position (in meters) 
# and rotation (in euler angle).
def __state2viz( state ):
	global layoutScale
	pos = (layoutScale * state[0], VERTICAL_OFFSET, -1 * layoutScale * state[1])
	rot = (state[2], 0, 0)
	return (pos, rot)

# Takes the viz.POSITION and viz.AXISANGLE of an object and converts them 
# into the experiment's (x, z, angle) coordinate system (where x and z are 
# measured in number of intersections).  
# If round is true, the x and z values are rounded to the nearest intersection.
# If viz.AXISANGLE is not provided, angle will be None.  
def __viz2state( vizPosition, vizRotation = None, round = True ):
	global layoutScale
	# Convert the position
	x = vizPosition[0] / layoutScale
	z = -1 * vizPosition[2] / layoutScale
	# Round the position
	x = int(x + 0.5)
	z = int(z + 0.5)

	# Convert the rotation
	if vizRotation:
		if vizRotation[1] < 0:
			angle = 360 - vizRotation[3]
		else:
			angle = vizRotation[3]
	else:
		angle = None
	return (x, z, angle)

def SetLayoutScale( scale ):
	global layoutScale
	layoutScale = scale

def CreateAvatar( startLocation, avatarScale = 0.35, visible = viz.OFF ):
	avatar = viz.add( 'female.cfg' )

	avatar.destination = startLocation
	avatar.interrupted = "No"
	avatar.backupMoveProbability = None
	avatar.moveProbability = None

	(position, rotation) = __state2viz( startLocation )
	avatar.visible( visible )
	avatar.translate( position )
	avatar.rotate( rotation )
	avatar.scale( avatarScale, avatarScale, avatarScale )
	avatar.idlepose( 12 )
	return avatar

def MoveAvatar( avatar, dest, speed = WALK_SCALE ):
	(position, rotation) = __state2viz( dest )
	scale = avatar.get(viz.SCALE)
	walk = avatar.walkto( position[0], position[1], position[2], 
							speed * scale[0], 360, viz.AVATAR_WALKSTEP )
	avatar.clear(viz.ACTION)
	avatar.clear(viz.CURRENT_ACTION)
	avatar.act(walk)

def LoiterAvatar( avatar ):
	avatar.clear(viz.ACTION)
	avatar.clear(viz.CURRENT_ACTION)
	avatar.act( 12 )

def TemporaryStop( avatar ):
	avatar.clear(viz.ACTION)
	avatar.clear(viz.CURRENT_ACTION)
	avatar.interrupted = "Delay"
	if avatar.moveProbability and not avatar.backupMoveProbability:
		avatar.backupMoveProbability = avatar.moveProbability
	avatar.moveProbability = LOITER_ONLY_MOVE_PROBABILITY

# Move avatar down a random hallway.
# The probability of each direction is specified in moveProbability:
# (forward, left, right, back, loiter)
def MoveAvatarRandomly( avatar, moveProbability = None, speed = None ):
	global layoutScale

	if not moveProbability:
		if avatar.moveProbability:
			moveProbability = avatar.moveProbability
			if avatar.backupMoveProbability:
				avatar.moveProbability = avatar.backupMoveProbability
				avatar.backupMoveProbability = None
			else:
				avatar.moveProbability = None
		else:
			moveProbability = DEFAULT_MOVE_PROBABILITY

	# If the avatar's speed was not specified, 
	# randomly choose a speed.
	if not speed:
		speed = WALK_SCALE * random.uniform( 0.9, 1.1 )

	if avatar.interrupted == "Delay":
		avatar.interrupted = "Continue"
	elif avatar.interrupted == "Continue":
		MoveAvatar( avatar, avatar.destination, speed )
		avatar.interrupted = "No"
		return

	(intersCenter, rotation) = __state2viz( avatar.destination )

	# Build the list of valid directions.
	if moveProbability[4] > 0:
		validDirections = [None]
	else:
		validDirections = []
	for direction in range(0, 360, 90):
		testState = (intersCenter[0], intersCenter[2], direction)

		# Take a measurement above the heads of the other avatars.
		length = Joystick.getHallLength( testState, layoutScale, 0.3 )
		if length > 0:
			validDirections.append( direction )

	# Randomly pick the next movement for this avatar based on moveProbability.
	oldDirection = avatar.destination[2]
	directionProbs = {}
	if oldDirection in validDirections:
		directionProbs[oldDirection] = moveProbability[0]
	oldLeft = (oldDirection - 90) % 360
	if oldLeft in validDirections:
		directionProbs[oldLeft] = moveProbability[1]
	oldRight = (oldDirection + 90) % 360
	if oldRight in validDirections:
		directionProbs[oldRight] = moveProbability[2]
	oldBack = (oldDirection + 180) % 360
	if oldBack in validDirections:
		directionProbs[oldBack] = moveProbability[3]
	if None in validDirections:
		directionProbs[None] = moveProbability[4]
	normalize = sum( directionProbs.values() )
	randomNum = random.random() * normalize
	for (dir, prob) in directionProbs.items():
		if randomNum < prob:
			newDirection = dir
			break
		else:
			randomNum -= prob
	else:
		raise "Error choosing random direction."

	# Start the Avatar's next move.
	if newDirection == None:
		LoiterAvatar( avatar )
	else:
		x = avatar.destination[0]
		y = avatar.destination[1]
		if newDirection == 0:
			y -= 1
		elif newDirection == 90:
			x += 1
		elif newDirection == 180:
			y += 1
		elif newDirection == 270:
			x -= 1
		avatar.destination = (x, y, newDirection)
		offset = (random.uniform(-0.075, 0.075), random.uniform(-0.075, 0.075))
		destination = (x + offset[0], y + offset[1], newDirection)
		MoveAvatar( avatar, destination, speed )

def AvatarCallback( object, type, num ):
	MoveAvatarRandomly( object )

class AvatarList:
	def __init__( self ):
		self.avatars = []

	def addAvatar( self, avatar ):
		self.avatars.append( avatar )

	def createAvatars( self, locationList, visible = viz.OFF ):
		for loc in locationList:
			avatar = CreateAvatar( loc, visible = visible )
			self.addAvatar( avatar )

	def visible(self, state ):
		for avatar in self.avatars:
			avatar.visible( state )

	def removeAllAvatars( self ):
		for avatar in self.avatars:
			avatar.remove()
		self.avatars = []

	def startMovingAvatars( self ):
		for avatar in self.avatars:
			avatar.callback( viz.ACTION_END_EVENT, AvatarCallback )
			MoveAvatarRandomly( avatar )
