#!/bin/bash

PWD=`pwd`
INFILE="${PWD}/${1}"
OUTDIR="${PWD}/${2}/"

DBFILE="/usr0/home/bdhingra/tmp.db"
rm -rf $DBFILE
cd DrQA/scripts/retriever

python build_db.py $INFILE $DBFILE
python build_tfidf.py $DBFILE $OUTDIR --data_file $INFILE
