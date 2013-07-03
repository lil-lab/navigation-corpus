from Parser import parseLine, parseFile, debug
import re, string,os,sys

TopoMap = {}
TopoPatterns={}

class lineParser:
    def __init__(self,PropName,ComponentPatts,Key,DB,Patterns,ExtrasFn=None,PropContent=None):
        self.PropName = PropName
        self.ComponentPatts = ComponentPatts
        self.Key = Key
        self.linePatt = makeLinePatt(PropName,PropContent)
        if not PropContent: PropContent = PropName
        self.itemPatt = makeItemPatt(PropContent,ComponentPatts)
        self.ExtrasFn = ExtrasFn
        self.DB = DB
        self.DB[PropName] = {}
        Patterns[self.linePatt] = self.parseLine
    def parseLine(self,results):
        if __debug__: print __name__,self.PropName,results[self.PropName+'Line']
        for item in results[self.PropName+'Line'].split(';'):
            m = self.itemPatt.match(item)
            if m:
                d = m.groupdict()
                if self.ExtrasFn: self.ExtrasFn(results,self.DB,d)
                tripDictAdd(self.DB,self.PropName+'-evidence',tuple([d[k] for k in self.Key]),d['evidence'])
        del results[self.PropName+'Line']
        del results['evidence']

class topoLineParser(lineParser):
    ps = {}  #property strings
    bs = '.'
    ps['evidence']='\s*'+bs+'ev\{(?P<evidence>[0-9,\*]+)\}\{'
    ps['place']=bs+'sshplace\{(?P<place>[^\}]+)\}'
    ps['place2']=re.sub('>','2>',ps['place'])
    ps['path']=bs+'sshpath\{(?P<path>[^\}]+)\}'
    ps['pathdir']=bs+'sshpathdir(?P<pathdir>\{(?P<path>[^\}])\}\{(?P<dir>(\+|\-))\})'
    ps['pathdir2']=re.sub('>','2>',ps['pathdir'])
    ps['appear']='(?P<appear>[^\)\{]+)'
    ps['object']='(?P<object>[^\)\{]+)'
    ps['thing']='(?P<thing>'+ps['object']+'|'+ps['place']+')'
    ps['thing2']=re.sub('>','2>',ps['thing'])
    ps['localTopology']='(?P<localTopology>[^\)]+)'
    ps['pathType']='(?P<pathType>[^\)]+)'
    ps['distCount']='(?P<distCount>[^\), ]+)'
    ps['distUnit']='(?P<distUnit>[^\), ]+)'
    ps['islot']=bs+'islot\{(?P<islot>[-\w]+)\}\{(?P<islotVal>[^, ]+)\}'
    ps['instruction']='('+bs+'instruct\{(?P<instruction>[-\w]+)\}\{(?P<islots>.*)\}'+')'
    def __init__(self,PropName,Key,ExtrasFn=None,PropContent=None):
        global TopoMap, TopoPatterns
        ComponentPatts = [self.ps[k] for k in Key]
        lineParser.__init__(self,PropName,ComponentPatts,Key,DB=TopoMap,Patterns=TopoPatterns,ExtrasFn=ExtrasFn,PropContent=PropContent)

Sp='[\s~\\;\\!]*'
cSp=','+Sp
def makeLinePatt(Name,Patt=None):
    if not Patt: Patt = Name
    return re.compile('(?P<'+Name+'Line>'+topoLineParser.ps['evidence']+Patt+'\(.*)')
def makeItemPatt(Name,Components): return re.compile(topoLineParser.ps['evidence']+Name+'\('+cSp.join(Components)+'\)\}')

def tripDictAdd(outer,inner,key,value):
    if not outer.has_key(inner): outer[inner] = {}
    outer[inner][key] = value

def placeLineExtras(results,DB,d):
    DB['place'][d['place']]=1
placeParser = topoLineParser('place',['place'],placeLineExtras)

def pathLineExtras(results,DB,d):
    DB['path'][d['path']]=1
pathParser = topoLineParser('path',['path'],pathLineExtras)

TopoMap['placesOn'] = {}
TopoMap['objectsOn'] = {}
TopoMap['pathsAt'] = {}
def onLineExtras(results,DB,d):
    if d['place']:
        tripDictAdd(DB['pathsAt'],d['place'],d['path'],d['evidence'])
        tripDictAdd(DB['placesOn'],d['path'],d['place'],d['evidence'])
    elif d['object']:
        tripDictAdd(DB['objectsOn'],d['path'],d['object'],d['evidence'])
    else: print 'ERROR: unmatched entity in', __name__, d
onParser = topoLineParser('on',['path','thing'],onLineExtras)

