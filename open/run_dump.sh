#!/bin/bash

DUMP_DIR=${1}
OUT_DIR=${2}
WIKITFIDF=${3}

mkdir -p $OUT_DIR

HDF5_USE_FILE_LOCKING=FALSE python dump_tfidf.py \
    $DUMP_DIR \
    $OUT_DIR \
    --ranker_path $WIKITFIDF
