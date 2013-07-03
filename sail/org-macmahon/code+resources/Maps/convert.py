import os
from Utility import lstail
dir = './'
for poi in lstail(dir,re.compile('.*.poi$')):
    poiFile = file(dir+poi)
    newFile = file(dir+poi+'_PLAT','w')
    for line in poiFile:
        x,y,snd1,snd2 = line.split('|')
        print x,y,snd1,snd2
        x=int(x)/40
        y=int(y)/40
        print x,y,snd1,snd2
        newFile.write('|'.join([str(x),str(y),snd1,snd2]))
    poiFile.close()
    newFile.close()
    os.rename(dir+poi,dir+poi+'.bak')
    os.rename(dir+poi+'_PLAT',dir+poi)