def orderLineExtras(results,DB,d):
    if d['place'] and d['place2']:
        thing1 = d['place']; thing2 = d['place2']
    elif d['object'] and d['place2']:
        thing1 = d['object']; thing2 = d['place2']
    elif d['place'] and d['object2']:
        thing1 = d['place']; thing2 = d['object2']
    elif d['object'] and d['object2']:
        thing1 = d['place']; thing2 = d['object2']
    else: print 'ERROR: unmatched entity in', __name__ , d; thing1 = thing2 = None
    tripDictAdd(DB['order'],d['path']+d['dir'],(thing1,thing2),d['evidence'])
orderParser = topoLineParser('order',['pathdir','thing','thing2'],orderLineExtras)

TopoMap['localTopology'] = {}
def sideOfLineExtras(results,DB,d):
    tripDictAdd(DB['localTopology'],d['place'],(d['path']+d['dir'],d['path2']+d['dir2']),d['sideOf'])
    if d['sideOf']=='Right': otherSide = 'Left'
    elif d['sideOf']=='Left': otherSide = 'Right'
    else:
        print 'ERROR:',__name__,'Unknown totheSideOf Side:', d['sideOf']
        raise EOFError
        otherSide = 'Unknown'
    tripDictAdd(DB['localTopology'],d['place'],(d['path2']+d['dir2'],d['path']+d['dir']),otherSide)
sideOfParser = topoLineParser('sideOf',['place','pathdir','pathdir2'],sideOfLineExtras,'tothe(?P<sideOf>(Right|Left))Of')

def appearLineExtras(results,DB,d):
    tripDictAdd(DB['appear'],d['path']+d['dir'],d['place'],d['appear'])
appearParser = topoLineParser('appear',['pathdir','place','appear'],appearLineExtras)

def pathTypeLineExtras(results,DB,d):
    tripDictAdd(DB['pathType'],d['path']+d['dir'],d['place'],d['pathType'])
pathTypeParser = topoLineParser('pathType',['pathdir','place','pathType'],pathTypeLineExtras)

def distanceLineExtras(results,DB,d):
    tripDictAdd(DB['pathDistance'],d['path'],(d['place'],d['place2']),d['distCount'])
distanceParser = topoLineParser('pathDistance',['path','place','place2','distCount','distUnit'],distanceLineExtras)

def terminatesLineExtras(results,DB,d):
    DB['terminates'][d['path']+d['dir']]=d['place']
terminatesParser = topoLineParser('terminates',['pathdir','place'],terminatesLineExtras)

def atLineExtras(results,DB,d):
    DB['at'][d['place']]=d['object']
atParser = topoLineParser('at',['place','object'],atLineExtras)

def localTopologyLineExtras(results,DB,d):
    tripDictAdd(DB['localTopology'],d['place'],'shape',d['localTopology'])
localTopologyParser = topoLineParser('localTopology',['place','localTopology'],localTopologyLineExtras)

TopoMap['routeInstructions'] = []
def instructionLineExtras(results,DB,d):
    RI = {'Action': d['instruction']}
    islotPatt = re.compile(topoLineParser.ps['islot'])
    for islot in d['islots'].split(', '):
        m = islotPatt.match(islot)
        if m:
            d = m.groupdict()
            RI[d['islot']]=d['islotVal']
    DB['routeInstructions'].append(RI)
instructionParser = topoLineParser('instruction',['instruction'],instructionLineExtras)
instructionParser.linePatt=re.compile(topoLineParser.bs+'item'+instructionParser.linePatt.pattern)
TopoPatterns[instructionParser.linePatt] = instructionParser.parseLine

def dontCareLine(results): pass
TopoPatterns[re.compile('^.topolist.*$')] = dontCareLine
TopoPatterns[re.compile('^.raggedright$')] = dontCareLine
TopoPatterns[re.compile('^\s*.(begin|end)\{enumerate\}\s*$')] = dontCareLine
TopoPatterns[re.compile('^(\}\{?|\s*)(%.*)?$')] = dontCareLine               #End of one block
TopoPatterns[re.compile('^\s*..\s*$')] = dontCareLine                        #Newline
TopoPatterns[re.compile('^\s*$')] = dontCareLine                             #Blank line
TopoPatterns[re.compile('^.emph\{.*$')] = dontCareLine                       #Comment

def printEvidence(TopoMap):
    print '='*8,file,'Evidence','='*8
    for k,v in TopoMap.items():
        if k.endswith('-evidence'): print k,v

def printMap(TopoMap):
    print '='*8,file,'Propositional Map','='*8
    for k,v in TopoMap.items():
        if v and not k.endswith('-evidence'): print k,v

