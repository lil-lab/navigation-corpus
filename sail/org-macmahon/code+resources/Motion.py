import os, os.path, sets, re, pylab
from Utility import lstail, entropy, histogram, frequency_entropy, mode, percent
from Harness import Directors, Maps, Positions
from LogAnalyzer import Followers
import stats
from POMDP.MarkovLoc_Grid import pomdp as Grid_pomdp
from POMDP.MarkovLoc_Jelly import pomdp as Jelly_pomdp
from POMDP.MarkovLoc_L import pomdp as L_pomdp
POMDPs = {'Grid':Grid_pomdp, 'Jelly':Jelly_pomdp, 'L':L_pomdp}

MinDistances = {}
for envname in POMDPs.keys():
    for posset in '0','1':
        mapname = envname+posset
        for line in file('Maps/Direction'+mapname+'.eff'):
            if line.startswith('#'): continue
            p1,p2,d = line.split()
            MinDistances[envname,p1,p2] = float(d)
            MinDistances[envname,p2,p1] = float(d)

def getMotions(directory,route=None,filename=None):
    if route: filename = 'MotTrace-'+route
    return [eval(pose) for pose in file(os.path.join(directory,filename))]

def getFloat(directory,valuename,route=None,filename=None):
    if route: filename = '%s-%s' % (valuename,route)
    try:
        valuefile = file(os.path.join(directory,filename))
        value = float(valuefile.readline())
        valuefile.close()
    except IOError: value = None
    return value

def getPlaces(poses):
    """Return a hash of places visited, given a list of poses."""
    places = sets.Set()
    for pose in poses:
        places.add(pose[0:2])
    return places

def findRoute(Directory,Director,Map,Start,Target,Num='.'):
    regexp = re.compile('MotTrace-%s_%s[01]_%s_%s_Dirs_%s\.txt' % (Director,Map,Start,Target,Num))
    return lstail(Directory, regexp)

class Route(object):
    def __init__(self,Directory,Director,Map,Start,Target,Num='1',Key=None,Poses=[]):
        self.directory = Directory
        self.director = Director
        self.map = Map
        self.start = Start
        self.target = Target
        self.num = Num
        if Key:
            if '-' in Key: self.key = Key.split('-')[1]
            else: self.key = Key
        else:
            self.key = '%(Director)s_%(Map)s[01]_%(Start)s_%(Target)s_Dirs_%(Num)s.txt' % locals()
        if Poses: self.poses = Poses
        else: self.poses = getMotions(Directory, self.key)
        if self.poses:
            if len(self.poses[0]) == 2: # (Place,Gateway) coords
                self.poses = [POMDPs[self.map].state2plat(pose) for pose in self.poses]
            self.start_place = self.poses[0][:2]
            self.term_place = self.poses[-1][:2]
        else:
            self.start_place = POMDPs[self.map].position2plat(self.start)
            self.term_place = self.start_place
        self.target_place = POMDPs[self.map].position2plat(self.target)
        self.places = getPlaces(self.poses)
        self.rating = getFloat(Directory,'DirRtng',self.key)
        self.navconf = getFloat(Directory,'NavConf',self.key)
        try:
            self.efficiency = MinDistances[Map,self.start,self.target] / len(self.places)
        except ZeroDivisionError: self.efficiency = 0.0
        self.effaccuracy = getFloat(Directory,'Efficiency',self.key)
        if self.effaccuracy is None:
            if not self.termAtTarget(): self.effaccuracy = 0
            else: self.effaccuracy = self.efficiency
    
    def __str__(self): return 'Route(%s,%s,%s,%s, Poses=%s)' % (self.directory,self.map,self.start,self.target,self.poses)
    
    def termAtStart(self):
        return self.term_place == self.start_place
    
    def termAtTarget(self):
        return self.term_place == self.target_place
    
    def sharedPlaces(self,other): return self.places.union(other.places)

def createRoute(Directory,Director,Map,Start,Target,Num='1',Routes={}):
    Directory = os.path.join('SubjectLogs',Directory)
    routeFiles = findRoute(Directory,Director,Map,Start,Target,Num)
    if not routeFiles: return
    if len(routeFiles)>1:
        print 'ERROR: More than one route trace found for ', (Directory,Director,Map,Start,Target,Num)
    route = Route(Directory,Director,Map,Start,Target,Num,routeFiles[0])
    print Directory.split('_')[0].split('/')[1],
    Routes[(Directory,routeFiles[0])] = route
    return route

