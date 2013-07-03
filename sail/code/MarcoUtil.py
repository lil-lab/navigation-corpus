# Author: David Chen (dlcc@cs.utexas.edu)
# Created: November 2009
# Updated: August 2011

# This script provides utility functions for running
# the MARCO parser and executor

#################
# Import: Start #
#################

import os, sys, random

# Add the directory containing MARCO code to the system path
MarcoPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MARCO")
if MarcoPath not in sys.path:
  sys.path.insert(0, MarcoPath)

# Add the path for NLTK corpora
NLTKCorporaPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MARCO", "nltk_contrib")
os.environ["NLTK_CORPORA"] = NLTKCorporaPath

# Suppress warnings since many packages are outdated
import warnings
warnings.simplefilter("ignore")
import ParseDirections
from CompoundAction import *
warnings.resetwarnings()

import Sense

import logging
from Utility import logger

from Robot.POMDP_Sim import Robot_POMDP_Sim as Robot
from Robot import Recognizers_POMDP_Antie_Periph_Sim as RecognizerModule

from POMDP.MarkovLoc_Grid import getMapGrid
from POMDP.MarkovLoc_Jelly import getMapJelly
from POMDP.MarkovLoc_L import getMapL

###############
# Import: End #
###############

##############################
# Set global variables: Start #
###############################

maps = {'grid': getMapGrid, 'jelly':getMapJelly, 'l':getMapL}

#############################
# Set global variables: End #
#############################

#############################
# Function Defitions: Start #
#############################

# MARCO requires a directory to write the log files.  This sets that 
# log directory
def setLog(logDir="/tmp"):
  logger.shutdownLogger()
  logger.initLogger("MARCO_Logs", consoleLevel=logging.CRITICAL, doTrace=False, LogDir=logDir)


# Takes in an instruction in text form, parses it with the MARCO
# parser and returns the resulting list of compound actions (a Plan)
# The optional argument subplan specifies whether this is a subplan.
# If it's not a subplan, MARCO will try to infer additional end of
# route instructions that were not specified (e.g. adds a travel()
# if the last action is a turn)
def parse(instruction, subplan=True):
  # suppress outputs
  oldStdOut = sys.stdout
  sys.stdout = open(os.devnull, "w")

  # first arguments are Directors and Maps, this is only useful
  # when training the parser from scratch.  But in our case,
  # we are just loading a trained pcfg.
  parser = ParseDirections.getDirParser([], [], collectStats=False)

  compoundActions = []
  try:
    parsed = parser.parse(instruction)
    frames = Sense.trees2frames(parsed)
    # This is basically doing the same thing as CompoundAction.model()
    # except model() always has subplan=False
    compoundActions = Plan(frames, subplan=subplan)
  except KeyboardInterrupt:
    raise
  except:
    # restore standard output
    sys.stdout = oldStdOut
    print "Unexpected error while parsing text:", sys.exc_info()[0]
  finally:
    # restore standard output
    sys.stdout = oldStdOut

  return compoundActions

# Takes a map and a starting location/orientation and executes
# the given compoundActions.  Then return the list of positions
# visited while executing the actions
# The startPos is in the format (x,y,orientation) which
# is referred to as plat in the MARCO framework (i.e. position2plat)
# orientation is 0,90,180, 270 or -1 which means unknown
def execute(mapName, startPos, compoundActions):
   pomdp = maps[mapName.lower()]()
   robot = Robot(pomdp, "test", RecognizerModule.PomdpAntiePeriphSimRecognizer)   
   (x,y,direction) = startPos

   # A direction of -1 means it's unspecified, so randomly select one
   if direction == -1:
     possibleDirections = [0, 90, 180, 270]
     random.shuffle(possibleDirections)
     direction = possibleDirections[0]
     startPos = (startPos[0], startPos[1], direction)

   #Doing the transformation from our representation to internal
   #MARCO representation
   place = robot.pomdp.plat2place(x,y)
   orientation = robot.pomdp.platdir2orient(direction)
   robot.pomdp.trueState = (place, orientation)
   
   path = [startPos]
   try:
     for action in compoundActions:
        action.execute(robot)

        #Transforming internal MARCO representation of the new position
        #back to our representation
        (newPlace, newDir) = robot.pomdp.trueState
        newCoords = robot.pomdp.place2coords(newPlace)
        newPlat = robot.pomdp.coords2plat(newCoords[0], newCoords[1], newDir)     
        path.append(newPlat)
   except:
     print "Unexpected error:", sys.exc_info()
   return path



## The log directory needs to be set before anything else
# can be used
setLog()
