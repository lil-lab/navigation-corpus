# HotSpots.py
# $Revision: 1.8 $
# $Date: 2006/12/01 21:22:53 $
"""
Handle hotspots placed in the environment.

ReadInHotSpots loads the location and audio cue of each hotspot.

After the hotspots are loaded, the audio cue will be played whenever the subject enters a hotspot.

The subject can also be requested to go on a series of trials of randomly going from hotspot to
hotspot (see StartTrials). The structure of the trials can also be customized by specifying a
callback function in StartTrials."""

import os
import string
import copy
import random
import wave
import viz
import Movement
import SoundQueue

__HOTSPOTS = [] # list of hotspots (elements are tuples of (x,y) coordinates)
__HOTSPOT_SOUNDS = [] # list of sounds for entering a hotspots
__GOTO_SOUNDS = [] # list of hotspot sounds for go-to commands
__NUM_TRIALS = 0 # number of trials subject must run (0 if done, None if infinite)
__CURRENT_TARGET = 0 # current hotspot target
__NEXT_TARGET = 0
__ANNOUNCE_TARGET = 0 # variable for announcing target if subject starts in a hotspot
__ANNOUNCE_HOTSPOTS = 1 # variable for announcing hotspots when subject traverses
__MESSAGE = None # last audio message
__SOUND_ON = 1 # 1 if you want to announce targets, 0 otherwise
__IN_HOTSPOT = 0 # The Hotspot# if subject currently in hotspot, 0 otherwise
__CALLBACK = None # callback function called whenever subject completes one trial (this function gets __START and __CURRENT_TARGET as paramers)
__START = None # The Hotspot# of where trial started (None if trial started outside of a hotspot)
__RADIUS = 0.5 # the radius of the hotspot
__SCALE = 4 # the distance between two nodes in the layout
__FINISHED_WAV_FILE = './Layouts/SharedMedia/Sounds/finished.wav'
__MOVEMENT = None

# adds two waves together to a single wave file
# (used, for example, to say: "Position 1...Go to Position 3")
def CombineWaves(wavefile1,wavefile2,outwavefile):
	wav1 = wave.open(wavefile1,'r')
	params = wav1.getparams()
	n = wav1.getnframes()
	data = wav1.readframes(n)
	wav1.close()
	wav2 = wave.open(wavefile2,'r')
	n = wav2.getnframes()
	data = data + wav2.readframes(n)
	wav2.close()
	out = wave.open(outwavefile,'w')
	out.setparams(params)
	out.writeframes(data)
	out.close()

# reset the hotspots.
# its good to reset hotspots if youve been running trials
# and you are about to start a new task.
def ResetHotSpots(numtrials=None):
	global __HOTSPOTS, __IN_HOTSPOT, __CALLBACK, __START, __RADIUS, __SCALE, __NUM_TRIALS
	
	num = 0
	__IN_HOTSPOT = 0
	__CALLBACK = None
	__START = None
	__NUM_TRIALS = numtrials
	#print 'Resetting HotSpots:',
	for (x,z) in __HOTSPOTS:
		num += 1
		viz.deletehotspot(num)
		viz.deletehotspot(-num)
		viz.starthotspot(num,viz.CIRCLE_HOTSPOT_IN,x*__SCALE,-z*__SCALE,__RADIUS)
		#print '%d=(%d,%d)<=>(%d,%d); ' % (num,x,z,x*__SCALE,-z*__SCALE),
	#print