class partialOrder:
    def __init__(self,partialOrder): self.partialOrder = partialOrder
    def cmp(self,x,y):
        if (x,y) in self.partialOrder: return -1
        elif (y,x) in self.partialOrder: return 1
        else: return 0 # Arbitrary 

def getTotalOrder(TopoMap,path):
    totalOrder = [k for k in TopoMap['placesOn'][path]]
    porder = partialOrder(TopoMap['order'][path+'+'])
    totalOrder.sort(porder.cmp)
    return totalOrder

dirs = 'drul'
def graphPlace(TopoMap,name,drawn,currentLoc,dist=2,pathdir=0,mapFile=sys.stdout,context=''):
    #print __name__,(name,drawn,currentLoc,dist,pathdir)
    mapFile.write(writePlace(name,drawn,currentLoc,dist,pathdir,context))
    if TopoMap['at'].has_key(name):
        obj = TopoMap['at'][name]
        dir = 'rd' #[,'ru','ld','lu']
        mapFile.write('"Pl'+name+'" [] !{"Pl'+name+'"!/'+dir+' 24pt/} *++={\\txt{'+obj+'}}\n')
    paths = TopoMap['pathsAt'][name].keys()
    paths.sort()
    #print __name__,' : paths =>',paths
    lastpath = None
    lastplace=name
    side = None
    for path in paths:
        if lastpath and TopoMap['localTopology'].has_key(place):
            side = TopoMap['localTopology'][place].get((path+'+',lastpath+'+'),None)
            if not side:
                side = TopoMap['localTopology'][place].get((lastpath+'+',path+'+'),None)
        if lastpath and not side: pathdir -= 1# Arbitary left
        if side == 'Left': pathdir -= 1
        if side == 'Right': pathdir += 1
        pathdir %= 4
        for place in getTotalOrder(TopoMap,path):
            #print place,
            if not drawn.has_key('Pl'+place):
                if TopoMap['pathDistance'].has_key(path):
                    dist = int(TopoMap['pathDistance'][path].get((lastplace,place),2))
                else: dist = None
                graphPlace(TopoMap,place,drawn,currentLoc,dist,pathdir,mapFile,lastplace)
        if not drawn.has_key('Pa'+path):
            writePath(TopoMap,path,pathdir,drawn,getTotalOrder(TopoMap,path),mapFile)
            if not side: print 'Arbitrary.  Draw fuzzy turn'  
        # output path description
        #print
        lastpath = path

def writePlace(name,drawn,currentLoc,dist=1,pathDir=0,context=''):
    #print __name__,(name,drawn,currentLoc,dist,pathDir)
    if not dist: dist = 3 # Arbitrary placement leaves room for visible gap.
    if pathDir: drawn['Pl'+name] = (currentLoc[0],currentLoc[1]+dist)
    else: drawn['Pl'+name] = (currentLoc[0]+dist,currentLoc[1])
    if dist == 0: disp = ''
    if context: context = '"Pl'+context+'" '
    return context+'['+dirs[pathDir]*dist+']'+' '*(10-dist)+'*{\\sshplace{'+name+'}}*++[o]{}*+\\frm{o} ="Pl'+name+'"\n'

