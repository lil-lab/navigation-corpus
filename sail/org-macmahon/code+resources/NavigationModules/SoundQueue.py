# SoundQueue.py
"""Play sounds and to keep a new sound from cutting off a previous sound before it finishes.

If a sound is currently playing, new sounds will be added to a queue.  Sounds are played in the
order in which they were entered in the queue."""
import wave
import viz

SOUND_QUEUE = {} # queue of sounds that need to be played
LAST_INDEX = 0 # the last used index for a sound in the queue
PLAYING_SOUND = None # the index of the currently playing sound
SOUND_FINISHED_CALLBACK = 27643 # The id for the SoundFinished callback

# Init is just here for legacy purposes.
def Init():
	pass

# Tell the Movement module about the SoundQueue timer callback.
# This should be called anytime the SoundQueue is being used with the 
# Movement module.
def RegisterWithMovementModule(movement=None):
	if not movement: import Movement as movement
	movement.AddTimerHandler(SOUND_FINISHED_CALLBACK, SoundFinished)

def __PlayNextSound():
	global SOUND_QUEUE, LAST_INDEX, PLAYING_SOUND, SOUND_FINISHED_CALLBACK

	if PLAYING_SOUND == None:
		# This shouldn't happen
		return

	# Search through the sound queue, starting at the last played sound 
	# to find the next sound waiting to be played
	index = PLAYING_SOUND
	while index <= LAST_INDEX and not SOUND_QUEUE.has_key(index):
		index = index + 1

	if index <= LAST_INDEX:
		PLAYING_SOUND = index
		# play the next sound
		viz.playsound(SOUND_QUEUE[index]["filename"])

		# start a timer to tell us when the sound is finished
		viz.starttimer(SOUND_FINISHED_CALLBACK, SOUND_QUEUE[index]["length"])
	else:
		# No sounds were waiting to be played
		PLAYING_SOUND = None 

def SoundFinished():
	global SOUND_QUEUE, PLAYING_SOUND

	finishedIndex = PLAYING_SOUND

	if PLAYING_SOUND == None:
		# This shouldn't happen
		# set PLAYING_SOUND to the lowest possible index to make sure 
		# we didn't miss any sounds
		PLAYING_SOUND = 1
	elif SOUND_QUEUE[PLAYING_SOUND] != None:
		# Call the "sound finished" callback for this sound if there is one
		if SOUND_QUEUE[PLAYING_SOUND]["callback"] != None:
			callback = SOUND_QUEUE[PLAYING_SOUND]["callback"]
			callback( finishedIndex, SOUND_QUEUE[PLAYING_SOUND]["filename"] )
		# Delete this sound from the queue
		del SOUND_QUEUE[PLAYING_SOUND]

	# If there's another sound waiting to be played, play it
	__PlayNextSound()

def PlaySound(wavefile, callback=None):
	"""Adds a wavefile to the queue of sounds to be played.

	wavefile: <String> The name of the wavefile to be played.
	callback: <Function Pointer> called when the associated wavefile is finished playing."""
	global SOUND_QUEUE, LAST_INDEX, PLAYING_SOUND

	# compute the time this wave file will play
	wav1 = wave.open(wavefile,'r')
	n = wav1.getnframes() 
	rate = wav1.getframerate()
	length = 1.0 * n / rate
	wav1.close()

	# create an object for the new sound
	newSound = {}
	newSound["filename"] = wavefile[:]
	newSound["callback"] = callback
	newSound["length"] = length

	# place the new sound object in the queue
	thisIndex = LAST_INDEX + 1
	SOUND_QUEUE[thisIndex] = newSound
	LAST_INDEX = thisIndex
	# If no sound is playing, start this one
	# Note: If another sound is playing, we don't have to do anything
	if PLAYING_SOUND == None:
		PLAYING_SOUND = thisIndex - 1
		__PlayNextSound()

	# Return the index of the file in the queue
	return thisIndex

def ClearAllSounds():
	"""Remove all sounds currently in the queue (sounds that have not been played yet).

	If a sound is currently being played, it will not be stopped."""
	global SOUND_QUEUE, LAST_INDEX, PLAYING_SOUND, SOUND_FINISHED_CALLBACK

	# Are there any sounds in the queue?
	if PLAYING_SOUND == None or PLAYING_SOUND == LAST_INDEX:
		return

	# Delete all sounds waiting to be played
	index = PLAYING_SOUND + 1
	while index <= LAST_INDEX:
		if SOUND_QUEUE.has_key(index):
			del SOUND_QUEUE[index]
		index = index + 1
