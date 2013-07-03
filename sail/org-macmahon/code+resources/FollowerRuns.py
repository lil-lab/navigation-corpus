import random, os, string, itertools

def getFiles(name,dir='.'):
	files=os.listdir(dir)
	dirFiles=[]
	for file in files:
		#print file,string.find(file,name)
		if string.find(file,name)>=0:
			dirFiles.append(file)
			#print "Found matches for ",name,": ",file
	return dirFiles

directionFiles=[]

# No director is repeated within 4 and each is in each line.
givers=['EDA', 'EMWC', 'KLS', 'KXP', 'TJS', 'WLH',
		'EMWC', 'KXP', 'WLH', 'EDA', 'KLS', 'TJS',
		'KXP', 'EDA', 'TJS', 'EMWC', 'WLH', 'KLS',
		'KLS', 'WLH', 'EMWC', 'TJS', 'EDA', 'KXP',
		'TJS', 'KLS', 'EDA', 'WLH',  'KXP', 'EMWC',
		'WLH', 'TJS', 'KXP', 'KLS', 'EMWC', 'EDA']
envs=['Grid', 'Jelly', 'L']
#random.shuffle(givers)

# Constructed to have eash place as start and end
# in each row, but not repeated within one set.
# No place is repeated within 3.
Pairs=[[2,1],[4,3],[6,5],[1,7],[3,2],[5,4],[7,6],
	   [1,5],[6,3],[4,1],[2,6],[7,4],[5,2],[3,7],
	   [2,4],[1,3],[7,2],[4,6],[3,5],[6,1],[5,7],
	   [6,4],[7,5],[3,1],[2,7],[4,2],[5,3],[1,6],
	   [4,7],[6,2],[1,4],[3,6],[5,1],[7,3],[2,5],
	   [7,1],[2,3],[4,5],[6,7],[1,2],[3,4],[5,6]]
group=0
n=0
numDirs=42*3*6*2
for Places in [Pairs,
               Pairs[36:42]+Pairs[6:12]+Pairs[18:24]+Pairs[30:36]+Pairs[0:6]+Pairs[12:18]+Pairs[24:30]]:
	while n < numDirs:
		for [F,T] in Places:
			#print n
			giver = givers[n%36]
			env=envs[(n%6)/2] #Switch envs every other route
			filePrefix='%(giver)s_%(env)s%(group)d_%(F)d_%(T)d'%vars()
			directions=getFiles(filePrefix,'Directions')
			#Use the most recent match
			#print filePrefix, directions
			directionFiles.append(directions.pop())
			#directionFiles.append(filePrefix)
			n+=1
			#Rotate environments to get Latin Square
			if (n%42 == 0 and not n%324 == 0):
				envs.insert(0,envs.pop())
			#Rotate the direction givers to not repeat giver/env/route combo
			#252 is the the period of 42 and 36
			if (n%252 ==0):
				temp = givers[0:12]
				givers[0:12]=[]
				givers.extend(temp)
				#print 324, givers

			if directionFiles.count(filePrefix) > 1: print n

#for file in directionFiles:
#	print file, directionFiles.count(file)

def outputArray(Array, filename):
	try:
		FILE = open(filename,'w')
		for item in Array:
			try:
				FILE.write('%s\n' % item)
			except:
				pass
		FILE.close()
	except:
		raise IOError,"Cannot open file for writing"

setSize=126
for i in range((numDirs/2)/setSize):
	filename = 'DirectionFollower_'+`i+1`+'.run'
	outputArray(directionFiles[setSize*i:setSize*(i+1)],os.path.join('RunFiles',filename))
directionFiles.reverse()
for i in range((numDirs/2)/setSize):
	filename = 'DirectionFollower_'+`i+7`+'.run'
	outputArray(directionFiles[setSize*i:setSize*(i+1)],os.path.join('RunFiles',filename))