def writePath(TopoMap,path,pathdir,drawn,placesOrder,mapFile):
    # output ghost ends if not terminates
    if not TopoMap['terminates'].has_key(path+'-'):
        mapFile.write('"Pl'+placesOrder[0]+'" ['+dirs[(pathdir+2)%4]+'] *{} ="Pa'+path+'-"\n')
        mapFile.write('"Pa'+path+'-":@{/--+} "Pl'+placesOrder[0]+'"\n')
    if not TopoMap['terminates'].has_key(path+'+'):
        mapFile.write('"Pl'+placesOrder[-1]+'" ['+dirs[pathdir]+'] *{} ="Pa'+path+'+"\n')
        mapFile.write('"Pl'+placesOrder[-1]+'":@{/--+} "Pa'+path+'+"\n')
    #Sanity check ends
    mapFile.write('"Pl'+placesOrder[0]+'":@^{/:+} ')
    for place in placesOrder[1:-1]: mapFile.write('\'"Pl'+place+'" ')
    mapFile.write('"Pl'+placesOrder[-1]+'" ')
    mapFile.write('^{\\sshpath{'+path+'}}\n')
    #{ A \ar @{/:|} [r] & {} \ar @{|==|} [r] & {} \ar @{|:+} [r] & B }
    for place1,place2 in zip(placesOrder[:-1],placesOrder[1:]):
        mapFile.write('"Pl'+place1+'" :@^{} "Pl'+place2+'" ')
        if TopoMap['pathDistance'].has_key(path):
            dist = int(TopoMap['pathDistance'][path].get((place1,place2),None))
        else: dist = None
        if dist: mapFile.write(' ^(.33){-'+str(dist)+'-}\n')
        else: mapFile.write(' ^(.33){-?-}\n')
    annotePath = ''
    if TopoMap['objectsOn'].has_key(path):
        mapFile.write('"Pl'+placesOrder[0]+'" :@^{} "Pl'+placesOrder[-1]+'" ')
        objects = TopoMap['objectsOn'][path].keys()
        for place in placesOrder:
            if TopoMap['at'].has_key(place): objects.remove(TopoMap['at'][place])
        mapFile.write('^(0.75){\\textsf{\\txt{'+',\\\\ '.join(objects)+'}}}\n')
    if TopoMap['appear'].has_key(path+'+'):
        place1 = TopoMap['appear'][path+'+'].keys()[0]
        place2 = placesOrder[placesOrder.index(place1)+1]
        annotePath += TopoMap['appear'][path+'+'][place1]+' '
    if TopoMap['pathType'].has_key(path+'+'):
        place1 = TopoMap['pathType'][path+'+'].keys()[0]
        place2 = placesOrder[placesOrder.index(place1)+1]
        annotePath += TopoMap['pathType'][path+'+'][place1]+' '
    if TopoMap['on'].has_key(path):
        place1 = TopoMap['pathType'][path+'+'].keys()[0]
        place2 = placesOrder[placesOrder.index(place1)+1]
        annotePath += TopoMap['pathType'][path+'+'][place1]+' '
    if annotePath:
        annotePath = re.split('[, ]+',annotePath[:-1])
        mapFile.write('"Pl'+place1+'" :@^{} "Pl'+place2+'" _{\\texttt{\\txt{'+',\\\\'.join(annotePath)+'}}}\n')
    drawn['Pa'+path] = 1

def getRouteSequence(riList):
    routePlaces = []
    placePatt = re.compile(topoLineParser.ps['place'])
    for ri in riList:
        if ri['Action'] == 'turn':
            place = ri['at']
        elif ri['Action'] == 'travel' or ri['Action'] == 'find':
            place = ri['from']
            #place = ri['to']
        elif ri['Action'] == 'declare-goal': pass
        routePlaces.append('"Pl'+placePatt.match(place).groupdict()['place']+'" ')
        if ri['Action'] == 'travel' or ri['Action'] == 'find': place = ri['to']
        routePlaces.append('"Pl'+placePatt.match(place).groupdict()['place']+'" ')
    uniqPlaces = [routePlaces[0]]
    for i in range(len(routePlaces)-1):
        if routePlaces[i] != routePlaces[i+1]:
            uniqPlaces.append(routePlaces[i+1])
    return uniqPlaces

def printGraphicalMap(TopoMap,Giver):
    print '='*8,file,'Graphical Map','='*8
    drawn = {}
    mapFile = open(os.path.join('Directions','CorrFullTrees',
                                'TopoMap_'+Giver+'_Grid0_4_5_Dirs_1.txt.tex')
                   ,'w')
    mapFile.write('\\[\\xy \\xygraph{\n')
    graphPlace(TopoMap,'1',drawn,(0,0),dist=0,pathdir=0,mapFile=mapFile)
    routePlaces = getRouteSequence(TopoMap['routeInstructions'])
    for place in TopoMap['place']:
        drawnPlaces = [k for k in drawn if k.startswith('Pl')]
        drawnPlaces.sort()
        if 'Pl'+place not in drawnPlaces: #Arbitrary 3 dist, Arbitrary direction
            graphPlace(TopoMap,place,drawn,(3,3),3,0,mapFile,drawnPlaces[-1][2:])
    mapFile.write(routePlaces[0]+' :@{(~)} ')
    for rp in routePlaces[1:-1]:
        mapFile.write('\''+rp)
    mapFile.write(routePlaces[-1])#+' _{route}\n')
    mapFile.write('} \\endxy \\]\n')
    mapFile.close()

if __name__ == '__main__':
    results = {}
    for Giver in ['EDA','EMWC','KLS','KXP','TJS','WLH']:
        file = 'Topo_'+Giver+'_Grid0_4_5_Dirs_1.txt.tex'
        print '\n',file
        # initialize TopoMap fn
        for k in TopoMap.keys():
            TopoMap[k] = {}
            TopoMap['routeInstructions'] = []
        parseFile(TopoPatterns, os.path.join('Directions','CorrFullTrees',file), results)
        if debug: printEvidence(TopoMap)
        printMap(TopoMap)
        printGraphicalMap(TopoMap,Giver)
