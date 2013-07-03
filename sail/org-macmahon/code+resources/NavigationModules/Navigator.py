#!/usr/local/bin/python

# CVS:
# $Revision: 1.2 $
# $Date: 2005/09/06 22:08:44 $

# Version 2.0:
# added scaling and ability to select wall texture in DisplayVRMLLayout

# Version 1.02:
# 10/13 Added the ability to determine location for known
# Building.
# Version 1.03:
# Changed the list of views to a string.
# Navigator Module 10/26/99
#------------------
# Version 0.01 10/26/99 
# Added the ability to search ahead to determine which of N
# 	moves is optimal.
# Version 0.03 3/2/2000
# Modifying this version to allow the program to read and write
# files that specify specific indoor layout designs.  
# 
#------------------
# Version 0.04 3/8/2000
# Modified the code to allow ANTIE to find her way to a specific location
# in the environment.  Before her task was to determine her location.  Currently
# it is to find the shortest route to a particular location.
#  LocalizeMySelf(self,StartState=(0,0,0),DataFile=sys.stdout):
#   This function finds the optimal path for determining her location within an
#   environment.  CurrState is the location where ANTIE will start.
#------------------
#Version 0.065
#  Added symmetry breaking algorithm.
#------------------
#Version 0.0651
#  
#------------------
# Version 0.0660 (4/24/2001)
# Added the ability to limit the number of locations considered while 
# navigating through building.  This is the sub-ideal with limited position
# knowledge.
#------------------
# Version 0.661 (4/24/2001)
# Adding the ability to change the weighting of the moves
# Never actually added this yet.
#------------------
# Version 0.662 4/25/2001
# Adding the ability to search only N deep in the search tree.  
# 4/25/2001 Having the computer pick a move at random.
#------------------
# Version 0.663 5/1/2001
# Adding the ability to change the cost for each of the move types
#------------------

import sys, math, random, string, re,os
from posixpath import exists

# return the plat width, height, and size for a given text map file
def getPlatDim(filename):
	"""returns (width, height, size (= # of hallways))"""
	f = open(filename,'r')
	lines = f.readlines()
	f.close()
	width = height = size = 0
	for line in lines:
		width = max([width,string.count(line,'.')])
		if string.find(line,'.') >= 0: height = height + 1
		size = size + string.count(line,'_') + string.count(line,'|')
	return (width,height,size)

# returns the current version of the module
def GetVersion():
	import re
	m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.2 $')
	if m:
		return m.group(1)
	else:
		return None

#AvailableMoves={'SlideRight':(1,0,0),'SlideLeft':(-1,0,0),'RotateLeft':(0,0,-1),'RotateRight':(0,0,1),'Forward':(0,1,0)}
#MoveNum={'SlideRight':0,'SlideLeft':1,'RotateLeft':2,'RotateRight':3,'Forward':4}
#MoveName=['SlideRight','SlideLeft','RotateLeft','RotateRight','Forward']
#AvailableMoves={'RotateLeft':(0,0,-1),'RotateRight':(0,0,1),'Forward':(0,1,0)}
#MoveDesc=[(1,0,0),(-1,0,0),(0,0,-1),(0,0,1),(0,1,0)]
MoveNum={'RotateLeft':0,'RotateRight':1,'Forward':2}
MoveName=['RotateLeft','RotateRight','Forward']
MoveDesc=[(0,0,-1),(0,0,1),(0,1,0)]
class TESTPATH:
	def __init__(self):
		self.Path={}
		self.View={}
		self.StartPosition=[]
		self.CurrPosition={}
		self.OtherCurrPositions={}
		self.ConsideredStartPositions={}
		self.NumSteps={}
		self.Done={}
		self.OptimalPath={}
		self.MinCost={}
		self.Cost={}
		self.Path={}
class NODE:
	def __init__(self):
		self.Active=0
		self.ProspectList=[]
		self.Linked=[]
		self.View=[0,0,0,0]
	#------------------------
	# FindPotentialNodes
	# This function determines which intersections are in the vacinity of the coordinates passed
	# into the function.  This function is run when the plat is first created.  It produces a 
	# list of tuples with all of the coordinates of the potential nodes that can be connected
	# to the given node.  
	#------------------------
	def FindPotentialNodes(self,x,y,xsize,ysize):
		#------------------------
		# We need to check three things
		# to make the appropriate potential list:
		# 1) is the potential node outside of the plat
		# 2) is the node already on the potential list
		# 3) is the node already active
		# If the answer to any of these questions is 'yes' then
		# we don't put the node on the list
		#------------------------
		if (x+1 <  xsize):
			self.ProspectList.append((x+1,y))
		if (x-1 >= 0 ):
			self.ProspectList.append((x-1,y))
		if (y+1 < ysize):
			self.ProspectList.append((x,y+1))
		if (y-1 >= 0):
			self.ProspectList.append((x,y-1))