# read in hotspot list from a file
# each line of the file should be:
#  <x-coord>|<y-coord>|<Position Audio file>|<GotoPos Audio file>
# (<x-coord>, <y-coord> should be in PLAT coordinates)
def ReadInHotSpots(filename, scale = 4, radius=0.5, movement=None):
	global __HOTSPOTS, __HOTSPOT_SOUNDS, __GOTO_SOUNDS, __MESSAGE, __IN_HOTSPOT
	global __CALLBACK, __START, __RADIUS, __SCALE, __MOVEMENT

	num = 0
	for (x,z) in __HOTSPOTS: # remove any existing hotspots
		num += 1
		viz.deletehotspot(num)
		viz.deletehotspot(-num)
	# reset variables
	__HOTSPOTS = []
	__HOTSPOT_SOUNDS = []
	__GOTO_SOUNDS = []
	__MESSAGE = None
	__CALLBACK = None
	__START = None
	__IN_HOTSPOT = 0
	__RADIUS = radius
	__SCALE = scale
	if movement is None: __MOVEMENT = Movement
	else: __MOVEMENT = movement
	try:
		inFile = open(filename,'r')
	except:
		raise "\n\n********************************************\nCan not open the hotspot file:\n\t%s\nMake sure that the file exists and that\nthe current working directory is correct.\n********************************************\n"%filename
	for line in inFile.readlines():
		# read in hotspot info from each line
		words = line.split('|')
		__HOTSPOTS.append((int(float(words[0])),int(float(words[1]))))
		__HOTSPOT_SOUNDS.append(string.strip(words[2]))
		__GOTO_SOUNDS.append(string.strip(words[3]))
	inFile.close()
	ResetHotSpots() # resets hotspots (which will activate them)
	viz.callback(viz.HOTSPOT_EVENT, HotSpotHandler) # set viz callback function for hotspots

def StartNextTrial(target=None,callback = None):
	global __HOTSPOTS, __HOTSPOT_SOUNDS, __GOTO_SOUNDS, __START, __NUM_TRIALS, __CURRENT_TARGET
	global __ANNOUNCE_TARGET, __MESSAGE, __SOUND_ON, __IN_HOTSPOT, __NEXT_TARGET
	
	if callback != None:	# change the callback function if one is specified.
		__CALLBACK = callback
	if __NUM_TRIALS != None and __NUM_TRIALS<=0:
		# all trials completed, play 'finished' sound if __SOUND_ON
		__CURRENT_TARGET = 0
		__MESSAGE = __FINISHED_WAV_FILE
		SoundQueue.PlaySound(__MESSAGE)
	else:
		__START = InHotSpot()
		if target:
			__CURRENT_TARGET = target
		else:
			__CURRENT_TARGET = __NEXT_TARGET
		__NEXT_TARGET = 0
		SayCurrentHotSpot(__GOTO_SOUNDS[__CURRENT_TARGET-1])

# viz hotspot callback function. called when enters or leaves hotspots
def HotSpotHandler(id,x,y,z):
	global __HOTSPOTS, __HOTSPOT_SOUNDS, __GOTO_SOUNDS, __NUM_TRIALS, __CURRENT_TARGET, __NEXT_TARGET
	global __ANNOUNCE_TARGET, __MESSAGE, __SOUND_ON, __IN_HOTSPOT, __CALLBACK, __START, __SCALE, __RADIUS
	if id==__CURRENT_TARGET:
		# subject entered the current target
		__IN_HOTSPOT = id
		if __ANNOUNCE_TARGET: __ANNOUNCE_TARGET = 0
		elif __NUM_TRIALS != None: __NUM_TRIALS -= 1 # one trial complete, so reduce #trials if not running infinite trials
		if __NUM_TRIALS != None and __NUM_TRIALS<=0:
			__NEXT_TARGET = 0
		else:
			id = InHotSpot()
			__NEXT_TARGET = __CURRENT_TARGET
			while __NEXT_TARGET == __CURRENT_TARGET:
				# make sure you select a new target
				__NEXT_TARGET = random.randint(1,len(__HOTSPOTS))
		NextTrial = 1
		if __CALLBACK:
			# trial complete, call callback function if it exists
			NextTrial = __CALLBACK((__START,__CURRENT_TARGET,__NEXT_TARGET))
		if NextTrial != 0: StartNextTrial(__NEXT_TARGET)
		_x,_z = __HOTSPOTS[id-1]
		viz.starthotspot(-id,viz.CIRCLE_HOTSPOT_OUT,_x*__SCALE,-_z*__SCALE,__RADIUS) # create hotspot for leaving this hotspot
	elif id>0:
		# id>0 means subject entered a hotspot
		__IN_HOTSPOT = id
		if __ANNOUNCE_TARGET:
			# if starting in this hotspot and must announce the target, combine the two wavefiles and play them
			__ANNOUNCE_TARGET=0
			SayCurrentHotSpot(__GOTO_SOUNDS[__CURRENT_TARGET-1])
		else:
			SayCurrentHotSpot()
		_x,_z = __HOTSPOTS[id-1]
		viz.starthotspot(-id,viz.CIRCLE_HOTSPOT_OUT,_x*__SCALE,-_z*__SCALE,__RADIUS) # create hotspot for leaving this hotspot
	elif id<0:
		# id<0 means you left a hotspot
		# (since hotspots are removed from the list whenever you enter them,
		# you must put them back in the list)
		__IN_HOTSPOT = 0
		_x,_z = __HOTSPOTS[-id-1]
		viz.starthotspot(-id,viz.CIRCLE_HOTSPOT_IN,_x*__SCALE,-_z*__SCALE,__RADIUS) # reactivate this hotspot