def manhattan_dist(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])
def percentage(x): return 100.0*float(x)

def AtTarget(Routes): return [percentage(r.termAtTarget()) for r in Routes]
def AtStart(Routes): return [percentage(r.termAtStart()) for r in Routes]
def Oth_Plc(Routes): return [percentage(not r.termAtStart() and not r.termAtTarget()) for r in Routes]
def AtModePl(Routes): return [percentage(r.term_place == r.mode_term_place) for r in Routes]
def AtOtMdPl(Routes): return [percentage(r.term_place == r.mode_term_place
                                         and not r.termAtStart() and not r.termAtTarget()) for r in Routes]
def NavConf(Routes): return [r.navconf for r in Routes if r.navconf]
def DirRtng(Routes): return [r.rating for r in Routes if r.rating]
def NumPlace(Routes): return [len(r.places) for r in Routes]
def NumPose(Routes): return [len(r.poses) for r in Routes]
def ManDist(Routes): return [manhattan_dist(r.term_place,r.target_place) for r in Routes]
def Effic(Routes): return [r.efficiency for r in Routes if r.efficiency]
def EffAcc(Routes): return [r.effaccuracy for r in Routes]

def analyzeRoutes(placeStats,RatingBounds,*RouteGroups):
    print '\tGroup\t\t', ('\t'*4).join([RouteGroup[0] for RouteGroup in RouteGroups])
    print 'Fun Name\t', 'Entropy\t Mean\t StdDev| '*len(RouteGroups)
    RouteGroupList = [RouteGroup[1].values() for RouteGroup in RouteGroups]
    
    for fn in (AtTarget,AtStart,Oth_Plc,AtModePl,AtOtMdPl,NavConf,DirRtng,NumPlace,NumPose,ManDist,Effic,EffAcc):
        print fn.__name__,'\t',
        for Routes in RouteGroupList:
            if RatingBounds: Routes = [route for route in Routes
                                       if route.mean_rating > RatingBounds[0]
                                       and route.mean_rating <= RatingBounds[1]]
            seq = fn(Routes)
            if len(seq)>1:
                avg = pylab.mean(seq)
                stddev = pylab.std(seq)
            else:
                if len(seq): avg = seq[0]
                else: avg = 0.0
                stddev = 0.0
            print '%6.2f\t%6.2f\t%6.2f | ' %(frequency_entropy(seq), avg, stddev),
        print
    if not placeStats: return
    print 'Common Places:\t',
    for Routes in RouteGroupList:
        max_places = max([len(route.places) for route in Routes]+[1])
        if not Routes: continue
        commonPlaces = Routes[0].places
        for route in Routes[1:]:
            commonPlaces = commonPlaces.intersection(route.places)
        print '%d of %d\t%6.2f | ' % (len(commonPlaces),max_places, len(commonPlaces)/float(max_places)),
    print
    print 'Termination Place Entropy:\t',
    for Routes in RouteGroupList:
        print ' %6.2f |\t' % (frequency_entropy([route.term_place for route in Routes])),
    print
    if RouteGroupList and RouteGroupList[0] and RouteGroupList[0][0]:
        print 'Most common termination place (Target %s):\t' %str(RouteGroupList[0].target_place),
    else: print 'No routes found',
    for Routes in RouteGroupList:
        print ' %s |\t' % (str(mode([route.mode_term_place for route in Routes],3))),
    print

def iterateRoutes():
    for Director in Directors:
        for Map in Maps:
            for Start in Positions:
                for Target in Positions:
                    if Start == Target: continue
                    yield (Director,Map,Start,Target,'.')

def generateRoutesFile(routeList='MarcoLogs/Matches'):
    for routename in file(routeList):
        (Director,Map,Start,Target,Dirs,Suffix) = routename.split('_')
        Mapname = Map[:-1] # chop off map ID
        Num = Suffix.split('.')[0]
        if Mapname not in Maps: continue
        yield (Director,Mapname,Start,Target,Num)

