#!/bin/bash

INDEXDIR=${1}
DATAFILE=${2}
QUESTIONEMB=${3}
WIKITFIDF=${4}

for SPW in 0.1; do
    HDF5_USE_FILE_LOCKING=FALSE python run_index_pred_eval.py \
        $INDEXDIR \
        $DATAFILE \
        --sparse \
        --do_f1 \
        --ranker_path $WIKITFIDF \
        --step_size 1 \
        --sparse_weight $SPW \
        --nprobe 64 \
        --search_strategy "sparse_first" \
        --num_clusters 1024 \
        --start_top_k 1000 \
        --doc_sample_ratio 0.2 \
        --vec_sample_ratio 0.2 \
        --pred_dir "sparse_first_spw${SPW}" \
        --question_dump_path $QUESTIONEMB
done
