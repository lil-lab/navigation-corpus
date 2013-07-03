#!/bin/bash
cd ~/dev/research/tiny.git/navigation/navi/data/instructions/train.eda
python ../../../../pysrc/labeled_to_tracesinglesentence.py -u corpus1-instructions.xgoal.noimplicit.segmented.train.eda.txt > corpus1-instructions.xgoal.noimplicit.segmented.train.eda.ccg
python ~/dev/research/tiny.git/navi/pysrc/tracesinglesentence_preprocess.py corpus1-instructions.xgoal.noimplicit.segmented.train.eda.ccg
python trace_split_to_folds.py
mv *.ccg ~/dev/research/tiny.git/navi/experiments/3speaker.oracle.exec.dev.segmented.cross

cd ~/dev/research/tiny.git/navigation/navi/data/instructions/train.emwc
python ../../../../pysrc/labeled_to_tracesinglesentence.py -u corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.txt > corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.ccg
python ~/dev/research/tiny.git/navi/pysrc/tracesinglesentence_preprocess.py corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.ccg
python trace_split_to_folds.py
mv *.ccg ~/dev/research/tiny.git/navi/experiments/3speaker.oracle.exec.dev.segmented.cross

cd ~/dev/research/tiny.git/navigation/navi/data/instructions/train.wlh
cat corpus1-instructions.xgoal.noimplicit.segmented.train.wlh.txt corpus1-instructions.xgoal.partial.segmented.train.wlh.txt > corpus1-instructions.xgoal.noimplicit-partial.segmented.train.wlh.txt
python ../../../../pysrc/labeled_to_tracesinglesentence.py -u corpus1-instructions.xgoal.noimplicit-partial.segmented.train.wlh.txt > corpus1-instructions.xgoal.noimplicit.segmented.train.wlh.ccg
python ~/dev/research/tiny.git/navi/pysrc/tracesinglesentence_preprocess.py corpus1-instructions.xgoal.noimplicit.segmented.train.wlh.ccg
python trace_split_to_folds.py
mv *.ccg ~/dev/research/tiny.git/navi/experiments/3speaker.oracle.exec.dev.segmented.cross
rm corpus1-instructions.xgoal.noimplicit-partial.segmented.train.wlh.txt

cd ~/dev/research/tiny.git/navi/experiments/3speaker.oracle.exec.dev.segmented.cross

cat corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.ccg corpus1-instructions.xgoal.noimplicit.segmented.train.eda.ccg corpus1-instructions.xgoal.noimplicit.segmented.train.wlh.ccg > corpus1-instructions.xgoal.noimplicit.segmented.train.all.ccg

mkdir giza
cd giza
python ~/dev/research/tiny.git/tiny/pysrc/create_gize_job.py -o nl2lf -g ~/dev/research/tiny.git/tiny/giza/giza-pp/GIZA++-v2 -s NL -p ~/dev/research/tiny.git/tiny/pysrc/giza_postprocess.py ../corpus1-instructions.xgoal.noimplicit.segmented.train.all.ccg 
./nl2lf.giza.sh
mv nl2lf.giza.cooc ..
cd ..
rm -rf giza
