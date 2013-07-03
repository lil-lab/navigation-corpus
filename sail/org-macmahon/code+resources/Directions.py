"""Directions.py:
  Control Script for Human Route Instrucitons Study.

Select Option HMD for Position Group 1 (else 0)
Select Option Fullscreen for Fullscreen mode
Select Option 1 for Following Directions
Select Option 2 to skip training in Giving Directions
Select Option Tracker to take snapshots
Init Message is "Initials Env [C|D] [subjNumber] [startNum]"
C is for Continuous movement, D is Discrete movement (default).
"""
from Tkinter import *
import tkSimpleDialog, tkMessageBox, tkFont
import sys, os, string
try:
    import pychecker.checker
except ImportError: pass
sys.path.append('./NavigationModules')
import Train, viz, SoundQueue

class DirectionDialog(tkSimpleDialog.Dialog):
	def __init__(self, parent=None, title="Enter Directions", filename="Default_Dirs.txt",
				dir='Directions', state=DISABLED, startPos=0, endPos=0):
		self.filename = filename
		self.directory = dir
		self.state=state
		self.startPos=startPos
		self.endPos=endPos
		self.directions=None
		if parent == None:
			parent=Tk()
		tkSimpleDialog.Dialog.__init__(self,parent,title)
	def body(self,parent):
		self.font=tkFont.Font(family="Times", size=15, weight=tkFont.BOLD)
		self.directionEntry=Text(parent,wrap=WORD,state=self.state,font=self.font)
		if self.state==NORMAL:
			instructions='Enter directions to get from Position %d to Position %d '%(self.startPos, self.endPos)
		else:
			instructions="Follow these directions to the best of your ability"
			self.directionEntry.config(state=NORMAL)
			files = getFiles(self.filename, self.directory)
			if not files: return self.directionEntry
			filename = files[0]
			filepath = os.path.join(self.directory, filename)
			print filepath
			file = open(filepath,'r')
			self.directionEntry.insert(END,file.read())
			print self.filename
			print file.read()
			file.close()
			self.directionEntry.config(state=self.state)
		Label(parent,text=instructions,anchor=W,font=self.font).pack()
		self.scrollbar = Scrollbar(parent,command=self.directionEntry.yview)
		self.scrollbar.pack(side=RIGHT, fill=Y)
		self.directionEntry.pack()
		self.directionEntry.config(yscrollcommand=self.scrollbar.set)
		return self.directionEntry
	def cancel(self, event=None):
		self.parent.destroy()
	def apply(self):
		self.directions=self.directionEntry.get(0.0,END)
		if self.state==NORMAL and self.filename:
			matches=getFiles(self.filename,self.directory)
			self.filename+="_"+`len(matches)+1`+".txt"
			file = open(os.path.join(self.directory,self.filename),'w')
			file.write(self.directions)
			file.close()
	def buttonbox(self):
		# overriden to change behavior for <Return>
		box = Frame(self)
		w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
		w.pack(side=LEFT, padx=5, pady=5)
		box.pack()

class CompetencyTest:
	def __init__(self,prefix="Default",env="",list=[],group=0):
		self.QuizList=list
		self.prefix=prefix
		self.startPos=None
		self.endPos=None
		self.env=env
		self.group=group
	def setTrain(self,train):
		self.QuizList=Train.generatePairs()
#		self.QuizList=[[1, 5], [3, 1], [2, 3], [5, 2]]
		train.numSuccess=0
		train.numGoodTrials=numGoodTrials
		self.numTrials=0
		self.maxTrials=25
		train.resetTrain()
		SoundQueue.ClearAllSounds()
		SoundQueue.PlaySound('SharedMedia/Sounds/ExploreFreely.wav')
	def Prep(self,train):
		#print "Finished BoundedWander, Start Competency Test"
		train.onFinish=self.Test
		(self.startPos,self.endPos)=self.QuizList.pop()
		train.resetTrain()
		SoundQueue.ClearAllSounds()
		train.MoveToNext(self.startPos,'TurnAround')
	def Test(self,train):
		train.onFinish=self.EvalTest
		self.numTrials+=1
		#SoundQueue.PlaySound('SharedMedia/Sounds/NavigationQuiz.wav')
		train.StartHotSpotQuiz([self.startPos,self.endPos],mode='EfficiencyTest')
	def EvalTest(self,train):
		if (train.numSuccess >= train.numGoodTrials 
			and (train.numGoodTrials == 1 or train.VisitedHotSpots.all())):
			print "Achieved competency"
			train.log("### Achieved competency\n")
			dir=GetDirections(self.prefix, self.env, group=self.group)
			train.onFinish = next.Next
			next.setTrain(train)
			next.Next(train)
		# Director will have more inefficient routes than efficient, or has too many failures.
		elif (((self.numTrials + train.numGoodTrials) > (self.maxTrials + train.numSuccess))
				or (train.numFailures > 3)):
			print "Failed test"
			train.log("### Failed competency\n")
			self.setTrain(train) #reset
			(self.startPos,self.endPos)=self.QuizList.pop()
			train.onFinish=self.Prep
			viz.clearcolor(0,0,0)
			train.numSuccess = 0
			train.numOK = 0
			train.numFailures = 0
			train.MoveToNext(self.startPos,'BoundedWander')
		else:
			print "Continue test with trial ", self.numTrials, " and successes ", train.numSuccess
			self.Prep(train)

