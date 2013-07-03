#!/usr/bin/env python
import sys

Maps = ['Grid','Jelly','L','All']
Positions = [str(i+1) for i in range(7)]
Routes = []
Groups = [0,1]

__author__ = 'Laura Massey'
__doc__ ="""Generate shortest route given an environment map.

Usage: ShortestPath.py [options]

Options:
    -h / --help
        Print this message and exit.

    -v / --verbose
        Be more verbose.

    -e mapname/ --env=mapname
        Run on the environment with given mapname.
        mapname must be one of %(Maps)s (default 1st).

    -g / --group=number
        Use named position group, from %(Groups)s, default 0.
""" % globals()

# Others, for later.
"""
    -r / --route
        Calculate this route, of form ENV_START_DEST.

    -s / --start
        Specify start position.
        Must be one of %(Positions)s.

     -t / --target
        Specify target position.
        Must be one of %(Positions)s.
""" % globals()

class ShortestPath(object):
    def __init__(self, pomdp, currentState=None, group=0):
        self.pomdp = pomdp
        if group == 1: self.positions = pomdp.Positions1
        else: self.positions = pomdp.Positions
        #current state is (Gateway, direction) format
        self.currentState = currentState
        #create graph associated with the pomdp
        self.g = {}
        for num in range(self.pomdp.NumPlaces):
            self.g[num]=[]

        for (num, dir) in self.pomdp.Gateways:
            (node, nextdir) = self.pomdp.Gateways[(num, dir)]
            self.g[num].append((node,dir))

        self.graph = [self.Vertex(num,self.g[num]) for num in self.g]
                
    class Vertex(object):
        #A vertex in a graph, using adjacency list.
        # 'edges' is a sequence or collection of tuples (edges), the first element of
        #  which is a name of a vertex and the second element is the distance to that vertex.
        #  'name' is a unique identifier for each vertex, like a city name, an integer, a tuple of coordinates..."""

        # I took this code from some cookbook online.
        def __init__(self, name, edges):
            self.name = name
            self.edges = edges
 
    def Dijkstra(self, graph, source, dest):
        """Returns the shortest distance from vertex source to vertex dest.
        
        Uses Dijkstra's algorithm, so assumes the graph is connected."""
        infinity = sys.maxint - 1
        distances = {}
        names = {}
        P = {}
        for v in graph:
            distances[v.name] = infinity # Initialize the distances
            names[v.name] = v # Map the names to the vertices they represent
        distances[source.name] = 0 # The distance of the source to itself is 0
        dist_to_unknown = distances.copy() # Select the next vertex to explore from this dict
        last = source
        while last.name != dest.name:
            # Select the next vertex to explore, which is not yet fully explored and which 
            # minimizes the already-known distances.
            next = names[ min( [(v, k) for (k, v) in dist_to_unknown.iteritems()] )[1] ]
            for n, d in next.edges: # n is the name of an adjacent vertex, d is the distance to it
                if(distances[next.name] + 1 < distances[n]):
                    P[n] = (next.name,d)
                    distances[n] = distances[next.name] + 1 #assume all distances between each pair of nodes are 1
                    #distances[n] = min(distances[n], distances[next.name] + d)
                if n in dist_to_unknown:
                    dist_to_unknown[n] = distances[n]
            
            last = next
            if last.name in dist_to_unknown: # Delete the completely explored vertex
                del dist_to_unknown[next.name]
    
        return (P,distances)

    #Start and Dest are positions (1-7) in the pomdp
    def ReturnPath(self, Start, Dest):
        #make sure the start and end destinations are integers to be passed into the Positions dictionary
        if isinstance(Start, str):
            Start = int(Start)
        if isinstance(Dest,str):
            Dest = int(Dest)
        #obtain the gateways corresponding to the Start & End positions
        Start = self.positions[Start]
        Dest = self.positions[Dest]
        
        #use current state when defined (used when recalculating a route) 
        if self.currentState:
            (Start,temp) = self.currentState
        numlist = range(self.pomdp.NumPoses)
        
        source = self.Vertex(Start, self.g[Start])
        dest = self.Vertex(Dest, self.g[Dest])

        #use Dijkstra's algorithm
        (P,D) = self.Dijkstra(self.graph,source,dest)
        distance = D[Dest]

        #extract the path from source to dest
        Path = []
        dir = -1
        while 1:
            if Dest == Start: break
            Path.append((Dest, dir))
            (Dest,dir) = P[Dest]
        
        Path.reverse()
        
        (secondnode,x) = Path[0]

        #add in the initial direction, from start node to second node
        initDir = 0
        for i in numlist:
            if (Start,i) in self.pomdp.Gateways:
                (next,dir) = self.pomdp.Gateways[(Start,i)]
            
                if next == secondnode:
                    initDir = dir
        
        Path = [(Start,initDir)]+Path        
        return (distance,Path)
    
    def outputPathLengthFile(self, name):
        """Output the shortest path lengths between each Position pairing to at filename name in Matt's format."""
        output = open(name,'w')
        lengths = {}
        positions = self.positions.keys()
        positions.sort()
        # the following commented out code is an optimization, it looks through the distances vector returned
        # from the dijkstra's call and pulls out useful distances so that we won't have to call dijkstra's
        # specifically for that start, destination pair. (this dijkstra's finds the distances to most destination
        # nodes, but not all). the optimization will only work with a large map.
        """
        for i in positions:
            i = int(i)
            lengths[(i,i)] = 0
        destinations=[]

        for Start in positions:
            start = Start
            if isinstance(start, str):
                start = int(Start)
            #obtain the gateways corresponding to the Start & End positions
            StartGate = self.positions[start]
            DestGate = self.positions[7]                            

            source = self.Vertex(StartGate, g[StartGate])
            dest = self.Vertex(DestGate, g[DestGate])

            #use Dijkstra's algorithm       
            (P,D) = self.Dijkstra(graph,source,dest)

            for ic,d in self.positions:
                startcopy = start
                if ic < start:
                    temp = start
                    start = ic
                    ic = temp

                if D[d] != sys.maxint - 1:
                    lengths[(start,ic)] = D[d]
                    #print start,ic,D[d]

                start = startcopy"""
        output.write('# ___'+'___'.join([str(pos) for pos in positions])+'\n')
        buffer = ""
        for i,igate in self.positions.items():
            # i represents the start location
            output.write("#%d|" % i)
            for j,jgate in self.positions.items():
                #j represents the destination location
                if i > j:
                    if (i,j) in lengths: #if statment only useful when above code is uncommented, but will still work as is
                        distance = lengths[(i,j)]
                    else:
                        source = self.Vertex(igate, self.g[igate])
                        dest = self.Vertex(jgate, self.g[jgate])

                        #use Dijkstra's algorithm       
                        (P,D) = self.Dijkstra(self.graph,source,dest)
                        distance = D[jgate]
                        lengths[(i,j)] = lengths[(j,i)] = distance
                        output.write('%3d' % distance)
                #elif i <= j: output.write("   ")
                if j == len(positions):
                    output.write("\n")
        output.write("#\n")
        for i in positions:
            for j in positions[i:]:
                output.write('%d %d %d\n' %(i,j,lengths[(i,j)]))
        output.close()

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

