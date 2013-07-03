import csv
from math import log
import Numeric
from Utility import entropy, conditional_entropy, normalize_to_prob, logistic_regression, pca    

def nullHash(x): return x
def truncate(x): return int(float(x))
def round_int(x): return int(round(float(x)))
def log_truncate(x):
    if x=='0' or x=='0.0' or x==0 or x==0.0: return '-inf'
    return int(log(float(x),2))
def log_round(x):
    if x=='0' or x=='0.0' or x==0 or x==0.0: return '-inf'
    return int(round(log(float(x),2)))
def qualitative(x):
    x=float(x)
    if x < 0.1: return 'Never'
    if x < 0.65: return 'Seldom'
    if x < 1.2: return 'Reliably'
    return 'Often'

def getConditionalDist(StatsDict,X,Stats,hashFns):
    X_given_stats = {'All' : X}
    for stat in Stats:
        X_given_stat = {}
        for statnames,set in X_given_stats.items():
            for key,val in set.items():
                statVal = StatsDict[stat][key]
                hashVal = (hashFns[stat](statVal),)
                if statnames != 'All': hashVal += statnames
                X_given_stat.setdefault(hashVal, {})[key]=val
        X_given_stats = X_given_stat
    total = 0
    print '\n',"['","',".join(Stats),"']",hashFns[stat].__name__
    for key,set in X_given_stats.items():
        X_given_stats[key] = set.values()
        print key, len(set),
        print entropy(normalize_to_prob(set.values()))
        total += len(set)
    entropy_given_stat = conditional_entropy(X_given_stats)
    print 'X |',"'[","',".join(Stats),"']",total,entropy_given_stat
    return X_given_stats,entropy_given_stat

if __name__ == "__main__":
    StatsCSVName = 'InstructionErrors_AllCorpora.csv'
    StatsCSV=open(StatsCSVName,'r')
    ColNames = StatsCSV.readline().split(',')
    ColNames[0] = 'StatName'
    StatsDict = {}
    for rowDict in csv.DictReader(StatsCSV,ColNames):
        name = rowDict['StatName']
        del rowDict['StatName']
        StatsDict[name] = rowDict
    StatsCSV.close()

    Entropies = []
    TgtFound = [float(StatsDict['TgtFound'][key])
                for key in ColNames if key.endswith('.txt') or key.endswith('.txt\n')]
    TgtFound = normalize_to_prob(TgtFound)
    Entropies.append((entropy(TgtFound),'TgtFound'))
    print 'TgtFound',entropy(TgtFound)
    TgtFoundDict = {}
    for key,val in zip(ColNames[2:],TgtFound):
        TgtFoundDict[key] = val

    StatHash = {
        'Director': nullHash,
        'Director Sex': nullHash,
        'Environment': nullHash,
        'NavConf': round_int,
        'DirRtng': round_int,
        'ReDirect': truncate,
        'FwdMove': log_truncate,
        'RTurns': log_truncate,
        'LTurns': log_truncate,
        'TimesFollowed': nullHash,
        'Words': log_truncate,
        'Sentences': log_truncate,
        'Misspell': nullHash,
        'Typo': nullHash,
        'Miss Word': nullHash,
        'Repeat Word': nullHash,
        'Incoherent': nullHash,
        'Ambig Ref': nullHash,
        'Object #': log_truncate,
        'Obj: Vague': nullHash,
        'Obj: Err': nullHash,
        'Obj: Place': nullHash,
        'Appear #': log_truncate,
        'Appear Err': nullHash,
        'Inter Type #': log_truncate,
        'Inter Type Err': nullHash,
        'Inter Paths #': log_truncate,
        'Inter Paths Err': nullHash,
        'Turn Dir #': log_truncate,
        'Turn Dir Err': nullHash,
        'Dist #': log_truncate,
        'Dist Err': nullHash,
        'Travel Term': log_truncate,
        'Turn Term': log_truncate,
        'Route Places': log_truncate,
        'Route Conn': nullHash,
        'Route Eff': nullHash,
        'Target Name Err': nullHash,
        'Target Pos Err': nullHash,
        'Initial Orientation': nullHash,
        'Dest Clear': nullHash,
        'Turn': log_truncate,
        'Travel': log_truncate,
        'Verify': log_truncate,
        'DeclareGoal': log_truncate,
        'Find': log_truncate,
        'FollowTrack': log_truncate,
        'Meta': log_truncate,
        }

    # Stats affected by the length of the route instruction set
    LengthStats = [
       'FwdMove',
       'RTurns',
       'LTurns',
       'ReDirect',
       'Words',
       'Sentences',
       'Object #',
       'Appear #',
       'Turn Dir #',
       'Dist #',
       'Travel Term',
       'Turn Term',
       'Turn',
       'Travel',
       'Verify',
       ]
    
    TotalErrors = {}
    for stat in StatHash:
        if stat.endswith('Err'):
            for route in ColNames[2:]:
                TotalErrors[route] = TotalErrors.setdefault(route,0) + float(StatsDict[stat][route])
    StatsDict['Total Errors'] = TotalErrors
    StatHash['Total Errors'] = nullHash
    
    for stat in LengthStats:
        d = {}
        for route in ColNames[2:]:
            d[route] = float(StatsDict[stat][route])
            places = float(StatsDict['Route Places'][route])
            if places>1: d[route] /= places-1
        StatsDict[stat+" Norm"] = d
        StatHash[stat+" Norm"] = log_round

    for stat in StatHash:
        dist,ent = getConditionalDist(StatsDict,TgtFoundDict,
                                      [stat],StatHash)
        Entropies.append((ent,stat))

        for comp_stat in ['Director','Appear # Norm','Turn Dir # Norm', 'Dist # Norm', 'Words']:
            dist,ent = getConditionalDist(StatsDict,TgtFoundDict,
                                          [stat,comp_stat],StatHash)
            Entropies.append((ent,stat,comp_stat))

    dist,ent = getConditionalDist(StatsDict,TgtFoundDict,
                                  ['Appear # Norm','Turn Dir # Norm', 'Dist # Norm'],StatHash)
    Entropies.append((ent,'Appear # Norm','Turn Dir # Norm', 'Dist # Norm'))

    Entropies.sort()
    print
    for e in Entropies: print e

    Norm = []
    for stat in StatHash:
        if stat.endswith('Norm'):
            Norm.append([StatsDict[stat][route] for route in ColNames[2:]])
    TgtFoundA = Numeric.array(TgtFound)
    NormA = Numeric.array(Norm)
    logistic_regression.logistic_regression(NormA,TgtFoundA)
    Norm.append(TgtFound)
    pca.pca(Numeric.array(Norm))
