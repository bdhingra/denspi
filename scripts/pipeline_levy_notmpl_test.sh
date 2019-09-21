#!/bin/bash -e

BASE_DIR="downloads/levy_test"
QRY_FILE="test.json"
IN_DOC="corpus.txt"
MODELDIR="downloads/model/"
TEMPLATES="downloads/relation_templates.json"
SPW="0.1"
FILT="0.2"
STRATEGY="sparse_first"
OUT_DIR="output/dump_levy_test_filt${FILT}"

# Intermediate files
DOC_FILE="squad_$IN_DOC.json"
python scripts/corpus_to_squad.py $BASE_DIR/$IN_DOC $BASE_DIR/$DOC_FILE

export HDF5_USE_FILE_LOCKING=FALSE

echo "Converting to DrQA format"
python scripts/to_drqa.py $BASE_DIR/$DOC_FILE $BASE_DIR/drqa_$DOC_FILE
echo "Creating TFIDF index"
./scripts/create_drqa_tfidf.sh $BASE_DIR/drqa_$DOC_FILE $BASE_DIR

echo "Indexing phrases"
python run_piqa.py \
    --do_index \
    --data_dir $BASE_DIR \
    --predict_file $DOC_FILE \
    --metadata_dir "downloads/bert/" \
    --output_dir $OUT_DIR \
    --load_dir $MODELDIR \
    --iteration 1 \
    --filter_threshold $FILT \
    --predict_batch_size 64 \
    --max_seq_length 192 \
    --parallel

echo "Indexing questions"
./scripts/run_embed_questions.sh $BASE_DIR $QRY_FILE $OUT_DIR

PWD=`pwd`
TFIDF="$PWD/$(ls ${BASE_DIR}/*.npz | tail -1)"
OUT_DIR="$PWD/$OUT_DIR"
QRY_FILE="$PWD/$BASE_DIR/$QRY_FILE"
echo "reading drqa index from $TFIDF"
cd open/
echo "Dumping tfidf vectors"
./run_dump.sh "$OUT_DIR" "$OUT_DIR/tfidf/" $TFIDF

echo "Running predictions"
PREDDIR="${STRATEGY}_spw${SPW}"
python run_index_pred_eval.py \
    $OUT_DIR \
    $QRY_FILE \
    --sparse \
    --do_f1 \
    --ranker_path $TFIDF \
    --step_size 1 \
    --sparse_weight $SPW \
    --nprobe 64 \
    --search_strategy $STRATEGY \
    --num_clusters 1024 \
    --start_top_k 1000 \
    --mid_top_k 50 \
    --doc_sample_ratio 0.2 \
    --vec_sample_ratio 0.2 \
    --pred_dir "${PREDDIR}" \
    --question_dump_path "$OUT_DIR/question.hdf5"

cd ../
PREDFILE="$(ls ${OUT_DIR}/${PREDDIR}/*.json | tail -1)"
python scripts/piqa_to_simple.py $PREDFILE ${OUT_DIR}/${PREDDIR}/final_answers.json