if __name__ == "__main__":
    import getopt
    verbose = False
    Map = 'All' # Maps[0]
    Group = 1
    try:
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'vhe:g:',
                                       ['verbose', 'help',
                                        'env=', 'group',
                                        ])
        except getopt.error, msg:
             raise Usage(msg)
        for opt, arg in opts:
            if opt in ('-v', '--verbose'):
                verbose = True
            elif opt in ('-h', '--help'):
                print >>sys.stderr, __doc__
                sys.exit(0)
            elif opt in ('-e', '--env'):
                Map = arg
                if Map not in Maps:
                    raise Usage("map name '%s' not in map list: %s" %(Map,Maps))
            elif opt in ('-g', '--group'):
                Group = int(arg)
                if Group not in Groups:
                    raise Usage("group id '%s' not in group list: %s" %(Group,Groups))
            
            if opt in sys.argv: sys.argv.remove(opt)
            if arg in sys.argv: sys.argv.remove(arg)
            if opt+'='+arg in sys.argv: sys.argv.remove(opt+'='+arg)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        sys.exit(2)

    POMDPs = {}
    if Map in ('All', 'Grid'):
        from POMDP.MarkovLoc_Grid import pomdp as Grid_map
        POMDPs['Grid'] = Grid_map
    if Map in ('All', 'Jelly'):
        from POMDP.MarkovLoc_Jelly import pomdp as Jelly_map
        POMDPs['Jelly'] = Jelly_map
    if Map in ('All', 'L'):
        from POMDP.MarkovLoc_L import pomdp as L_map
        POMDPs['L'] = L_map

    for map,pomdp in POMDPs.items():
        if verbose: print 'Producing efficiency file for environment %s, Position Group %d.'%(map,Group)
        ShortestPath(pomdp, group=Group).outputPathLengthFile('Maps/Direction%s%d.eff'%(map,Group))
            