class GetDirections:
	def __init__(self,prefix="Default",env="",list=[],group=0):
		self.QuizList=list
		self.prefix=prefix+'_'+env+`group`
		self.runnum=0
		self.startPos=None
		self.endPos=None
	def setTrain(self,train):
		self.QuizList=Train.generatePairs()
		train.log("### Direction Series: "+str(self.QuizList))
		SoundQueue.ClearAllSounds()
		SoundQueue.PlaySound('SharedMedia/Sounds/GiveDirections.wav')
	def Next(self,train):
		print "Direction set ", self.runnum
		if self.runnum > 0:
			if self.dialog.filename:
				train.log("# Direction confidence giving "+self.dialog.filename)
			train.log(getEvaluation(1,1))
		if len(self.QuizList)==0:
			tkMessageBox.showinfo("Finished!","Finished with this part of the experiment.")
			viz.quit()
		else:
			(self.startPos,self.endPos)=self.QuizList.pop()
			train.MoveToNext(self.startPos)
			train.onFinish=self.Dialog
		self.runnum += 1
	def Dialog(self,train):
		filename='%s_%d_%d_Dirs'%(self.prefix,self.startPos,self.endPos)
		self.dialog=DirectionDialog(Tk(),startPos=self.startPos,endPos=self.endPos,filename=filename,state=NORMAL)
		train.StartHotSpotQuiz([self.startPos,self.endPos],self.dialog.filename)
		train.onFinish=self.Next

class GiveDirections:
	def __init__(self, directions=[], SubjNumber=0, directory='Directions/DirectionsNoNames'):
		self.directions=directions
		self.runnum=1
		self.filename=""
		self.env=None
		self.group = None
		self.SubjNumber = SubjNumber
		self.directory = directory
	def setTrain(self,train):
		#		self.train=train
		train.log('# Direction Follower number '+str(self.SubjNumber)+'\n')
		SoundQueue.ClearAllSounds()
		SoundQueue.PlaySound('SharedMedia/Sounds/NavigationQuiz.wav')
		return self.popDirection(train)
	def popDirection(self,train,number=0):
		self.filename=string.strip(self.directions.pop(number))
		print "Moving for ", self.filename
		(dirPrefix,env,self.startPos,self.endPos,id,number)=self.filename.split('_')
		group = env[-1]
		env = env[:len(env)-1]
		if (env,group) != (self.env,self.group):
			print "Resetting env",prefix,env,self.env,mode,numMoves
			if train: train.switchLayout(env, group)
			self.env = env
			self.group = group
		if train: train.MoveToNext(int(self.startPos),'Directions')
	def Next(self,train):
		print "Give Directions: ", self.runnum
		if self.dialog.filename:
			train.log("# Direction confidence following "+self.dialog.filename)
			train.log(getEvaluation(1,1))
		if len(self.directions)==0:
			tkMessageBox.showinfo("Finished!","Finished with this part of the experiment.")
			viz.quit()
		else:
			self.popDirection(train)
			train.onFinish=self.Dialog
		self.runnum += 1
	def Dialog(self,train):
		print "Presenting ", self.filename
		self.dialog = DirectionDialog(Tk(), filename=self.filename, state=DISABLED, dir=self.directory)
		train.StartHotSpotQuiz([int(self.startPos),int(self.endPos)], self.filename, mode='Directions' )
		train.onFinish = self.Next

class likert(tkSimpleDialog.Dialog):
	def __init__(self,parent,values,title,question):
		#print values,title,question
		self.values=values
		self.question=question
		self.rating = IntVar()
		self.rating.set(0)
		tkSimpleDialog.Dialog.__init__(self,parent,title)
	def body(self,parent):
		self.font=tkFont.Font(family="Times", size=15, weight=tkFont.BOLD)
		q=Label(parent,text=self.question,font=self.font).pack()
		for text, mode in self.values:
			#print text,mode
			self.b = Radiobutton(parent, text=text,variable=self.rating, value=mode,font=self.font)
			self.b.bind(mode, self.b.select)
			self.b.pack(anchor=W)
		self.b.pack()
		self.b.bind("<Double-Button-1>", self.ok)
		return self.b
	def validate(self):
		try:
			if (self.rating.get()==0):
				print self.rating.get()
				raise ValueError
			return 1
		except ValueError:
			tkMessageBox.showwarning(
			"Please pick a value",
			"No value chosen, please try again"
			)
			return 0
	def cancel(self, event=None):
		self.parent.destroy()
	def apply(self):
		return self.rating.get()
	def buttonbox(self):
		# overriden to remove cancel
		box = Frame(self)
		w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
		w.pack(side=LEFT, padx=5, pady=5)
		box.pack()

