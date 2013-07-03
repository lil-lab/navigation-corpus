#!/bin/bash
cat corpus1-instructions.xgoal.noimplicit.segmented.train.wlh.txt corpus1-instructions.xgoal.partial.segmented.train.wlh.txt > corpus1-instructions.xgoal.noimplicit-partial.segmented.train.wlh.txt
python ../../../../pysrc/labeled_to_positionsinglesentence.py -u corpus1-instructions.xgoal.noimplicit-partial.segmented.train.wlh.txt > corpus1-instructions.xgoal.noimplicit.segmented.train.wlh.ccg
python ~/dev/research/tiny.git/navi/pysrc/positionsinglesentence_preprocess.py corpus1-instructions.xgoal.noimplicit.segmented.train.wlh.ccg
python position_split_to_folds.py
mv *.ccg ~/dev/research/tiny.git/navi/experiments/noimplicit.segmented.oracle.dev.wlh.cross
rm corpus1-instructions.xgoal.noimplicit-partial.segmented.train.wlh.txt
cd ~/dev/research/tiny.git/navi/experiments/noimplicit.segmented.oracle.dev.wlh.cross
mkdir giza
cd giza
python ~/dev/research/tiny.git/tiny/pysrc/create_gize_job.py -o nl2lf -g ~/dev/research/tiny.git/tiny/giza/giza-pp/GIZA++-v2 -s NL -p ~/dev/research/tiny.git/tiny/pysrc/giza_postprocess.py ../corpus1-instructions.xgoal.noimplicit.segmented.train.wlh.ccg 
./nl2lf.giza.sh
mv nl2lf.giza.cooc ..
cd ..
rm -rf giza