class PLAT(NODE):
	def __init__(self,val1=20,val2=20,len=10):
		self.x=val1
		self.y=val2
		self.Length=len
		self.PotentialList=[]
		self.ChosenList=[]
		self.Nodes=[]
		for x in range(self.x):
			self.Nodes.append([])
			for y in range(self.y):
				self.Nodes[x].append(NODE())
				self.Nodes[x][y].FindPotentialNodes(x,y,self.x,self.y)
				

		
	def AnalyzeLayout(self,ViewDepth, EndState=[0,0],floorPlanName=':Data:tempFloor'):
		PossiblePositions=[]
		self.ComputeAllViews(ViewDepth)
		for tempPos in self.ChosenList:
			for VCount in range(4):
				PossiblePositions.append((tempPos[0],tempPos[1],VCount))
		positionCount=0
		ambiguity=0
		for CurrState in PossiblePositions:	
			currView=self.Nodes[CurrState[0]][CurrState[1]].View[CurrState[2]]
			currPossiblePositions=self.FindView(currView,PossiblePositions)
			#OptimalMoves=self.GoToLocation(StartState=CurrState,EndState=EndState,floorPlanName=floorPlanName)
			#print '%s\t%s' % (CurrState,len(currPossiblePositions))
			#print '%s\t%s' % (CurrState,len(currPossiblePositions), currView)
			print '%s\t%s' % (CurrState, currView)
			positionCount=positionCount+1
			ambiguity=ambiguity+len(currPossiblePositions)
		print 'Average Ambiguity=%5.4f' % (ambiguity/positionCount)
	def FindGotoLocaitonInFile(self,CurrState,EndState,ViewDepth,floorPlanName=':Data:tempFloor',PossiblePositions=[],Mode=1,Weighting=[1,1,1]):
		OptimalMove=[]
		modelMode=['WAI','GOTO']
		print "------------------------"
		#-------------------------------------------------------------------
		# Version 0.651 (BJS: 2/01/2001)
		# FloorPlanName will now have the path and the view information
		# This was done so that the user could use different look-up-files
		# for different conditions specified in different directories
		#-------------------------------------------------------------------
		#GotoFileName='%s_%i_Weight_01_01_1.DAT' % (floorPlanName,ViewDepth)
		weightString="%s_%s_%s" % (Weighting[0],Weighting[1],Weighting[2])
		weightString=re.sub('\.','',weightString)
		GotoFileName='%s_%i_%s_%s.DAT' % (floorPlanName,ViewDepth,weightString,modelMode[Mode])
		#print "GotoFileName=%s" % GotoFileName
		#GotoFileName='%s' % (floorPlanName)
		if not exists(GotoFileName):
			LOCALIZEFILE=open(GotoFileName,'w')
			LOCALIZEFILE.close()
		LOCALIZEFILE=open(GotoFileName,'r')
		for line in LOCALIZEFILE.readlines():
			Fields=re.split('\s\#\s',line)
			tempFields=str(PossiblePositions)
			#tempFields=re.sub('[\s+]',',',tempFields)
			#Fields[0]==re.sub('[\s+]',',',Fields[0])					
			#if re.search(Fields[0],tempFields)!=None and re.search(tempFields,Fields[0])!=None:
			if Fields[0]==tempFields:
				#print "\n#%s#\t#%s#" % (Fields[0] ,tempFields)
				#print "FindGotoLocaitonInFile(Fields[0])=%s" % Fields[0]
				#print "FindGotoLocaitonInFile(tempFields)=%s" % tempFields
				#print "Pre-substitution fields=%s\n" % Fields[1]
				Fields[1]=re.sub('[\[\]\s]','',Fields[1])
				tempOptimalMove=re.split(',',Fields[1])
				for temp in tempOptimalMove:
					OptimalMove.append(string.atoi(temp))
		LOCALIZEFILE.close()
		#---------------
		# Brian, You set Optimalmove=[]
		# to force the program to compute the set of
		# moves.  Remove when done
		#---------------
		#OptimalMove=[]
		print "Optimal Move=%s" % OptimalMove
		#---------------
		if 0==len(OptimalMove):
			LOCALIZEFILE=open(GotoFileName,'a')
			tempPossiblePositions=str(PossiblePositions)
			tempPossiblePositions=re.sub('\s+]',',',tempPossiblePositions)
			#---------------
			# Now use FindPosition to determine the next optimal move
			# given the current state
			#--------------
			OptimalMove=self.FindPosition((CurrState[0],CurrState[1]),CurrState[2],PossiblePositions,EndPosition=EndState,Weighting=Weighting,Mode=Mode)
			print 'GoToLocation(tempPossiblePositions):\t %s' % tempPossiblePositions
			LOCALIZEFILE.write("%s # %s\n" % (tempPossiblePositions,OptimalMove))
			LOCALIZEFILE.close()

		return(OptimalMove)
	def GoToLocationNoPlanning(self,StartState,EndState=(0,0),PossiblePositions=[],ViewDepth=100,DataFile="",floorPlanName="",ProbRandom=1.0):
		CheckState=[0,0,0]
		Ambiguity=[0,0,0]
		self.ComputeAllViews(ViewDepth+1)
		CurrState=StartState
		currView=self.Nodes[CurrState[0]][CurrState[1]].View[CurrState[2]]
		NumMoves=0;
		if (PossiblePositions==[]):
			# ---------------------------------
			# First we will make all of the positions "possible positions".
			# ---------------------------------
			for tempPos in self.ChosenList:
				for VCount in range(4):
					PossiblePositions.append((tempPos[0],tempPos[1],VCount))
		# ---------------------------------
		# Find all of the locations that are consistent with the current
		# View.
		# ---------------------------------
		PossiblePositions=self.FindView(currView,PossiblePositions)
		InitialPossiblePositions=PossiblePositions
		#print 'GoToLocation(currView):\t %s' % currView
		Moves="#"
		OptimalMoveList=[]
		ConsideredPositions=[]

		#while len(PossiblePositions)>1:
		Selection=random
		while len(PossiblePositions)>1 or\
				CurrState[0] != EndState[0] or\
				CurrState[1] != EndState[1]:
			if Selection.random()<ProbRandom:
				SelectedMove=random.choice([0,1,2])
				while (0==self.CheckIfValidMove(CurrState,MoveName[SelectedMove])):
					# Since we are only checking for walls we can now assume that 
					# the person cannot move forward.  We will only select for
					# a rotation.
					SelectedMove=random.choice([0,1])
			else:
				SelectedMove=self.FindGotoLocaitonInFile(ViewDepth=ViewDepth,CurrState=CurrState,floorPlanName=floorPlanName,PossiblePositions=PossiblePositions,EndState=EndState)
				#SelectedMove=self.GoToLocation(StartState=CurrState,EndState=EndState,PossiblePositions=PossiblePositions,ViewDepth=ViewDepth,DataFile=DataFile,floorPlanName=floorPlanName,PositionMemory=0)
				SelectedMove=random.choice(SelectedMove)
			OptimalMoveList.append(SelectedMove)
			CurrState=self.MakeState(CurrState,SelectedMove)
			currView=self.Nodes[CurrState[0]][CurrState[1]].View[CurrState[2]]
			OldPos=[]
			for otherPos in PossiblePositions:
				OldPos.append(self.MakeState(otherPos,SelectedMove))
			NewPossiblePositions=self.FindView(currView,OldPos)
			# ---------------------------------
			# Now we want to only include those possible positions that were
			# part of our original set of possible positions
			# ---------------------------------
			PossiblePositions=[]
			for OldPosItem in OldPos:
				if OldPosItem in NewPossiblePositions:
					PossiblePositions.append((OldPosItem[0],OldPosItem[1],OldPosItem[2]))
		OptimalMoveList.append(4)
		return(OptimalMoveList)
	def GoToLocation(self,StartState,ViewDepth=9999,EndState=(0,0),PossiblePositions=[],DataFile=sys.stdout,floorPlanName=':Data:tempFloor',PositionMemory=0,Weighting=[1,1,1],Mode=1):
		CheckConsideredPos=[]
		Ambiguity=[0,0,0,0]
		MovementChoices=[0,0,0]
		self.ComputeAllViews(ViewDepth+1)
		CurrState=StartState
		currView=self.Nodes[CurrState[0]][CurrState[1]].View[CurrState[2]]
		print "CurrView=%s" % currView
		NumMoves=0;
		if (PossiblePositions==[]):
			# ---------------------------------
			# First we will make all of the positions "possible positions".
			# ---------------------------------
			for tempPos in self.ChosenList:
				for VCount in range(4):
					PossiblePositions.append((tempPos[0],tempPos[1],VCount))
		# ---------------------------------
		# Find all of the locations that are consistent with the current
		# View.
		# ---------------------------------
		PossiblePositions=self.FindView(currView,PossiblePositions)
		#InitialPossiblePositions=PossiblePositions
		#print 'GoToLocation(currView):\t %s' % currView
		Moves="#"
		OptimalMoveList=[]
		ConsideredPositions=[]
		while len(PossiblePositions)>1 or CurrState[0] != EndState[0] or CurrState[1] != EndState[1]:
			#print 'Possible Positions (281)=%s' % PossiblePositions

			#-------------
			# Find the next move that is optimal
			#-------------
			# Version 0.0660 (4/23/2001)
			# - This is where we are going to select one position of the possible positions.  We will have two 
			#   lists of positions.  One will be the total set of possible positions (PossiblePositions) and the second
			#   will be the set of position under consideration (ConsieredPositions).
			#-------------
			# ------------
			# Version 0.0660 4/24
			# This part of the algorithm is used to check to see if
			# there was an inconsistent move before.  This is part of the
			# memory limitation.
			# 1 = Pick a random location only when current hypothesis is inconsistent with view
			# 2 = Pick a random location on every move
			# 0 = No Memory Limitation
			# ------------	
			#ConsideredPositions=[]
			#-----------------------------
			# V 0.0663 BJS 5/23/2002
			# We are changing the function so that it will select a random number
			# of positions as specified by Position memory.
			# We are now changing the flag meanings (as specified above)
			# 0= No memory limitation
			# >0 Indicates number considered states.
			#-----------------------------
			# We run in this first section if we hypothesized that we
			# were at a state and now have evidence that we are not at
			# that state.
			if (ConsideredPositions not in PossiblePositions) and (PositionMemory>0):
				#-----------------------------
				# Ver 0.0663 BJS 5/23/2002
				# First we will make TempPositions equal to all of the possible
				# positions.  Then we will randomly select from this.
				# vector the elements for ConsideredPositions				
				#-----------------------------
				#print 'Possible Positions (319)=%s' % PossiblePositions

				ConsideredPositions=[]
				tempPosList=PossiblePositions[:]
				if len(tempPosList)>PositionMemory:
					listLength=PositionMemory
				else:
					listLength=len(tempPosList)
				#print 'Possible Positions (327)=%s' % PossiblePositions

				for i in range(listLength):
					#print 'Possible Positions (330:%i:%i)=%s' % (i,PositionMemory,PossiblePositions)
					tempListItem=random.choice(tempPosList)
					ConsideredPositions.append((tempListItem[0],tempListItem[1],tempListItem[2]))
					tempPosList.remove(tempListItem)
				print '-------------------\nConsideredPositions(1)=%s\nPossiblePositions=%s\n-------------------\n' % (ConsideredPositions,PossiblePositions)
			else:
				ConsideredPositions=[]
				for otherPosition in PossiblePositions:
					ConsideredPositions.append((otherPosition[0],otherPosition[1],otherPosition[2]))
				print '-------------------\nConsideredPositions(2)=%s\n-------------------\n' % ConsideredPositions
			#print 'Possible Positions (335)=%s' % PossiblePositions

			#print "GotoLocation(ConsideredPositions)=%s" % ConsideredPositions
			#print "PositionMemory%s" % PositionMemory
			#print "GotoLocation(PossiblePositions)=%s" % PossiblePositions
			
			OptimalMove=self.FindGotoLocaitonInFile(ViewDepth=ViewDepth,CurrState=CurrState,floorPlanName=floorPlanName,PossiblePositions=ConsideredPositions,EndState=EndState,Weighting=Weighting,Mode=Mode)
			#print "GotoLocation(OptimalMove)=%s" % OptimalMove
			#--------------
			# The current state was not visited before and we
			# are going to compute the optimal moves from the
			# current state
			#--------------
			#print ' GoToLocation PossiblePositions(%s)' % (PossiblePositions)
			#print ' GoToLocation CurrentState(%s,%s,%s) OptimalMove(%s)' % (CurrState[0],CurrState[1],CurrState[2],OptimalMove)
			#print "Before--CheckState=%s" % (CheckState)
			#print "Before--CheckState %s == %s" % (CheckState[0],CheckState[2])
			#if (CheckState[0]==CheckState[2] and Ambiguity[0]==Ambiguity[1] and Ambiguity[1]==Ambiguity[2] and len(OptimalMoveList)>2 and PositionMemory==0):
			# ------------
			# This is part of the symmetry breaking algorithm
			# ------------
			#print "len(OptimalMoveList)=%s" % len(OptimalMoveList)
			#print "len(Ambiguity)=%s" % len(Ambiguity)
			
			if len(OptimalMoveList)>3:
				CheckConsideredPos[0]=CheckConsideredPos[1]
				CheckConsideredPos[1]=CheckConsideredPos[2]
				CheckConsideredPos[2]=CheckConsideredPos[3]
				CheckConsideredPos[3]=ConsideredPositions;
				if (CheckConsideredPos[0]==CheckConsideredPos[2] and CheckConsideredPos[1]==CheckConsideredPos[3]) : 
					OptimalMoveList=[5]
					CurrState[0]= EndState[0]
					CurrState[1]= EndState[1]
					#----------------------
					print '----------------\nPossiblePositions\n-------------\n%s(%s)' % (PossiblePositions,len(PossiblePositions))
					print '################\nExcluded Trial\n################'
					PossiblePositions=[]
			else:
				CheckConsideredPos.append(ConsideredPositions)
			print "CheckConsideredPos=%s\nPossiblePositions=%s" % (CheckConsideredPos,PossiblePositions)
			print "OptimalMoveList:%s" % OptimalMoveList

			#print "OptimalMove=%s" % OptimalMove
			SelectedMove=random.choice(OptimalMove)
			print "Optimal Move=%s (%s)" % (OptimalMove,SelectedMove)
			OptimalMoveList.append(OptimalMove)
			#print "OptimalMoveList=%s" % OptimalMoveList
			#print 'len(OptimalMove)=%s; OptimalMove(%s); SelectedMove(%s)' % (len(OptimalMove),OptimalMove,SelectedMove)
			CurrState=self.MakeState(CurrState,SelectedMove)
			# ------------
			# Version 0.0660 4/24				
			# When PositionalMemory equals 1 we are in hypothesis mode and we
			# need to update the position of the considered location.  Earlier in this
			# routine we check to see if the ConsideredPosition is one of the possible 
			# positions.  Later in this routine we update the possible positions based upon	
			# the actual current position.
			# ------------
			#if PositionMemory==1:
			#	ConsideredPositions=self.MakeState([ConsideredPositions[0][0],\
			#						ConsideredPositions[0][1],\
			#						ConsideredPositions[0][2]],SelectedMove)
			currView=self.Nodes[CurrState[0]][CurrState[1]].View[CurrState[2]]
			OldPos=[]
			#print "ConsideredPositions:%s" % ConsideredPositions
			for otherPos in PossiblePositions:
				if otherPos!=[]:
					#print "otherPos=%s,%s,%s" % (otherPos[0],otherPos[1],otherPos[2])
					OldPos.append(self.MakeState([otherPos[0],otherPos[1],otherPos[2]],SelectedMove))
			NewPossiblePositions=self.FindView(currView,OldPos)
			#print 'Possible Positions (401)=%s' % PossiblePositions
			# ---------------------------------
			# Now we want to only include those possible positions that were
			# part of our original set of possible positions
			# ---------------------------------
			#PossiblePositions=[]
			# ---------------------------------
			# Loop through all of theupdated postitions.
			# ---------------------------------	
			PossiblePositions=[]		
			for OldPosItem in OldPos:
				if OldPosItem in NewPossiblePositions:
					PossiblePositions.append((OldPosItem[0],OldPosItem[1],OldPosItem[2]))
			# ---------------------------------
			# Vers 0.0663 BJS 5/23/2002
			# Now we need to update the ConsideredPositions when
			# there is limited memory
			# ---------------------------------
			for otherPos in ConsideredPositions:
				if otherPos!=[]:
					#print "otherPos=%s,%s,%s" % (otherPos[0],otherPos[1],otherPos[2])
					OldPos.append(self.MakeState([otherPos[0],otherPos[1],otherPos[2]],SelectedMove))
			NewPossiblePositions=self.FindView(currView,OldPos)
			ConsideredPositions=[]
			for OldPosItem in OldPos:
				if OldPosItem in NewPossiblePositions:
					ConsideredPositions.append((OldPosItem[0],OldPosItem[1],OldPosItem[2]))

			if (0==Mode and 1==len(PossiblePositions)):
				break
			#print 'Possible Positions (431)=%s' % PossiblePositions
		if 1==len(PossiblePositions) and 5 not in OptimalMoveList:
			OptimalMoveList.append(4)
				#print ">>>GotoLocation(PossiblePositions)=%s" % PossiblePositions
		#DataFile.write("GoToLocation >%s\t(%s)\t%s\t%s\t%s\t%s\t%s\n" % (StartState,ViewDepth,CurrState,EndState,NumMoves,Moves,OptimalMoveList))
		return(OptimalMoveList)

	def AnalyzeIRT(self,SubID=[],Conditions=[]):
		IRTTime=[]
		numMoves=[]
		IRTUncertTime={}
		IRTUncertMoves={}
		for currSubID in SubID:
			for currCond in Conditions:
				DataFile=open(":DATA:"+currSubID+currCond+".OUT",'r')
				SimmFile=open(":DATA:"+currSubID+currCond+".SIM",'r')
				lastTime=0
				moveCount=0
				for line in DataFile.readlines():
					if re.match('>',line):
						SimmLine=SimmFile.readline()
						Uncertainty=len(re.split('\),',SimmLine))
						if re.match('> START',line):
							moveCount=0
							lastTime=0
							if not re.match('\#',SimmLine):
								sys.stdout.write("MISMATCH IN FILES:%s%s\n" % (currSubID,currCond))
								print line, SimmLine
						Fields=re.split('\s+',line)
						if len(IRTTime)<=moveCount:
							IRTTime.append(string.atof(Fields[5])-lastTime)
							numMoves.append(1)
						else:
							IRTTime[moveCount]=IRTTime[moveCount]+(string.atof(Fields[5])-lastTime)
							numMoves[moveCount]=numMoves[moveCount]+1
						if  "%s" % Uncertainty not in IRTUncertTime.keys():
							IRTUncertTime["%s" % Uncertainty]=string.atof(Fields[5])-lastTime
							IRTUncertMoves["%s" % Uncertainty]=1
						else:
							IRTUncertTime["%s" % Uncertainty]=IRTUncertTime["%s" % Uncertainty]+string.atof(Fields[5])-lastTime
							IRTUncertMoves["%s" % Uncertainty]=IRTUncertMoves["%s" % Uncertainty]+1
						lastTime=string.atof(Fields[5])
						moveCount=moveCount+1
						
		for moveCounter in range(len(numMoves)):
			print moveCounter, IRTTime[moveCounter]/numMoves[moveCounter]	
		uncertList=IRTUncertMoves.keys()
		uncertList.sort()
		for umoveCounter in uncertList:
			print umoveCounter, IRTUncertTime[umoveCounter]/IRTUncertMoves[umoveCounter]	
	def AnalyzeFollowPathData(self,fName='DATA:Temp',EndState=[0,0]):
		DataFile=open(fName,'r')
		PositionalCorrect={}	
		PositionalVisited={}
		sumCorrectGoto=0
		sumCorrectLocalize=0
		NumMoves=0
		Overshoot=0
		RemainUncertainty=0
		NumTrials=0
		IncorrectPosition=0
		SumPerfectRoute=0
		SumCorrectPosition=0
		DiscrepantAntiesCount=0
		WhereAmICount=0
		GotoLocationCount=0
		ChoseNeitherCount=0
		NumMovesBeforeWhereAmI=0
		NumMovesAfterWhereAmI=0
		NumCorrectBeforeWhereAmI=0
		NumCorrectAfterWhereAmI=0
		NumIncorrectBeforeWhereAmI=0
		NumIncorrectAfterWhereAmI=0
		CorrectGoto=[[],[],[]]
		JointProb=[[[],[],[]],[[],[],[]]]
		CountAntieMove=[[],[],[]]
		CountHumanMove=[[],[],[]]	
		NumProbabilities=0
		SumHumanMoves=0
		SumAntieMoves=0
		for line in DataFile.readlines():
			if re.match('\#',line):
				line=re.sub(',\s+',',',line)
				Fields=re.split('\s+',line)
				StartState=Fields[1]
				NumTrials=NumTrials+1.0
				OvershootFlag=0
				PossiblePosition=0
				PerfectRoute=1
				tempAntieMoves=string.atoi(Fields[2])
				tempHumanMoves=string.atoi(Fields[3])
			elif re.match('>',line):
				GoToMove=[]
				WhereAmIMove=[]
				line=re.sub(',\s+',',',line)
				Fields=re.split('\s+',line)
				CorrectLocalize=Fields[6]
				CorrectGoto=Fields[7]
				AntiesMatch=0
				#-----------------------------------------------
				# 	Get the AntieWhere and AntieGoto moves for the
				#   	current state.  Remove the brackets and put the
				# 	elements in a list.
				#-----------------------------------------------
				SubjectMove=string.atoi(Fields[2])
				tempList=re.sub('[\]\[,]','',Fields[3])
				for currItem in tempList:
					WhereAmIMove.append(string.atoi(currItem))
				tempList=re.sub('[\]\[,]','',Fields[4])
				#-----------------------------------------------
				# Version 0.063
				# PositionalInfo is going to be used to keep track of data for each
				# posiition in the environment.
				#-----------------------------------------------
				if PositionalCorrect.has_key(Fields[1]):
					PositionalCorrect[Fields[1]]=PositionalCorrect[Fields[1]]+string.atoi(Fields[7])
					PositionalVisited[Fields[1]]=PositionalVisited[Fields[1]]+1.0
					
				else:
					PositionalCorrect[Fields[1]]=string.atoi(Fields[7])		
					PositionalVisited[Fields[1]]=1.0
				#-----------------------------------------------
				# The following lines of code are used to consider when
				# Antie says there is more than one direction that the 
				# subject can go.
				#-----------------------------------------------
				for currItem in tempList:
					GoToMove.append(string.atoi(currItem))
					if ((string.atoi(currItem) in WhereAmIMove) and (4 not in WhereAmIMove)):
						AntiesMatch=1
					#-----------------------------------------------
					# Use the following to compute mutual information
					#-----------------------------------------------
					#JointProb[[string.atoi(Fields[2])],[string.atoi(currItem)]]=JointProb[[string.atoi(Fields[2])],[string.atoi(currItem)]]+1.0
					#CountAntieMove[string.atoi(currItem)]=CountAntieMove[string.atoi(currItem)]+1.0	
					#CountHumanMove[string.atoi(Fields[2])]=CountHumanMove[string.atoi(Fields[2])]+1.0	
					#NumProbabilites=NumProbabilites+1.0

				if (AntiesMatch==0 and (4 not in WhereAmIMove)):
					DiscrepantAntiesCount=DiscrepantAntiesCount+1.0
					if SubjectMove in GoToMove:
						#print "Chose GoTo Move(%s,%s[%s])" % (SubjectMove,GoToMove,WhereAmIMove)
						GotoLocationCount=GotoLocationCount+1.0
					if SubjectMove in WhereAmIMove:
						#print "Chose WhereAmIMove(%s,%s[%s])" % (SubjectMove,WhereAmIMove,GoToMove)
						WhereAmICount=WhereAmICount+1.0
					if (SubjectMove not in WhereAmIMove) and (SubjectMove not in GoToMove):
						#print "Chose Neither (%s, %s, %s)" % (SubjectMove,GoToMove,WhereAmIMove)
						ChoseNeitherCount=ChoseNeitherCount+1.0
				#-----------------------------------------------
				# Counting how many optimal moves once the subject knows
				# (or could know) where they are located in the layout.
				#-----------------------------------------------
				if (4 in WhereAmIMove):
					NumMovesAfterWhereAmI=NumMovesAfterWhereAmI+1.0
					if 1==string.atoi(CorrectGoto):
						NumCorrectAfterWhereAmI=NumCorrectAfterWhereAmI+1.0
					else:
						NumIncorrectAfterWhereAmI=NumIncorrectAfterWhereAmI+1.0
				if (4 not in WhereAmIMove):
					NumMovesBeforeWhereAmI=NumMovesBeforeWhereAmI+1.0
					if 1==string.atoi(CorrectGoto):
						NumCorrectBeforeWhereAmI=NumCorrectBeforeWhereAmI+1.0
					else:
						NumIncorrectBeforeWhereAmI=NumIncorrectBeforeWhereAmI+1.0
				sumCorrectGoto=sumCorrectGoto+string.atoi(CorrectGoto)
				if 0==string.atoi(CorrectGoto):
					PerfectRoute=0
				sumCorrectLocalize=sumCorrectLocalize+string.atoi(CorrectLocalize)
				NumMoves=NumMoves+1.0
				AntieGoto=Fields[4]
				if re.search('4',AntieGoto) and OvershootFlag==0:
					OvershootFlag=1;
					Overshoot=Overshoot+1.0
			elif re.match('\$',line):
				theState=[]
				stateList=[]
				line=re.sub(',\s+',',',line)
				Fields=re.split('\s+',line)
				SubResp=Fields[2]
				GotoResp=Fields[4]
				GotoResp=re.sub('[\[\]]','',GotoResp)
				PossibleStates=Fields[5]
				PossibleStates=re.sub('[\[\]]','',PossibleStates)
				PossibleStates=re.split('\),',PossibleStates)
				if 1==PerfectRoute:
					SumPerfectRoute=SumPerfectRoute+1.0
					#print StartState
				for currState in PossibleStates:
					currState=re.sub('[\(\)]','',currState)
					currState=re.split(',',currState)
					for myState in currState:
						theState.append(string.atoi(myState))
					stateList.append(theState)
				for currState in stateList:
					if (currState[0]==EndState[0] and currState[1]==EndState[1] and 0==PossiblePosition):
						if (len(stateList)>1):
							RemainUncertainty=RemainUncertainty+1.0
							PossiblePosition=1
						if (1==len(stateList)):
							SumCorrectPosition=SumCorrectPosition+1.0
							PossiblePosition=1
							SumAntieMoves=tempAntieMoves+SumAntieMoves
							SumHumanMoves=tempHumanMoves+SumHumanMoves

				if (0==PossiblePosition):
					IncorrectPosition=IncorrectPosition+1.0
		print "---------------------------"
		print "Percent Correct(%s/%s)=%5.4f\n" % (sumCorrectGoto,NumMoves,sumCorrectGoto/NumMoves)
		print "Remaining Uncertainty(%s/%s)=%5.4f\n" % (RemainUncertainty,NumTrials,RemainUncertainty/NumTrials)
		print "Overshoot(%s/%s)=%5.4f\n" % (Overshoot,NumTrials,Overshoot/NumTrials)
		print "Incorrect(%s/%s)=%5.4f\n" % (IncorrectPosition,NumTrials,IncorrectPosition/NumTrials)
		print "Percent Perfect Route(%s/%s)=%5.4f\n" % (SumPerfectRoute,NumTrials,SumPerfectRoute/NumTrials)
		print "\n------------------------\nNum AntieMoves(%s/%s)=%5.4f\n" % (SumAntieMoves,NumTrials,SumAntieMoves/NumTrials)
		print "Num HumanMoves(%s/%s)=%5.4f\n" % (SumHumanMoves,NumTrials,SumHumanMoves/NumTrials)
		#print "---------------------------"
		#print "Environment and human information"
		#for EnvPosition in PositionalCorrect.keys():
		#	print "%s %s" % (PositionalCorrect[EnvPosition],PositionalVisited[EnvPosition])
		#	print "%s\n%5.4f\n" % (EnvPosition,PositionalCorrect[EnvPosition]/PositionalVisited[EnvPosition])
	def myFollowPath(self,ViewDepth,StartState=(0,0,0),InputPath=[],EndState=[0,0],fName='DATA:Temp',floorPlanName=':Data:tempFloor'):
		self.ComputeAllViews(ViewDepth)
		ValidTrial=1
		PossiblePositions=[]
		for tempPos in self.ChosenList:
			for VCount in range(4):
				PossiblePositions.append((tempPos[0],tempPos[1],VCount))
		currView=self.Nodes[StartState[0]][StartState[1]].View[StartState[2]]
		# ---------------------------------
		# Find all of the locations that are consistent with the current
		# View.
		# ---------------------------------
		PossiblePositions=self.FindView(currView,PossiblePositions)
		#print "myFollowPath(PossiblePositions):\t%s" % PossiblePositions
		AntieMoves=self.GoToLocation(StartState=StartState,EndState=EndState,PossiblePositions=PossiblePositions,ViewDepth=ViewDepth,floorPlanName=floorPlanName)
		print "myFollowPath(AntieMoves):\t%s" % AntieMoves
		#AntieMoves=self.FindPositionInFile(CurrState=StartState,floorPlanName=floorPlanName,Extension='_GOTO.DAT',EndState=EndState,ViewDepth=ViewDepth,PossiblePositions=PossiblePositions)
		CurrState=StartState
		ContinueWithGotoMoves=0
		NumMoves=0
		DataFileName='%s_%i.SIM' % (fName,ViewDepth)
		DataFile=open(DataFileName,'a')
		DataFile.write("#\t%s\t%s\t%s\t%s\t%s\n" % (StartState,len(AntieMoves),len(InputPath),AntieMoves,InputPath))
		DataFile.close()
		#print StartState,InputPath
		for stepNum in InputPath:
			oldState=CurrState
			prevPositions=PossiblePositions
			NumMoves=NumMoves+1
			print "myFollowPath(len(PossiblePositions)):\t%s" % len(PossiblePositions)
			#if len(PossiblePositions)>1:
			#	OptimalMove=self.FindPositionInFile(CurrState=CurrState,floorPlanName=floorPlanName,Extension='_Localize.dat',PossiblePositions=PossiblePositions)
			#else:
			#	OptimalMove=[4]
			#	print "Shortcut"
			OptimalMove=[4]
			#-------------------------------
			# Compute the optimal set of moves
			#-------------------------------
			OptimalGoToMoves=self.GoToLocation(StartState=CurrState,EndState=EndState,PossiblePositions=PossiblePositions,ViewDepth=ViewDepth,floorPlanName=floorPlanName)
			if stepNum!=4:
				#------------
				# Version 0.063
				# Check to make sure that the subject made a valid move.
				# If not then set ValidTrial to 0 and skip the rest of the
				# moves.
				#------------
				if 0==self.CheckIfValidMove(CurrState,MoveName[stepNum]) or 0==ValidTrial:
					DataFile=open(DataFileName,'a')
					DataFile.write("!\tInvalid Trial\n")
					DataFile.close()
					ValidTrial=0
					print "myFollowPath: Invalid Trial"
				else:
					CurrState=self.MakeState(CurrState,stepNum)
					currView=self.Nodes[CurrState[0]][CurrState[1]].View[CurrState[2]]
					OldPos=[]
					for otherPos in PossiblePositions:
						OldPos.append(self.MakeState(otherPos,stepNum))
					NewPossiblePositions=self.FindView(currView,OldPos)
					# ---------------------------------
					# Now we want to only include those possible positions that were
					# part of our original set of possible positions
					# ---------------------------------
					PossiblePositions=[]
					for OldPosItem in OldPos:
						if OldPosItem in NewPossiblePositions:
							PossiblePositions.append((OldPosItem[0],OldPosItem[1],OldPosItem[2]))
					DataFile=open(DataFileName,'a')
					#print "Length=%s\n" % len(OptimalGoToMoves)
					DataFile.write(">\t%s\t%s\t%s\t%s\t%s\t" % (oldState,stepNum,OptimalMove,OptimalGoToMoves[0],prevPositions))
					if stepNum in OptimalMove:
						DataFile.write("\t1")
						ContinueWithOptimal=1
					else: 
						DataFile.write("\t0")
						ContinueWithOptimal=0

					if stepNum in OptimalGoToMoves[0]:
						DataFile.write("\t1")
					else:
						DataFile.write("\t0")
	
					DataFile.write("\n")
					DataFile.close()
					print "Possible Positions:%s" % PossiblePositions
	
		#if len(OptimalGoToMoves)==1 and OptimalGoToMoves[0]==4:
		#	OptimalGoToMoves.append([4])
		DataFile=open(DataFileName,'a')
		DataFile.write("$\t%s\t4\t%s\t%s\t%s\t\n" % (CurrState,OptimalMove,OptimalGoToMoves[0],PossiblePositions))
		print "Done<-----------------"
		#DataFile.write(">%s\t(%s)\t%s\t%s\t%s\t%s\n" % (StartState,ViewDepth,CurrState,EndState,NumMoves,Moves))
		DataFile.close()
	def LocalizeMySelf(self,ViewDepth,StartState=(0,0,0),PossiblePositions=[],DataFile=sys.stdout):
		CurrState=StartState
		# ---------------------------------
		# First we want to check to see if the CurrState is part of
		# the possible states.
		# ---------------------------------
		# Brian, this still needs to be done.  Check to see if you can use the
		# PotentialList or the ChosenList to do this.
		NumMoves=0;
		self.ComputeAllViews(ViewDepth)
		currView=self.Nodes[CurrState[0]][CurrState[1]].View[CurrState[2]]
		# ---------------------------------
		# First we will make all of the positions "possible positions".
		# ---------------------------------
		if (PossiblePositions==[]):
			for tempPos in self.ChosenList:
				for VCount in range(4):
					PossiblePositions.append((tempPos[0],tempPos[1],VCount))
		#print "PossiblePositions1=%s" % PossiblePositions
		# ---------------------------------
		# Find all of the locations that are consistent with the current
		# View.
		# ---------------------------------
		PossiblePositions=self.FindView(currView,PossiblePositions)
		print "PossiblePositions2=%s" % PossiblePositions
		Moves=[]
		while len(PossiblePositions)>1:
			NumMoves=NumMoves+1
			OptimalMove=self.FindPosition((CurrState[0],CurrState[1]),CurrState[2],PossiblePositions,Mode=0)
			#print "Optimal Move=%s\n" % OptimalMove
			OptimalMove=random.choice(OptimalMove)
			CurrState=self.MakeState(CurrState,OptimalMove)
			Moves.append(OptimalMove)
			#print "Optimal Move=%s\n" % OptimalMove
			currView=self.Nodes[CurrState[0]][CurrState[1]].View[CurrState[2]]
			OldPos=[]
			for otherPos in PossiblePositions:
				OldPos.append(self.MakeState(otherPos,OptimalMove))
			NewPossiblePositions=self.FindView(currView,OldPos)
			print NewPossiblePositions
			# ---------------------------------
			# Now we want to only include those possible positions that were
			# part of our original set of possible positions
			# ---------------------------------
			PossiblePositions=[]
			for OldPosItem in OldPos:
				if OldPosItem in NewPossiblePositions:
					PossiblePositions.append((OldPosItem[0],OldPosItem[1],OldPosItem[2]))
		Moves.append(4)
		DataFile.write(">%s\t(%s)\t%s\t%s\t%s\n" % (StartState,ViewDepth,CurrState,NumMoves,Moves))
		return Moves
	def GenerateLayout(self):
		#---------------------------
		# Choose a random node to start
		#---------------------------
		randX=random.choice(range(self.x))
		randY=random.choice(range(self.y))
		self.Nodes[randX][randY].Active=1     #Make node active
		self.ChosenList.append((randX,randY)) #Place node on active list
		#---------------------------
		# Append previous prospect list of chosen link
		# to the list of all current Potential links
		#---------------------------
		self.PotentialList=self.Nodes[randX][randY].ProspectList[:]  
		#---------------------------
		for lencount in range(self.Length):
			#---------------------------
			# Select a random potential node
			#---------------------------
			ChosenNode=random.choice(self.PotentialList) 
			#---------------------------
			# Select one of the Active Nodes that is connected to 
			# the current chosen node.  
			# 1) Check the list of active nodes that are connected
			#    to the current node.  We are going to do this by
			#    checkin the current node's list of potential nodes.
			#---------------------------
			# Chosen Node is a random node of the Potential List.
			# Check to see all of the "prospects" from that node.
			# 
			currList=[]
			for PList in self.Nodes[ChosenNode[0]][ChosenNode[1]].ProspectList:
				if PList in self.ChosenList: 
					currList.append(PList[:])
			connectLink=random.choice(currList)
			self.Nodes[ChosenNode[0]][ChosenNode[1]].Linked.append(connectLink)
			self.Nodes[ChosenNode[0]][ChosenNode[1]].ProspectList.remove(connectLink)
			if ChosenNode not in self.ChosenList:
				self.ChosenList.append(ChosenNode)
			self.Nodes[connectLink[0]][connectLink[1]].ProspectList.remove(ChosenNode)
			self.PotentialList=[]
			for PList in self.ChosenList:
				self.PotentialList=self.PotentialList[:]+self.Nodes[PList[0]][PList[1]].ProspectList[:]
	
	def CheckIfLinked(self,currPosX,currPosY,checkPosX,checkPosY):
		if checkPosX<0 or checkPosX>=self.x or checkPosY<0 or checkPosY>=self.y:
			return 0
		if (checkPosX,checkPosY) in self.Nodes[currPosX][currPosY].Linked or (currPosX,currPosY) in self.Nodes[checkPosX][checkPosY].Linked:
			return 1
		else:
			return 0
	def DisplayParams(self,DispConn=0,DispParam=1):
		if 1==DispParam:
			print '\n----------------\nPlat Paramaters\n----------------'
			print 'X-Size=%i\nY-Size=%i' %(self.x,self.y)
			print 'Length=%i'% (self.Length)
			print '\n----------------\nConnected Nodes\n----------------'
		if 1==DispConn:
			for x in range(self.x):
				for y in range(self.y):
					if self.Nodes[x][y].Linked != []:
						print '%i,%i=>%s' % (x,y,self.Nodes[x][y].Linked)
	def ComputeView(self,OtherList,View):
		currentView=""
		Translation=self.ConvertTranslation(View,(1,0))
		if self.CheckIfLinked(OtherList[0],OtherList[1],\
				OtherList[0]+Translation[0],\
				OtherList[1]+Translation[1]):
			currentView=currentView+'Rc'
		else:
			currentView=currentView+'Rw'
		Translation=self.ConvertTranslation(View,(-1,0))
		if self.CheckIfLinked(OtherList[0],OtherList[1],\
				OtherList[0]+Translation[0],\
				OtherList[1]+Translation[1]):
			currentView=currentView+'Lc'
		else:
			currentView=currentView+'Lw'
		Translation=self.ConvertTranslation(View,(0,1))
		if self.CheckIfLinked(OtherList[0],OtherList[1],\
								OtherList[0]+Translation[0],\
								OtherList[1]+Translation[1]):
			currentView=currentView+'Fc'
		else:
			currentView=currentView+'Fw'
		return currentView
		
	def DispViews(self,Position=(-1,-1),View=-1,VisualSpan=0):
		#-------
		# We are going to check if there are any connecting nodes
		# to the N,S,E,or W.  We will then traverse the links to
		# generate the description for the observer.
		#-------
		# Check West
		# Looking west we first want to see if their are any N or S corridors
		# Views indicate whether the viewer is looking N,S,E or W.
		# 0 = W ; 1 = N ; 2 = E ; 3 = S
		#-------
		currList=[Position[0],Position[1]]
		currView=""
		currView=currView+self.ComputeView((currList[0],currList[1]),View)
		currView=re.sub('(Rc|Rw|Lw|Lc)','',currView)
		depthInc=1
		while (re.search("Fw",currView)==None and depthInc<VisualSpan):
			Translation=self.ConvertTranslation(View,(0,1))
			for i in range(2):
				currList[i]=currList[i]+Translation[i]
			currView=currView+self.ComputeView(currList,View)
			depthInc=depthInc+1
		else:
			return currView
	def ComputeAllViews(self,ViewDepth):
		# Directions=[(-1,0),(1,0),(0,-1),(0,1)]
		for View in range(4):
			for CList in self.ChosenList:
				self.Nodes[CList[0]][CList[1]].View[View]=\
				self.DispViews(CList,View,ViewDepth)
				#print "%s %s %s" % (CList,View,self.Nodes[CList[0]][CList[1]].View[View]	)
	def DisplayTextImage(self,OutputFile=sys.stdout,DispCoord=0):
		OutputFile.write(" ")
		for x in range(self.x):
			if x>9:
				stringx="%s" % x
				Base_10=string.atoi(stringx[0])
				x=x-(10*Base_10)
			if DispCoord:
				OutputFile.write("%s " % x)

		for y in range(self.y):
			for k in range(2):
				for x in range(self.x):
					if k == 0: 
						if (0==x):
							if DispCoord: OutputFile.write('%s'%y)
							OutputFile.write('\n$')
						OutputFile.write('.')
						if (x+1,y) in self.Nodes[x][y].Linked or ((x+1<self.x) and (x,y) in self.Nodes[x+1][y].Linked):
							OutputFile.write('_')
						else: OutputFile.write(' ')
					if k == 1:
						if (0==x):
							if DispCoord: OutputFile.write('%s'%y)
							OutputFile.write('\n$')
						if (x,y+1) in self.Nodes[x][y].Linked or ((y+1<self.y) and (x,y) in self.Nodes[x][y+1].Linked):
							OutputFile.write('| ')
						else: OutputFile.write('* ')
		OutputFile.write('\n')
	#------------------------------------------------------------------------
	#                      MakeResearchFile
	# This command is used to generate output files that can be used to run
	# subjects in an experiment. Version 0.02 (3/2/2000; BJS)
	#------------------------------------------------------------------------
	def MakeResearchFile(self,OutputFile=sys.stdout):
		OutputFile.write('X %s\n' % self.x)
		OutputFile.write('Y %s\n' % self.y)
		for y in range(self.y):
			for x in range(self.x):
				if (x,y) in self.ChosenList:
					OutputFile.write('@(%s,%s)->' % (x,y))
					if ((x+1,y) in self.Nodes[x][y].Linked) or ((x+1<self.x) and (x,y) in self.Nodes[x+1][y].Linked):
						OutputFile.write('(%s,%s);'%(x+1,y))
					if ((x-1,y) in self.Nodes[x][y].Linked) or ((x-1>=0) and (x,y) in self.Nodes[x-1][y].Linked):
						OutputFile.write('(%s,%s);'%(x-1,y))
					if ((x,y+1) in self.Nodes[x][y].Linked) or ((y+1<self.y) and (x,y) in self.Nodes[x][y+1].Linked):
						 OutputFile.write ('(%s,%s);'%(x,y+1))
					if ((x,y-1) in self.Nodes[x][y].Linked) or ((y-1>=0) and (x,y) in self.Nodes[x][y-1].Linked):
						 OutputFile.write ('(%s,%s);'%(x,y-1))
					OutputFile.write('\n')
	def ReadTextImage(self,InputFileName):
		INPUTFILE=open(InputFileName,'r')
		self.ChosenList=[]
		YPos=0
		for line in INPUTFILE.readlines():
			#---------------------------------------------
			# Sample input file
			#---------------------------------------------
			# $. . . . . 
			# $* * * * | 
			# $._._. . . 
			# $| * | * |  
			# $. . ._._. 
			# $| * | * |   
			# $._._. . . 
			# $* * * * | 
			# $. . . ._.
			# 
			# The $ symobol indicatest that the line is a "textdisplay"
			# line.  This will allow us to put the text display into a 
			# layout file.  
			# The '.' indicate potential intersections.
			# The '_' indicate a horizontal hallway.
			# The '|' indicate vertical hallways between intersections.
			# The '*' indicates that there is no vertical hallway and the '. .'
			# indicates that there is no horizontal hallway between the two 
			# intersections.
			#---------------------------------------------
			if line[0]=='$':
				#---------------------------------------------
				# Check to see if we are reading a horizontal
				# line or a vertical line.
				#---------------------------------------------
				if re.search('\.',line)!=None:
					#---------------------------------------------
					# Then we are on the horizontal line specifyer
					#---------------------------------------------
					ParsedLine=re.sub('\s','',line[1:])
					ParsedLine=re.split('\.',ParsedLine)
					for SegPos in range(len(ParsedLine)-1):
						if re.search('_',ParsedLine[SegPos])!=None:
							#---------------------------------------------
							# Check to see if the position is already on the "ChosenList"
							#---------------------------------------------
							#print "(%s,%s)" % (SegPos,YPos)
							if (SegPos-1,YPos) not in self.ChosenList:
								self.ChosenList.append((SegPos-1,YPos))
							if (SegPos,YPos) not in self.ChosenList:
								self.ChosenList.append((SegPos,YPos))
							self.Nodes[SegPos-1][YPos].Linked.append((SegPos,YPos))
							self.Nodes[SegPos][YPos].Linked.append((SegPos-1,YPos))
					
				else:
					#---------------------------------------------
					# Then we are on the horizontal line specifyer
					#---------------------------------------------
					ParsedLine=re.split('\s+',line[1:-1])
					for SegPos in range(len(ParsedLine)-1):
						if re.search('\|',ParsedLine[SegPos])!=None:
							if (SegPos,YPos) not in self.ChosenList:
								self.ChosenList.append((SegPos,YPos))
							if (SegPos,YPos+1) not in self.ChosenList:
								self.ChosenList.append((SegPos,YPos+1))
							self.Nodes[SegPos][YPos].Linked.append((SegPos,YPos+1))
							self.Nodes[SegPos][YPos+1].Linked.append((SegPos,YPos))
					YPos=YPos+1
		INPUTFILE.close()
	def ReadResearchFile(self,InputFileName):
		INPUTFILE=open(InputFileName,'r')
		self.ChosenList=[]
		for line in INPUTFILE.readlines():
			# --------------------------------
			# Sample output file that is read by this function.
			# pound (#) signs indicate a comment
			# @ sign indicates an intersection in the chosen list.
			# --------------------------------
			# $  0 1 2 3 4 
			# $0. . ._. . 
			# $   | | |   
			# $1._._._. . 
			# $   |   |   
			# $2. . ._. . 
			# $           
			# $3. . . . . 
			# $           
			# $4. . . . . 
			# $           
			# #[(3, 0), (2, 0), (2, 1), (1, 1), (3, 1), (1, 0), (3, 2), (1, 2), (0, 1), (2, 2)]
			# @(1,0)->[1,1];
			# @(2,0)->[3,0];[2,1];
			# @(3,0)->[2,0];[3,1];
			# @(0,1)->[1,1];
			# @(1,1)->[2,1];[0,1];[1,2];[1,0];
			# @(2,1)->[3,1];[1,1];[2,0];
			# @(3,1)->[2,1];[3,2];[3,0];
			# @(1,2)->[1,1];
			# @(2,2)->[3,2];
			# @(3,2)->[2,2];[3,1]
			# --------------------------------
			if re.search('@',line)!=None:
				(Node,ConnectedNode)=string.split(line,'->')
				NewNode=re.sub('[()@]','',Node)
				NewNode=string.split(NewNode,',')
				iNewNode=(string.atoi(NewNode[0]),string.atoi(NewNode[1]))
				self.ChosenList.append(iNewNode[0],iNewNode[1])
				CNodes=string.split(ConnectedNode[0:-2],';')
				for CurrNode in CNodes:
					temp=re.sub('[()]','',CurrNode)
					temp=string.split(temp,',')
					#self.Nodes[SegPos-1][YPos].Linked.append(SegPos,YPos)
					temp=(string.atoi(temp[0]),string.atoi(temp[1]))
					self.Nodes[iNewNode[0]][iNewNode[1]].Linked.append(temp)
				#print '%s:%s\n--------------\n' % (iNewNode,self.Nodes[iNewNode[0]][iNewNode[1]].Linked)
	#------------------------------------------------------------------------
	#                      DisplayVRMLLayout
	# This command is used to generate the vrml text file for use with the
	# viz program.
	#------------------------------------------------------------------------
	def DisplayVRMLLayout(self,OutputFile=sys.stdout,width=1,height=1,length=3,thickness=0.05,hallway_texture = "./SharedMedia/Textures/cement1.jpg",wall_texture = "./SharedMedia/Textures/cement1.jpg",floor_texture = "./SharedMedia/Textures/burlap.jpg",ceiling_texture = "./SharedMedia/Textures/cement1.jpg"):
		DidDefWall=0
		DidDefHall=0
		DidDefFloor=0
		length += width
		walldefinition = ('   children DEF WALL Group {\n    children [\n     Transform {\n'
						+'      translation 0 0 0\n      children[\n       Shape {\n'
						+'        appearance Appearance {\n         material Material {\n'
						+'          diffuseColor 0 0 0\n          emissiveColor 0 0 0 \n'
						+'         }\n         texture ImageTexture {\n'
						+'          url "%s"\n'%(wall_texture)
						+'         }\n        }\n        geometry Box {\n'
						+'         size %f %f %f\n'%(thickness,height,width)
						+'        }\n       }\n      ]\n     }\n'
						+'    ]\n   }\n  },')
		halldefinition = ('   children DEF HALL Group {\n    children [\n     Transform {\n'
						+'      translation %f 0 0\n'%(-width/2.0)
						+'      children[\n       Shape {\n        appearance Appearance {\n'
						+'         texture ImageTexture {\n'
						+'          url "%s"\n'%(hallway_texture)
						+'         }\n        }\n        geometry Box {\n'
						+'         size %f %f %f\n'%(thickness,height,length-width)
						+'        }\n       }\n      ]\n     },\n'
						+'     Transform {\n      translation %f 0 0\n'%(width/2.0)
						+'      children[\n       Shape {\n        appearance Appearance {\n'
						+'         texture ImageTexture {\n'
						+'          url "%s"\n'%(hallway_texture)
						+'         }\n        }\n        geometry Box {\n'
						+'         size %f %f %f\n'%(thickness,height,length-width)
						+'        }\n       }\n      ]\n     },\n'
						+'     Transform {\n      translation 0 %f 0\n'%(-height/2.0)
						+'      children [\n       Shape {\n'
						+'        appearance Appearance {\n         texture ImageTexture {\n'
						+'          url "%s"\n'%(floor_texture)
						+'         }\n        }\n        geometry Box {\n'
						+'         size %f %f %f\n'%(width,thickness,length-width)
						+'        }\n       }\n      ]\n     },\n'
						+'     Transform {\n      translation 0 %f 0\n'%(height/2.0)
						+'      children [\n       Shape {\n'
						+'        appearance Appearance {\n         texture ImageTexture {\n'
						+'          url "%s"\n'%(ceiling_texture)
						+'         }\n        }\n        geometry Box {\n'
						+'         size %f %f %f\n'%(width,thickness,length-width)
						+'        }\n       }\n      ]\n     },\n'
						+'     Transform {\n      translation 0 %f 0\n'%(height+length*0.1)
						+'      children [\n       Shape {\n        appearance Appearance {\n'
						+'         material Material {\n          diffuseColor  1 1 1\n'
						+'          emissiveColor 1 1 1\n         }\n        }\n'
						+'        geometry IndexedFaceSet {\n         coord Coordinate {\n'
						+'          point [\n           %f 0 %f,\n'%(-width/2.0,-(length-width)/2.0)
						+'           %f 0 %f,\n           %f 0 %f,\n'%(-width/2.0,(length-width)/2.0,width/2.0,(length-width)/2.0)
						+'           %f 0 %f\n          ]\n         }\n'%(width/2.0,-(length-width)/2.0)
						+'         coordIndex[0,1,2,3,-1]\n'
						+'        }\n       }\n      ]\n     }\n'  
						+'    ]\n   }\n  },')
		floordefinition = ('   children DEF FLOOR Group {\n    children [\n     Transform {\n'
						+'      translation 0 %f 0\n'%(-height/2.0)
						+'      children [\n       Shape {\n'
						+'        appearance Appearance {\n         texture ImageTexture {\n'
						+'          url "%s"\n'%floor_texture
						+'         }\n        }\n        geometry Box {\n'
						+'         size %f %f %f\n'%(width,thickness,width)
						+'        }\n       }\n      ]\n     },\n'
						+'     Transform {\n      translation 0 %f 0\n'%(height/2.0)
						+'      children [\n       Shape {\n        appearance Appearance {\n'
						+'         texture ImageTexture {\n'
						+'          url "%s"\n'%(ceiling_texture)
						+'         }\n        }\n        geometry Box {\n'
						+'         size %f %f %f\n'%(width,thickness,width)
						+'        }\n       }\n      ]\n     },\n'
						+'     Transform {\n      translation 0 %f 0\n'%(height+length*0.1)
						+'      children [\n       Shape {\n        appearance Appearance {\n'
						+'         material Material {\n          diffuseColor  1 1 1\n'
						+'          emissiveColor 1 1 1\n         }\n        }\n'
						+'        geometry IndexedFaceSet {\n         coord Coordinate {\n'
						+'          point [\n           %f 0 %f,\n'%(-width/2.0,-width/2.0)
						+'           %f 0 %f,\n           %f 0 %f,\n'%(-width/2.0,width/2.0,width/2.0,width/2.0)
						+'           %f 0 %f\n          ]\n         }\n'%(width/2.0,-width/2.0)
						+'         coordIndex[0,1,2,3,-1]\n'
						+'        }\n       }\n      ]\n     }\n'
						+'    ]\n   }\n  },')
		OutputFile.write('#VRML V2.0 utf8\n')
		OutputFile.write('#*SCALE*(width,height,length,thickness): %f %f %f %f\n\n'%(width,height,length-width,thickness))
		OutputFile.write('Group {\n')
		OutputFile.write(' children [')
		#OutputFile.write('  Transform {\n')
		#OutputFile.write('   children  DEF HALL Inline {\n')
		#OutputFile.write('    url \"HALL.wrl\"\n')
		#OutputFile.write('   }\n')
		#OutputFile.write('  },\n')
		#OutputFile.write('  Transform {\n')
		#OutputFile.write('   children  DEF WALL Inline {\n')
		#OutputFile.write('    url \"Wall.wrl\"\n')
		#OutputFile.write('   }\n')
		#OutputFile.write('  },\n')
		#------------------------------------------------------------------------
		# We will step through all of the x (self.x) and y (self.y) potential
		# positions to see if the node was selected.
		#------------------------------------------------------------------------
		#print '%s' % self.ChosenList
		for y in range(self.y):
			#for k in range(2):
			for x in range(self.x):
				if (x,y) in self.ChosenList:
					#--------------------------------
					# Lay down floor and place ceiling
					#--------------------------------
					OutputFile.write('\n  Transform {\n   translation %f 0 %f\n   rotation 0 0 0 0\n'% (((x)*length),((y)*length)))
					if 1==DidDefFloor:
						OutputFile.write('   children USE FLOOR\n  },') 
					else: 
						#OutputFile.write('   children  DEF FLOOR Inline {\n    url \"FLOOR.wrl\"\n')
						#OutputFile.write('   }\n  },\n')
						OutputFile.write(floordefinition)
						DidDefFloor=1
					if (x-1<0) or ((x-1,y) not in self.Nodes[x][y].Linked and (x,y) not in self.Nodes[x-1][y].Linked):
						OutputFile.write('\n  Transform {\n   translation %f 0 %f\n   rotation 0 1 0 0\n'% (((x)*length)-(width/2.0),((y)*length)))
						if 1==DidDefWall:
							OutputFile.write('   children USE WALL\n  },') 
						else:
							#OutputFile.write('   children  DEF WALL Inline {\n    url \"WALL.wrl\"\n')
							#OutputFile.write('   }\n  },\n')
							OutputFile.write(walldefinition)
							DidDefWall=1
					if (x+1>=self.x) or ((x+1,y) not in self.Nodes[x][y].Linked and (x,y) not in self.Nodes[x+1][y].Linked):
						OutputFile.write('\n  Transform {\n   translation %f 0 %f\n   rotation 0 1 0 0\n' % ((x*length)+(width/2.0),(y*length)))
						if 1==DidDefWall:
							OutputFile.write('   children USE WALL\n  },')
						else:
							#OutputFile.write('   children  DEF WALL Inline {\n    url \"WALL.wrl\"\n')
							#OutputFile.write('   }\n  },\n')
							OutputFile.write(walldefinition)
							DidDefWall=1
					if (y+1>=self.y) or ((x,y+1) not in self.Nodes[x][y].Linked and (x,y) not in self.Nodes[x][y+1].Linked):
						OutputFile.write('\n  Transform {\n   translation %f 0 %f\n   rotation 0 1 0 1.5708\n' % ((x*length),(y*length)+(width/2.0)))
						if 1==DidDefWall:
							OutputFile.write('   children USE WALL\n  },')
						else:
							#OutputFile.write('   children  DEF WALL Inline {\n    url \"WALL.wrl\"\n')
							#OutputFile.write('   }\n  },\n')
							OutputFile.write(walldefinition)
							DidDefWall=1
					if (y-1<0) or ((x,y-1) not in self.Nodes[x][y].Linked and (x,y) not in self.Nodes[x][y-1].Linked):
						OutputFile.write('\n  Transform {\n   translation %f 0 %f\n   rotation 0 1 0 1.5708\n' % (((x)*length),((y)*length)-(width/2.0)))
						if 1==DidDefWall:
							OutputFile.write('   children USE WALL\n  },')
						else:
							#OutputFile.write('   children  DEF WALL Inline {\n    url \"WALL.wrl\"\n')
							#OutputFile.write('   }\n  },\n')
							OutputFile.write(walldefinition)
							DidDefWall=1
					if (x+1,y) in self.Nodes[x][y].Linked or ((x+1<self.x) and (x,y) in self.Nodes[x+1][y].Linked):
						OutputFile.write('\n  Transform {\n   translation %f 0 %f\n   rotation 0 1 0 1.5708\n' % (((x)*length)+(length/2.0),((y)*length)))
						if 1==DidDefHall:
							OutputFile.write('   children USE HALL\n  },')
						else:
							#OutputFile.write('   children  DEF HALL Inline {\n    url \"HALL.wrl\"\n')
							#OutputFile.write('   }\n  },\n')
							OutputFile.write(halldefinition)
							DidDefHall=1
					if (x,y+1) in self.Nodes[x][y].Linked or ((y+1<self.y) and (x,y) in self.Nodes[x][y+1].Linked):
						OutputFile.write('\n  Transform {\n   translation %f 0 %f\n   rotation 0 1 0 0\n' % (((x)*length),((y)*length)+(length/2.0)))
						if 1==DidDefHall:
							OutputFile.write('   children USE HALL\n  },')
						else:
							#OutputFile.write('   children  DEF HALL Inline {\n    url \"HALL.wrl\"\n')
							#OutputFile.write('   }\n  },\n')
							OutputFile.write(halldefinition)
							DidDefHall=1
		OutputFile.write('\n ]\n}\n')
	def FindView(self,targetView,listState):
		potentialView=[]
		for currState in listState:
			#print currState
			if targetView == self.Nodes[currState[0]][currState[1]].View[currState[2]]:
				potentialView.append(currState)
		return (potentialView)
	def IncramentProbDist(self,view,ProbList):
		if ProbList.has_key(view):
			ProbList[view]=ProbList[view]+1.0
		else:
			ProbList[view]=1.0
	def GetProbDist(self,PositionList):
		ProbList={}
		RotList=[1,-1]
		for rot in RotList:
			for currPos in PositionList:
				if 3==currPos[1] and 1==rot:
					rot=-3
				self.IncramentProbDist(self.Nodes[currPos[0][0]][currPos[0][1]].View[currPos[1]+rot],ProbList)
		for view in ProbList.keys():
			ProbList[view]=ProbList[view]/(2*len(PositionList))
		return ProbList
	def GetEntropy(self,PotentialPositions,TestMove): 	
		ProbList={}
		#----------------------------------------------
		# Test move is a three element
		# tuple.  The first and second are the X and Y
		# translations, and the third is the rotation.
		# (dx,dy,dr) -dr = left rotation
		# PotentialPositions is the list of the currently
		# considered positions.
		#----------------------------------------------
		# We are going to rotate the observer and return
		# the view that we expect to see.
		myPosition=[]
		Entropy=0
		for currPosition in PotentialPositions:
			rotation=TestMove[2]+currPosition[1]
			if 3<rotation:
				rotation=0
			if 0>rotation:
				rotation=3
			self.IncramentProbDist(self.Nodes[currPosition[0][0]][currPosition[0][1]].View[rotation],ProbList)
			myPosition.append(currPosition)
		# Computet the probabilities
		for view in ProbList.keys():
			ProbList[view]=ProbList[view]/len(PotentialPositions)
		for currPosition in myPosition:
			rotation=TestMove[2]+currPosition[1]
			if 3<rotation:
				rotation=0
			if 0>rotation:
				rotation=3
			Entropy=Entropy-\
					ProbList[self.Nodes[currPosition[0][0]]\
					[currPosition[0][1]].View[rotation]]*\
					math.log(ProbList[self.Nodes[currPosition[0][0]]\
					[currPosition[0][1]].View[rotation]])
		return Entropy
	def PrintViews(self):
		ViewDesc=['West','North','East','South']
		for i in range(4):
			print '\n',ViewDesc[i],'Views\n_________'
			for CList in self.ChosenList:
				print CList,self.Nodes[CList[0]][CList[1]].View[i]
	def CheckIfValidMove(self,Position,currMove):
		currView=self.Nodes[Position[0]][Position[1]].View[Position[2]]
		#if re.search("SlideRight",currMove)!=None and re.search("^Rc",currView)!=None :
		#	ValidMove=1
		#elif re.search("SlideLeft",currMove)!=-1 and re.search("^R[cw]Lc",currView)!=None:
		#	ValidMove=1
		if re.search("Forward",currMove)!=None and re.search("^Fc",currView)!=None:
			ValidMove=1
		elif re.search("RotateLeft",currMove)!=None:
			ValidMove=1
		elif re.search("RotateRight",currMove)!=None:
			ValidMove=1
		else: ValidMove=0
		return ValidMove		
	#----------
	# Version 0.04 BJS
	# FindPosition will have two modes:
	# "Where am I" mode (mode=0)
	# "Am I there yet" mode (mode = 1)
	def FindPosition(self,Position,currDirection,PossiblePositions,Mode=1,EndPosition=(0,0,0),Weighting=[1,1,1]):
		Views=[(-1,0),(0,-1),(1,0),(0,1)]
		PossibleViews=[]
		PossibleOrn=[]
		if PossiblePositions==[]:
			for position in self.ChosenList:
				for vCount in range(4):
					PossiblePositions.append((position[0],position[1],vCount))
		currView=self.Nodes[Position[0]][Position[1]].View[currDirection]
		#print "Starting View=%s" % currView
		#print "Starting State=(%s,%s)" % (Position,currDirection)
		#print "----------------------------"
		#PossiblePositions=self.FindView(currView,PossiblePositions)
		#print "Possible Positions"
		#print "-------------------"
		#print 'FindPosition(PossiblePositions):%s' % len(PossiblePositions)
		MovedToPosition=[Position[0],Position[1],currDirection]
		#----------
		# The following loop will spawn all of the possible
		# positions.  It will continue to spawn until one of the search
		# robots is able to reduce the uncertainty down to 0.  We will do this
		# for each potential position.  We will also keep track of how many steps
		# each potential position takes to find a solution.
		#----------
		currTestPath=TESTPATH()
		#---------
		# consideredMoved is considering one move ahead for all of the 
		# positions.  
		#---------
		for consideredMove in range(len(MoveName)):
			currTestPath.MinCost[consideredMove]={}
			currTestPath.Path[consideredMove]={}
			currTestPath.Done[consideredMove]={}
			currTestPath.NumSteps[consideredMove]={}
			currTestPath.OptimalPath[consideredMove]={}
			currTestPath.CurrPosition[consideredMove]={}
			#--------
			# Loop through all of the possible positions
			#--------
			#print ">>>>>>><<<<<<<<<<<<<<\n%s\n>>>>>>><<<<<<<<<<<<<<" % PossiblePositions
			for consideredPosition in PossiblePositions:
				print "ConsideredMove=%s" % consideredMove
				currTestPath.OtherCurrPositions[consideredMove]={}

				#print '----------------\nStart Num Poss. Pos.: %s\nconsideredPosition=%s\n------------------' % (len(PossiblePositions),consideredPosition)
				#print "consideredMove=%s\nconsideredPosition=%s\n==============\n" % (consideredMove,consideredPosition)
				currTestPath.Done[consideredMove][consideredPosition]=0
				currTestPath.MinCost[consideredMove][consideredPosition]=999999
				currTestPath.View[consideredMove]={}
				currTestPath.Cost[consideredMove]={}
				#print "Considering %s at %s" % (MoveName[consideredMove],consideredPosition)
				currTestPath.StartPosition=consideredPosition
				#-----------
				# Place position that is not currently being considered
				# in the "othercurrpositions" list
				#-----------
				currTestPath.OtherCurrPositions[consideredMove]["%s" % consideredMove]=[]
				for otherPosition in PossiblePositions:
					#print "Considered Position:%s -- Other Position: %s" % (consideredPosition,otherPosition)
					currTestPath.OtherCurrPositions[consideredMove]["%s" % consideredMove].append(otherPosition)
				#--------
				# Move the virtual viewer to the 
				# appropriate position.  However, first we need to make sure that
				# the move is a valid one.
				#--------
				if 1==self.CheckIfValidMove(consideredPosition,MoveName[consideredMove]):
					#--------
					# If the move is valid, then move the viewer to the new
					# position
					#--------
					currTestPath.CurrPosition[consideredMove]["%s" % consideredMove]=\
						self.MakeState(consideredPosition,consideredMove)
					currPosition=currTestPath.CurrPosition[consideredMove]["%s" % consideredMove]
					#-----
					# Generate the new view for the move
					#-----
					currView=self.Nodes[currPosition[0]][currPosition[1]].View[currPosition[2]]
					currTestPath.View[consideredMove]["%s" % consideredMove]=currView

					#--------
					# Incrament all of the other views by the movement
					# and see which positions produce the same view
					#--------
					tempPosition=[]
					for otherPosition in currTestPath.OtherCurrPositions[consideredMove]["%s" % consideredMove]:
						tempPosition.append(self.MakeState(otherPosition,consideredMove))
					#print "tempPosition=%s" % tempPosition
					#--------
					# Check to see if the new position generates the same
					# view as the expected view
					#--------
					currTestPath.OtherCurrPositions[consideredMove]["%s" % consideredMove]=self.FindView(currView,\
					tempPosition)
					#print "PossiblePositions=%s" % PossiblePositions
					#print "currTestPath.OtherCurrPositions=%s" % currTestPath.OtherCurrPositions[consideredMove]["%s" % consideredMove]
					#--------
					# Check to see if we have already eliminated all of the
					# possible other positions.  If we have, then we are done with
					# this position.  If not, then we need to keep moving through
					#--------
					# Version 0.04 3/8/2000
					# Modifying the following conditional statement.  We are going to have this function run in
					# two different modes.  One mode is "where am I" mode.  And the second is the "Am I there yet"
					# mode.  Depending on the mode we will do a different conditional.
					#--------
					if 0==Mode:
						if 1==len(currTestPath.OtherCurrPositions[consideredMove]["%s" % consideredMove]):
							#print "Did it without searching (%s -- %s)" % (consideredMove,consideredPosition)
							currTestPath.Done[consideredMove][consideredPosition]=1
							currTestPath.MinCost[consideredMove][consideredPosition]=Weighting[consideredMove]
							currTestPath.NumSteps[consideredMove][consideredPosition]=1
						else:
							currTestPath.Done[consideredMove][consideredPosition]=0
							currTestPath.NumSteps[consideredMove][consideredPosition]=1

					if 1==Mode:
						if (1 == len(currTestPath.OtherCurrPositions[consideredMove]["%s" % consideredMove])) and\
						(EndPosition == consideredPosition):
							currTestPath.Done[consideredMove][consideredPosition]=1
							currTestPath.NumSteps[consideredMove][consideredPosition]=1
							currTestPath.MinCost[consideredMove][consideredPosition]=Weighting[consideredMove]
						else:
							currTestPath.Done[consideredMove][consideredPosition]=0
							currTestPath.NumSteps[consideredMove][consideredPosition]=1
					#--------
					# End of Modification for version 0.04
					#--------
				else:
					currTestPath.Done[consideredMove][consideredPosition]=1
					currTestPath.NumSteps[consideredMove][consideredPosition]=99999
					currTestPath.MinCost[consideredMove][consideredPosition]=99999
					currTestPath.Path[consideredMove][consideredPosition]=[5]
				#-------
				# Now we have all of the initial movments set up
				# we need to incrament through all of the movements past
				# the first movement
				#-------
				# The following loop spawns all of the considered states.
				#-------
				# Version 0.063
				# We want to eliminate redundant movmements.  These movements are
				# Left followed by a right with no change in the length of the possible 
				# positions. 
				# We are doing this to try and reduce the computations necessary and the
				# memory load.
				#-------
				currPath=currTestPath.OtherCurrPositions[consideredMove].keys()
				#currPath=currTestPath.OptimalPath.keys()
				print "currPath=%s" % currPath
				currTestPath.OptimalPath[consideredMove][consideredPosition]=[]
				#BeenThere=[]
				if currTestPath.Done[consideredMove][consideredPosition]!=1:
					print "Running not done"
					#---------
					# Version 0.063
					# Set the "BeenThere" variable to null.  This variable is
					# used to check if the viewer has been at a position already or not
					#---------
					#print '---------------\nFindPosition: Reset BeenThere\n-----------------'
					BeenThere=[currTestPath.OtherCurrPositions[consideredMove]["%s" % consideredMove]]
					#print "BeenThere=%s" % BeenThere
					for consideredPath in currPath:
						#print "ConsideredPath=",consideredPath
						#---------------
						#consideredPath=1
						#consideredPath=10
						#consideredPath=11
						#consideredPath=12
						#consideredPath=100
						#consideredPath=101
						#print "consideredPath=%s" % consideredPath
						#---------------
						# Need to check if the current cost excedes the MinCost
						# --------------
						currCost=0
						for moveItem in consideredPath:
							currCost=currCost+Weighting[string.atoi(moveItem)]
						if currCost>currTestPath.MinCost[consideredMove][consideredPosition]:
							print ">>>>>>>>>>> Done with %s , %s" % (consideredMove,consideredPosition)
							break
						for currMove in MoveName:
							#---------
							# Check to see if we can make the "currMove" at the
							# current location.  If we can, then make the move for
							# all of the other considered locations.
							#---------
							# Version 0.063
							# Check for redundancy.
							# We will check for redundancy by removing positions that have already
							# been visited.
							#------
							currCost=0
							for moveItem in consideredPath:
								currCost=currCost+Weighting[string.atoi(moveItem)]
							#holdPath="%s%s" % (consideredPath,MoveNum[currMove])
							
							holdPositions=[]
							#print "currTestPath.OtherCurrPositions=%s" % currTestPath.OtherCurrPositions[consideredMove][consideredPath]
							for otherNodes in currTestPath.OtherCurrPositions[consideredMove][consideredPath]:
								#print "OtherNodes=%s" % otherNodes
								holdPositions.append(self.MakeState(otherNodes,MoveNum[currMove]))
							tempPos=self.MakeState(currTestPath.CurrPosition[consideredMove][consideredPath],MoveNum[currMove])
							#print "tempPos=(%s,%s,%s)" % (tempPos[0],tempPos[1],tempPos[2])
							tempView=self.Nodes[tempPos[0]][tempPos[1]].View[tempPos[2]]

							holdPositions=self.FindView(tempView,holdPositions)
							#holdPositions.append(tempPos)
							#print "FindPosition(holdPath):\t%s" % holdPath
							#print "BeenThere:%s" % BeenThere
							repeat=0
							#print "BeenThere=%s" % BeenThere
							for testPos in BeenThere:	
								#print "%s==%s : %s : %s" % (testPos,holdPositions,currMove,currTestPath.CurrPosition[consideredMove][consideredPath])
								if "%s" % testPos == "%s" % holdPositions:
									repeat=1
									break

							#print "Trying %s repeat=%s" % (currMove,repeat)
							if self.CheckIfValidMove(currTestPath.CurrPosition[consideredMove][consideredPath],currMove) and \
								0==repeat and \
								(currCost+Weighting[MoveNum[currMove]])<currTestPath.MinCost[consideredMove][consideredPosition]:
								#(holdPositions not in BeenThere) and \
								newPath="%s%s" % (consideredPath,MoveNum[currMove])

								currPath.append(newPath)
								currTestPath.CurrPosition[consideredMove][newPath]=\
									self.MakeState(currTestPath.CurrPosition[consideredMove][consideredPath],MoveNum[currMove])
								currTestPath.View[consideredMove][newPath]=\
									self.Nodes[currTestPath.CurrPosition[consideredMove][newPath][0]]\
									[currTestPath.CurrPosition[consideredMove][newPath][1]].View\
									[currTestPath.CurrPosition[consideredMove][newPath][2]]
								

								#-------------
								# Now we need to make the new view for the other positions to see
								# if we are going to get a unique view yet.
								#-------------
								tempOtherPath=[]
								#print "OtherCurrPos:%s" % currTestPath.OtherCurrPositions[consideredMove][consideredPath] 
								for otherNodes in currTestPath.OtherCurrPositions[consideredMove][consideredPath] :
									tempOtherPath.append(self.MakeState(otherNodes,MoveNum[currMove]))
									#-------------
									# Check to see if the other nodes produce the same view
									# as the currently considered node.
									#-------------
								# Brian, this looks suspicious.
								currTestPath.OtherCurrPositions[consideredMove][newPath]=self.FindView(currTestPath.View[consideredMove][newPath],tempOtherPath)
								#print "tempOtherPath=%s" % tempOtherPath
								#print "BeenThere before append=%s" % BeenThere
								if len(tempOtherPath)>0:
									BeenThere.append(tempOtherPath)
								#print "BeenThere after append=%s" %  BeenThere								
								#BeenThere.append("%s" % currTestPath.CurrPosition[consideredMove][newPath])
								#print "newPath=%s : Position=%s : Move=%s : cost=%s : MinCost=%s : len(BeenThere)=%s" % (newPath,consideredPosition,consideredMove,currCost+Weighting[MoveNum[currMove]],currTestPath.MinCost[consideredMove][consideredPosition],len(BeenThere))

								#--------
								# Version 0.04 3/8/2000
								# Modifying the following conditional statement.  We are going to have this function run in
								# two different modes.  One mode is "where am I" mode.  And the second is the "Am I there yet"
								# mode.  Depending on the mode we will do a different conditional.
								#--------
								if 0==Mode and len(currTestPath.OtherCurrPositions[consideredMove][newPath])==1:
									currCost=0
									for moveItem in newPath:
										currCost=currCost+Weighting[string.atoi(moveItem)]
									if currCost<currTestPath.MinCost[consideredMove][consideredPosition]:
										currTestPath.MinCost[consideredMove][consideredPosition]=currCost
										currTestPath.OptimalPath[consideredMove][consideredPosition]=newPath
									del newPath
									break
								elif (1==Mode or 2==Mode) and len(currTestPath.OtherCurrPositions[consideredMove][newPath])==1 and\
								currTestPath.CurrPosition[consideredMove][newPath][0]==EndPosition[0] and\
								currTestPath.CurrPosition[consideredMove][newPath][1]==EndPosition[1]:
									#currTestPath.NumSteps[consideredMove][consideredPosition]=len(newPath)
									#-------------
									# Version 0.063
									# We are going to output the path and the current move to a file for
									# a lookup.  This should speed things along a little bit more.  The file will
									# be titled _MOVECHECK.DAT.
									# The data will be put in the following format:
									# State	Move	NumMoves
									#-------------
									currCost=0
									for moveItem in newPath:
										currCost=currCost+Weighting[string.atoi(moveItem)]
									if currCost<currTestPath.MinCost[consideredMove][consideredPosition]:
										currTestPath.MinCost[consideredMove][consideredPosition]=currCost
										currTestPath.OptimalPath[consideredMove][consideredPosition]=newPath
									# ---------------
									# Check other moves to see if less than current
									# ---------------
									
									#currTestPath.Done[consideredMove][consideredPosition]=1
									#print ">>>MinCost=%s" % currTestPath.MinCost[consideredMove][consideredPosition]
									#currTestPath.OptimalPath[consideredMove][consideredPosition]=newPath
									
									del newPath
									break
					del currTestPath.CurrPosition[consideredMove][consideredPath]
					del currTestPath.OtherCurrPositions[consideredMove]["%s" % consideredPath]
				del currTestPath.View[consideredMove]
		MinMove=99999
		BestMove=[]
		ListMove={}
		SumList=[]
		for consideredMove in currTestPath.MinCost.keys():
			SumMove=0
			for consideredPosition in currTestPath.MinCost[consideredMove].keys():
				print "---------------------------------"
				print "MinCost=%s\nMove=%s" %  (currTestPath.MinCost[consideredMove][consideredPosition],consideredMove)
				print "Path=%s\nconsideredPosition=%s" % (currTestPath.OptimalPath[consideredMove][consideredPosition],consideredPosition)
				print "---------------------------------\n"
				SumMove=SumMove+currTestPath.MinCost[consideredMove][consideredPosition]
			if SumMove<MinMove:
				BestMove=[consideredMove]
				MinMove=SumMove
			elif SumMove==MinMove:
				BestMove.append(consideredMove)
				MinMove=SumMove
			ListMove[SumMove]=consideredMove
			SumList.append(SumMove)
		if Mode==2:
			SumList.sort()
			print '------>',SumList
			return ListMove[SumList[1]]
		else:
			#print "BestMove=%s\n------------------\n" % BestMove		
			return BestMove
	def ConvertTranslation(self,Direction,InputMove):
		Movement=[]
		# West
		Movement.append(((0,1),(0,-1),(-1,0),(1,0)))
		# North
		Movement.append(((-1,0),(1,0),(0,-1),(0,1)))
		# East
		Movement.append(((0,-1),(0,1),(1,0),(-1,0)))
		# South
		Movement.append(((1,0),(-1,0),(0,1),(0,-1)))
		# Slide Left
		if InputMove==(-1,0): currMove=0
		# Slide Right
		if InputMove==(1,0): currMove=1
		# Forward
		if InputMove==(0,1): currMove=2
		# Backward
		if InputMove==(0,-1): currMove=3
		Translation=Movement[Direction][currMove]
		return Translation
	def MakeState(self,currState,MoveNum):
		
		Move=MoveDesc[MoveNum]
		if 0==Move[2]:
			Translation=self.ConvertTranslation(currState[2],(Move[0],Move[1]))
			MovedToPosition=[currState[0]+Translation[0],currState[1]+Translation[1],currState[2]]
		else: 
			MovedToPosition=[currState[0],currState[1],currState[2]+Move[2]]
		if MovedToPosition[2]>3: MovedToPosition[2]=0
		if MovedToPosition[2]<0: MovedToPosition[2]=3
		return MovedToPosition