def getEvaluation(goodness,confidence):
	likertGood=[
		("1: Extremely poor, confusing, or blank",1),
		("2",2),
		("3",3),
		("4",4),
		("5",5),
		("6: Excellent",6)
	]
	likertConf=[
		("1: Certain not at destination",1),
		("2",2),
		("3",3),
		("4",4),
		("5",5),
		("6: Certain at destination",6)
	]
	feedback="#"
	if (goodness):
		l=likert(Tk(),likertGood,"Evaluating the directions","How good do you feel the directions were for getting to the destination \non a scale of 1 (not at all useful) to 6 (excellent)?")
		print l.rating.get()
		feedback=feedback+" Goodness: "+`l.rating.get()`
	if (confidence):
		l=likert(Tk(),likertConf,"Destination Confidence","How confident are you that you are at the destination \non a scale of 1 (certain NOT at destination) to 6 (certain at destination)?")
		print l.rating.get()
		feedback=feedback+" Confidence: "+ `l.rating.get()`
	return feedback+"\n"

def getFiles(name,dir='.'):
	files=os.listdir(dir)
	dirFiles=[]
	for file in files:
		#print file,string.find(file,name)
		if string.find(file,name)>=0:
			dirFiles.append(file)
			#print "Found matches for ",name,": ",file
	return dirFiles

if __name__ == '__main__':
	prefix="MTM"
	dirPrefix=""
	env="Demo"
	InitMsg=None
	prompt = True
	if prompt:
		print __doc__
		viz.go(viz.PROMPT|viz.FULLSCREEN)
		InitMsg = viz.get(viz.INITMESG)
		giveDirs = viz.get(viz.OPTION1)
		skipTraining = viz.get(viz.OPTION2)
		movie = viz.get(viz.TRACKER)
		if viz.get(viz.HMD): group = 1
		else: group = 0
	else:
		viz.go(viz.FULLSCREEN)
		InitMsg= "MTM Grid D 1 1"
		giveDirs = 0
		skipTraining = 0
		movie = 0
		movement = 0
		group = 0
	viz.mouse(viz.OFF)
	viz.cursor(viz.OFF)
	viz.fov(70,1)
	sys.argv=('-c')
	debug=0
	if InitMsg:
		print InitMsg,giveDirs,group
		params = InitMsg.split()
		prefix,env = params[:2]
		if env == 'All': giveDirs = True
		if len(params) > 2:
			if params[2] == 'D':
				movement = 'Discrete'
			elif params[2] == 'C':
				movement = 'Continuous'
			else: 
				print 'UNKNOWN MOVEMENT TYPE',params[2]
		else: movement = 'Discrete'
		if len(params) > 3:
			subjNumber = params[3]
		else: subjNumber = '1'
		if len(params) > 4:
			debug=1
			startNum=int(params[4])
		else: startNum=1
		if giveDirs:
			filename = 'DirectionFollower_'+subjNumber+'.run'
			FILE = open(os.path.join('RunFiles',filename),'r')
			directions=FILE.readlines()
			FILE.close()
			directions=directions[startNum-1:len(directions)]
			# directionDir = os.path.join('Directions','DirectionsNoNames')
			directionDir = os.path.join('Directions','CleanDirs')
			next = GiveDirections(directions, subjNumber, directionDir)
			onFinish = next.Dialog
			numMoves=0
			mode='Directions'
			env='All'
		elif not skipTraining:
			next = CompetencyTest(prefix,env,group=group)
			onFinish = next.Prep
			numMoves=120
			numGoodTrials=10
			directionDir=os.path.join('Directions','')
			mode='BoundedWander'
		else:
			next = GetDirections(prefix,env,group=group)
			onFinish = next.Next
			numMoves=1
			directionDir=os.path.join('Directions','')
			mode='BoundedWander'
		if debug or env == 'Demo':
			numMoves = 20 # 5 #
			numGoodTrials = 1
		train = Train.Train(prefix,env,exptName="Direction",init_mode=mode,onFinish=onFinish,
							group=group,numMoves=numMoves,directionDir=directionDir,movie=movie,
							movement=movement)
		viz.callback(viz.KEYBOARD_EVENT, train.mykey)
		next.setTrain(train)
	InitMsg=None