# Start the Hotspot trials (going from hotspot to hotspot)
# numtrials is the # of target hotspots subject must go to before trials end 
#   set numtrials to None for unlimited trials
# startstate is where the subject will start the trials from
#   provide (x,y,theta) (in PLAT coords) if you want to start at a specific location, or
#   just None if you want to start from a random hotspot
# callback is the function that gets called whenever subject reaches the target hotspot
#   leave as None if you don't want to use a callback function, or pass a pointer to the function
#   The callback function receives a single tuple as a parameter containing:
#        the Hotspot# where the trials started (None if not from a hotspot)
#        the Hotspot# where the subject currently is (the target location)
# If you want to have the subject running trials until some criterion is reached,
# just set numtrials to None, and specify a callback function to test the criterion after each trial.
# The callback can then call StopTrials() to end the hotspots trials if the criterion is met.
def StartTrials(numtrials=None,startstate = None,targetHotspot=None,callback = None,AnnounceLater=1):
	global __HOTSPOTS, __HOTSPOT_SOUNDS, __GOTO_SOUNDS, __NUM_TRIALS, __CURRENT_TARGET
	global __ANNOUNCE_TARGET, __MESSAGE, __SOUND_ON, __CALLBACK, __START,__NEXT_TARGET, __MOVEMENT

	if len(__HOTSPOTS)<=1:
		raise "\n\nERROR: need at least two hotspots specified to use StartTrials.\n"
	else:
		__NUM_TRIALS = numtrials
		__CURRENT_TARGET = targetHotspot or random.randint(1,len(__HOTSPOTS))
		__NEXT_TARGET = 0
		__CALLBACK = callback
		if startstate != None:
			x,y,t = startstate # use startstate specified
		else:
			# find a hotspot to be the starting location
			x,y = __HOTSPOTS[__CURRENT_TARGET-1]
			while (x,y) == __HOTSPOTS[__CURRENT_TARGET-1]:
				x,y = random.choice(__HOTSPOTS)
			t = random.choice([0,90,180,270]) # randomly select angle
		__MOVEMENT.MoveTo(x,y,t) # move to the starting state
		__START = InHotSpot()
		if InHotSpot():
			__ANNOUNCE_TARGET = 1 #must announce the target when the starting location hotspot's handler is called
		else:
			# announce the target location
			__ANNOUNCE_TARGET = 0
			__MESSAGE = __GOTO_SOUNDS[__CURRENT_TARGET-1]
			if __SOUND_ON:
				SoundQueue.PlaySound(__MESSAGE)

# return 1 if trials are finished, 0 otherwise
def TrialFinished():
	global __NUM_TRIALS
	return __NUM_TRIALS != None and __NUM_TRIALS<=0

# give audio cue for current target
def SayCurrentTarget():
	global __GOTO_SOUNDS, __CURRENT_TARGET, __SOUND_ON
	try:
		if __CURRENT_TARGET>0 and __SOUND_ON:
			SoundQueue.PlaySound(__GOTO_SOUNDS[__CURRENT_TARGET-1])
	except:
		pass

