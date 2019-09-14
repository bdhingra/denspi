#!/bin/bash

INDEXDIR=${1}
DATAFILE=${2}
QUESTIONEMB=${3}
WIKITFIDF=${4}

HDF5_USE_FILE_LOCKING=FALSE python run_index_pred_eval.py \
    $INDEXDIR \
    $DATAFILE \
    --sparse \
    --do_f1 \
    --ranker_path $WIKITFIDF \
    --step_size 1 \
    --sparse_weight 0.05 \
    --nprobe 64 \
    --search_strategy "sparse_first" \
    --question_dump_path $QUESTIONEMB
