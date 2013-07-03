#!/bin/bash
python ../../../../pysrc/labeled_to_singlesentence.py corpus1-instructions.xgoal.noimplicit.segmented.train.sample20.txt > ~/dev/research/tiny.git/navi/experiments/sample20.segmented/corpus1-instructions.xgoal.noimplicit.segmented.train.sample20.ccg

python ~/dev/research/tiny.git/tiny/pysrc/singlesentence_preprocess.py ~/dev/research/tiny.git/navi/experiments/sample20.segmented/corpus1-instructions.xgoal.noimplicit.segmented.train.sample20.ccg

for i in corpus1-instructions.xgoal.noimplicit.segmented.train.sample20-*.txt; do
	python ../../../../pysrc/labeled_to_singlesentence.py $i > ~/dev/research/tiny.git/navi/experiments/sample20.segmented.cross/$i.ccg
	python ~/dev/research/tiny.git/tiny/pysrc/singlesentence_preprocess.py ~/dev/research/tiny.git/navi/experiments/sample20.segmented.cross/$i.ccg
done