def GetCurrentTargetSound():
	global __GOTO_SOUNDS, __CURRENT_TARGET, __SOUND_ON
	try:
		if __CURRENT_TARGET>0:
			return __GOTO_SOUNDS[__CURRENT_TARGET-1]
		else:
			return None
	except:
		return None

# repeat last audio message
def RepeatLastMessage():
	global __MESSAGE, __SOUND_ON
	if __SOUND_ON:
		SoundQueue.PlaySound(__MESSAGE)

# return current target hotspot number
def GetCurrentTarget():
	global __CURRENT_TARGET
	return __CURRENT_TARGET

# get coordinates of current target location
def GetCurrentTargetLocation():
	global __HOTSPOTS, __CURRENT_TARGET
	try:
		if __CURRENT_TARGET>0:
			return __HOTSPOTS[__CURRENT_TARGET-1]
		else:
			return None
	except:
		return None

def GetCurrentStart():
	"""Return current start hotspot number."""
	global __START
	return __START

def GetCurrentStartLocation():
	"""Return coordinates of current start location."""
	global __HOTSPOTS, __START
	try:
		return __HOTSPOTS[__START-1]
	except:
		return None

# return list of hotspot coordinates
def GetHotSpots():
	global __HOTSPOTS
	return copy.copy(__HOTSPOTS)

def GetHotSpot(num):
	global __HOTSPOTS
	try:
		if num>0:
			return __HOTSPOTS[num-1]
		else:
			return None
	except:
		return None

# if on==1, turn sound on, if on==0, turn sound off.
def SoundOn(on=1):
	global __SOUND_ON
	__SOUND_ON = on

def AnnounceHotSpots(on=1):
	"""Turn hot spot announcements on, if on==1, or off, if on==0."""
	global __ANNOUNCE_HOTSPOTS
	__ANNOUNCE_HOTSPOTS = on

# return hotspot number if currently in a hotspot, 0 otherwise
def InHotSpot():
	global __HOTSPOTS,__IN_HOTSPOT, __MOVEMENT
	
	x,y = __MOVEMENT.GetPlatCoords()
	num = 0
	__IN_HOTSPOT=0
	for (_x,_y) in __HOTSPOTS:
		num += 1
		if (x == _x) and (y == _y):
			__IN_HOTSPOT = num
	return __IN_HOTSPOT

# if in a hotspot, play that hotspot's audio cue, with extrawave appended to it
# if not in a hotspot, just play extrawave
def SayCurrentHotSpot(extrawave=None):
	global __HOTSPOT_SOUNDS, __MESSAGE, __IN_HOTSPOT, __SOUND_ON, __ANNOUNCE_HOTSPOTS
	if __ANNOUNCE_HOTSPOTS and InHotSpot()>0:
		__MESSAGE = __HOTSPOT_SOUNDS[__IN_HOTSPOT-1]
		if __SOUND_ON: SoundQueue.PlaySound(__MESSAGE)
	if extrawave:
		__MESSAGE = extrawave
		if __SOUND_ON: SoundQueue.PlaySound(__MESSAGE)

# Play hotSpotNum's goto sound
def PlayHotSpotMessage(hotSpotNum, playGoto = 0, forcePlay = 0):
	global __HOTSPOT_SOUNDS, __MESSAGE, __SOUND_ON
	if playGoto:
		__MESSAGE = __GOTO_SOUNDS [hotSpotNum - 1]
	else:
		__MESSAGE = __HOTSPOT_SOUNDS [hotSpotNum - 1]
	if __SOUND_ON or forcePlay:
		SoundQueue.PlaySound(__MESSAGE)

# end the hotspot trials
def StopTrials():
	global __NUM_TRIALS, __CURRENT_TARGET, __START, __NEXT_TARGET
	__NUM_TRIALS = 0
	__CURRENT_TARGET = 0
	__NEXT_TARGET = 0
	__START = None

# returns the current version of the module
def GetVersion():
	import re
	m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.8 $')
	if m:
		return m.group(1)
	else:
		return None	
	