if __name__=="__main__":
    followerRoutes = {}
    directorRoutes = {}
    marcoRoutes = {}
    perRoute = False # True
    Director = Directors[0]
    Map = Maps[0]
    Start = Positions[0]
    Target = Positions[1]
    Counts = {(True,True):0, (True,False):0, (False,True):0, (False,False):0,}
    Discrepancy = {}
    RouteGroups = (('Followers',followerRoutes),('Director',directorRoutes),('Marco',marcoRoutes))
    routeGenerator = generateRoutesFile
    
    for (Director,Map,Start,Target,Num) in routeGenerator():
        key = '%s_%s[01]_%s_%s_Dirs_%s.txt' % (Director,Map,Start,Target,Num)
        print key,
        Routes = []
        for Follower in Followers:
            for Directory in lstail('SubjectLogs', re.compile(Follower+'_DirectionAll0_\d$')):
                Routes.append(createRoute(Directory,Director,Map,Start,Target,Num,followerRoutes))
        Routes = [route for route in Routes if route]
        if Routes:
            mode_term_place = mode([route.term_place for route in Routes],3)
            try:
                mean_rating = pylab.mean(DirRtng(Routes))
                mean_navconf = pylab.mean(NavConf(Routes))
            except ZeroDivisionError:
                mean_rating = mean_navconf = 0.0
        for Directory in lstail('SubjectLogs', re.compile('%s_Direction%s[01]_\d$'%(Director,Map))):
            Routes.append(createRoute(Directory,Director,Map,Start,Target,Num,directorRoutes))
        for Directory in lstail('SubjectLogs', re.compile('Marco_DirectionAll0_\d$')):
            Routes.append(createRoute(Directory,Director,Map,Start,Target,Num,marcoRoutes))
        Routes = [route for route in Routes if route]
        print
        
        for route in Routes:
            route.mode_term_place = mode_term_place
            route.mean_rating = mean_rating
            route.mean_navconf = mean_navconf
        
        if perRoute:
            analyzeRoutes(True,(),*RouteGroups)
            print
            for mRoute in marcoRoutes.values():
                for hRoute in followerRoutes.values():
                    if (not hRoute.poses or not mRoute.poses 
                        or mRoute.poses[0] != hRoute.poses[0]):
                        continue
                    Counts[(mRoute.termAtTarget(), hRoute.termAtTarget())] += 1
            if followerRoutes and marcoRoutes:
                Discrepancy[key] = (pylab.mean(AtTarget(marcoRoutes.values()))
                                    - pylab.mean(AtTarget(followerRoutes.values())))
            followerRoutes.clear()
            directorRoutes.clear()
            marcoRoutes.clear()
    
    if not perRoute:
        analyzeRoutes(False,(),*RouteGroups)
        print
        analyzeRoutes(False,(1.0,6),*RouteGroups)
    else:
        print '\t'*5,'Human'
        print '\t'.join(['Marco\t','Success','Failure','Total','Percent'])
        mResults = hResults = (True,False)
        for mResult in mResults:
            if mResult: print '\tSuccess\t',
            else: print '\tFailure\t',
            for hResult in hResults:
                print '%4d\t' % (Counts[(mResult,hResult)]),
            total = sum([Counts[(mResult,hResult)] for hResult in hResults])
            print total,'\t',
            print '%4.1f%%' % (percent(Counts[(mResult,True)], total))
        print '\tTotals\t',
        for hResult in hResults:
            print sum([Counts[(mResult,hResult)] for mResult in mResults]),'\t',
        total = sum(Counts.values())
        print total,'\t',
        print '%4.1f%%' % (percent(sum([Counts[(mResult,True)] for mResult in mResults]), total))
        print '\tPercent\t',
        for hResult in (True,False):
            print '%4.1f%%\t' % (percent(Counts[(True,hResult)], sum([Counts[(mResult,hResult)] for mResult in mResults]))),
        print '%4.1f%%' % (percent(sum([Counts[(True,hResult)] for hResult in hResults]), total))
        precision = percent(Counts[(True,True)], sum([Counts[(True,hResult)] for hResult in hResults]))
        recall = percent(Counts[(True,True)], sum([Counts[(mResult,True)] for mResult in mResults]))
        f_measure = 2*precision*recall/(precision+recall)
        print '\t'.join(['Precision:','%4.1f%%'%precision, 'Recall:','%4.1f%%'%recall, 'F-Measure:','%4.1f%%'%f_measure])

        RouteDisc = [(disc,route) for route,disc in Discrepancy.items()]
        RouteDisc.sort()
        for disc,route in RouteDisc: print '%7.2f%%\t%s' % (disc,route)

        for (Director,Map,Start,Target,Num) in generateRoutesFile('MarcoLogs/Matches-All'):
            route = '%s_%s[01]_%s_%s_Dirs_%s.txt' % (Director,Map,Start,Target,Num)
            #print route,',',
            if route in Discrepancy: print '%7.2f' % Discrepancy[route],
            print
