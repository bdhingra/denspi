#!/bin/bash

DATADIR=${1}
PREDICTFILE=${2}
OUTPUT=${3}
MODELDIR="downloads/model/"

HDF5_USE_FILE_LOCKING=FALSE python run_piqa.py \
    --do_index \
    --data_dir $DATADIR \
    --predict_file $PREDICTFILE \
    --metadata_dir downloads/bert/ \
    --output_dir $OUTPUT \
    --load_dir $MODELDIR \
    --iteration 1 \
    --filter_threshold 0.2 \
    --predict_batch_size 16 \
    --parallel
