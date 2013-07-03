"""Insturctions:
Repeat this sequence twice:
 Leave the joystick in the center and press button 3.
 Move the joystick all the way BACK and LEFT and press button 2.
 Move the joystick all the way FORWARD and LEFT and press button 4.
 Move the joystick all the way FORWARD and RIGHT and press button 5.
 Move the joystick all the way BACK and RIGHT and press trigger button.
 Start in the center and press button 3.
"""

# Standard libraries
import sid

JOYSTICK_LEFT_X = None
JOYSTICK_CENTER_X = None
JOYSTICK_RIGHT_X = None

JOYSTICK_FORWARD_Y = None
JOYSTICK_CENTER_Y = None
JOYSTICK_BACK_Y = None

JOYSTICK_MIN_USEABLE = 0.13
JOYSTICK_MAX_USEABLE = 0.53
Lefts = []
Rights = []
Forwards = []
Backs = []
Zeros_X = []
Zeros_Y = []
Samples = 2

def joystickButtonCallback( button ):
	global JOYSTICK_MIN_USEABLE, JOYSTICK_MAX_USEABLE

	data = sid.get()
	if button == 3: # Center
		Zeros_X.append(data[0])
		Zeros_Y.append(data[1])
		message = 'Now back left and button 2'
	elif button == 2:  # Back left
		Lefts.append(data[0])
		Backs.append(data[1])
		message = 'Now forward left and button 4'
	elif button == 4:  # Forward left
		Lefts.append(data[0])
		Forwards.append(data[1])
		message = 'Now forward right and button 5'
	elif button == 5:  # Forward right
		Rights.append(data[0])
		Forwards.append(data[1])
		message = 'Now back right and trigger button'
	elif button == 1:  # Back right
		Rights.append(data[0])
		Backs.append(data[1])
		message = 'Now center and button 3'

	if (len(Lefts) >= Samples and len(Rights) >= Samples
	    and len(Forwards) >= Samples and len(Backs) >= Samples
		and len(Zeros_X) >= Samples and len(Zeros_Y) >= Samples):
		JOYSTICK_LEFT_X = sum(Lefts)/len(Lefts)
		JOYSTICK_RIGHT_X = sum(Rights)/len(Rights)
		JOYSTICK_BACK_Y = sum(Backs)/len(Backs)
		JOYSTICK_FORWARD_Y = sum(Forwards)/len(Forwards)
		JOYSTICK_CENTER_Y = sum(Zeros_Y)/len(Zeros_Y)
		JOYSTICK_CENTER_X = sum(Zeros_X)/len(Zeros_X)
		for side,array,val in zip(['Left','Right','Back','Forward','Zero_X','Zero_Y'],
								  [Lefts, Rights, Backs, Forwards, Zeros_X, Zeros_Y],
								  [JOYSTICK_LEFT_X,JOYSTICK_RIGHT_X,JOYSTICK_BACK_Y,
								  JOYSTICK_FORWARD_Y,JOYSTICK_CENTER_X,JOYSTICK_CENTER_Y]):
									  print side,array,val
		print 'Outputting to file'

		FILE = open( "joycal.dat", 'w' )
		FILE.write( str(JOYSTICK_LEFT_X) + ' ' )
		FILE.write( str(JOYSTICK_CENTER_X) + ' ' )
		FILE.write( str(JOYSTICK_RIGHT_X) + ' ' )

		FILE.write( str(JOYSTICK_FORWARD_Y) + ' ' )
		FILE.write( str(JOYSTICK_CENTER_Y) + ' ' )
		FILE.write( str(JOYSTICK_BACK_Y) + ' ' )

		JOYSTICK_MAX_USEABLE = JOYSTICK_CENTER_X - JOYSTICK_LEFT_X
		JOYSTICK_MAX_USEABLE = min( JOYSTICK_MAX_USEABLE, JOYSTICK_RIGHT_X - JOYSTICK_CENTER_X )
		JOYSTICK_MAX_USEABLE = min( JOYSTICK_MAX_USEABLE, JOYSTICK_CENTER_Y - JOYSTICK_FORWARD_Y )
		JOYSTICK_MAX_USEABLE = min( JOYSTICK_MAX_USEABLE, JOYSTICK_BACK_Y - JOYSTICK_CENTER_X )

		FILE.write( str(JOYSTICK_MIN_USEABLE) + ' ' )
		FILE.write( str(JOYSTICK_MAX_USEABLE) + '\n' )
		FILE.close()
		viz.quit()
	else:
		print data, message

if __name__ == '__main__':
	print __doc__
	viz.go()
	sid.callback( sid.BUTTONDOWN_EVENT, joystickButtonCallback )
