import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../sail/code')



from MarcoUtil import *

def robot_create(map_name, start_pos, direction = 0):
	'''
		Create a robot in a given map and position.
	'''
	pomdp = maps[map_name.lower()]()
	robot = Robot(pomdp, "test", RecognizerModule.PomdpAntiePeriphSimRecognizer)
	if isinstance(start_pos, int):
		x, y = pomdp.position2plat(start_pos)
	else:
		(x, y, direction) = start_pos
	# A direction of -1 means it's unspecified, so randomly select one
	if direction == -1:
		possibleDirections = [0, 90, 180, 270]
		random.shuffle(possibleDirections)
		direction = possibleDirections[0]
	#Doing the transformation from our representation to internal
	#MARCO representation
	place = robot.pomdp.plat2place(x, y)
	orientation = robot.pomdp.platdir2orient(direction)
	robot.pomdp.trueState = (place, orientation)
	return robot

def robot_state(robot):
	'''
		Returns the state of the robot.
	'''
	return robot.pomdp.state2plat(robot.pomdp.trueState), robot.pomdp.observe()

def robot_execute(robot, action):
	'''
		Execute an action given a specific robot
	'''
	p = Plan(actions = [action])
	initialState = robot.pomdp.state2plat(robot.pomdp.trueState)
	for a in p:
		a.execute(robot)
	newState = robot.pomdp.state2plat(robot.pomdp.trueState)
	print '%s -> %s' % (initialState, newState)

def implicit_demo_short():
	r = robot_create('l', (22, 17, 270))
	print '=== Robot state: ', robot_state(r)
	a = parse('with your back to the wall turn left')[0]
	print '=== Action to take: ', a
	robot_execute(r, a)
	print '=== Robot state: ', robot_state(r)

def implicit_demo_long():
	r = robot_create('jelly', (23, 16, 270))
	print '=== Robot state: ', robot_state(r)
	instruction = 'face and move to the hatrack. turn left and walk along the grass to the chair. turn left at the chair and turn right at the next interesection. turn left at the sofa chair and right at the next sofa chair.'
	print '=== Instruction: ', instruction
	plan = parse(instruction)
	for a in plan:
		print '=== Action to take: ', a
		#robot_execute(r,a)
		#print '=== Robot state: ', robot_state(r)

logger.initLogger('tester', LogDir = os.path.dirname(os.path.abspath(__file__)) + '/../sail/logs')