for i in range((numDirs/2)/setSize):
	filename = 'DirectionFollower_'+`i+13`+'.run'
	outputArray(directionFiles[setSize*i:setSize*(i+1)],os.path.join('RunFiles',filename))
directionFiles.reverse()
for i in range((numDirs/2)/setSize):
	filename = 'DirectionFollower_'+`i+19`+'.run'
	outputArray(directionFiles[setSize*i:setSize*(i+1)],os.path.join('RunFiles',filename))

from SubjectLogs.SubjectGroups import *
import DirectionCorpus

#DiscreteDirectors = Directors1 + Directors2
#instRegexp = DirectionCorpus.constructItemRegexp(DiscreteDirectors, mapversions='[01]')

ContinuousDirectors = Directors3
instRegexp = DirectionCorpus.constructItemRegexp(ContinuousDirectors, mapversions='[01]')
Instructions = DirectionCorpus.DirectionCorpusReader(instRegexp).items('CleanDirs')

RISet = {}
Counts = {}
for ri in Instructions:
    ri_id = ri.split('-')[1]
    director,envnum,start,dest,seq,d = ri_id.split('_')
    env,num = envnum[:-1],envnum[-1]
    if env not in Maps: continue
    RISet.setdefault((env,start,dest), [])
    RISet[(env,start,dest)].append(ri_id)
    Counts[ri_id] = 0

for k,riset in RISet.items():
    for d in riset[:]:
        if '2.txt' in d:
            ri_other = d[:-5]+'1.txt'
            print k,d,ri_other
            if ri_other in riset:
                riset.remove(ri_other)

numDirs = 0
for k,riset in RISet.items():
    random.shuffle(riset)
    newDirs = [ri for ri in riset if ri.split('_')[0] in Directors3]
    newDirPool = newDirs * 2
    oldDirs = [ri for ri in riset if ri.split('_')[0] in Directors1]
    for oldri,newri in zip(oldDirs[:], newDirPool):
        index = oldDirs.index(oldri) + random.choice([0,1])
        #print index, newri
        oldDirs.insert(index, newri)
    if not oldDirs: oldDirs = newDirs
    numDirs += len(oldDirs)
    RISet[k] = itertools.cycle(oldDirs)

for ri,c in Counts.items():
    if '2_1' in ri: print ri, c

Envs = Maps*2
Envs.sort()
Envs = itertools.cycle(Envs)
RouteOrders = itertools.cycle([Pairs,
                               (Pairs[36:42]+Pairs[6:12]+Pairs[18:24]+Pairs[30:36]
                                +Pairs[0:6]+Pairs[12:18]+Pairs[24:30])])
for ri in Counts.keys(): Counts[ri] = 0
directionFiles = []
RouteOrder = []
for i in range(1,numDirs+1):
    if not RouteOrder: RouteOrder = RouteOrders.next()[:]
    start,dest = RouteOrder.pop()
    env = Envs.next()
    route = (env, str(start), str(dest))
    ri = RISet[route].next()
    print route, i, ri
    Counts[ri] += 1
    directionFiles.append(ri)
    if (i%42 == 0 and i%324 != 0):
        env = Envs.next()

hist = [(ri,c) for ri,c in Counts.items()]
hist.sort()
for ri,c in hist:
    print ri, c

#directionFiles = [i.split('-')[1] for i in Instructions]
#random.shuffle(directionFiles)
setSize=126
increment = len(directionFiles)/setSize
#count = 100
count = 204
for i in range(increment):
	filename = 'DirectionFollower_%d.run' % (count)
	outputArray(directionFiles[setSize*i:setSize*(i+1)],os.path.join('RunFiles',filename))
	count += 1
directionFiles.reverse()
for i in range(increment):
	filename = 'DirectionFollower_%d.run' % (count)
	outputArray(directionFiles[setSize*i:setSize*(i+1)],os.path.join('RunFiles',filename))
	count += 1
