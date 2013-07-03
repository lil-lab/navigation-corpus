#!/bin/bash
python ../../../../pysrc/labeled_to_singlesentence.py corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-train.txt > ~/dev/research/tiny.git/navi/experiments/sample10.segmented/corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-train.ccg 
python ../../../../pysrc/labeled_to_singlesentence.py corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-eval.txt > ~/dev/research/tiny.git/navi/experiments/sample10.segmented/corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-eval.ccg 

python ~/dev/research/tiny.git/tiny/pysrc/singlesentence_preprocess.py ~/dev/research/tiny.git/navi/experiments/sample10.segmented/corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-train.ccg 
python ~/dev/research/tiny.git/tiny/pysrc/singlesentence_preprocess.py ~/dev/research/tiny.git/navi/experiments/sample10.segmented/corpus1-instructions.xgoal.noimplicit.segmented.train.sample10-eval.ccg 


