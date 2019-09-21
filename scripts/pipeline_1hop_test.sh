#!/bin/bash -e

BASE_DIR="downloads/1hop_test"
IN_QRY="dev_qrys.json"
IN_DOC="paragraphs-00001-of-00010_10K.json"
MODELDIR="downloads/model/"
TEMPLATES="downloads/relation_templates.json"
MINPARALEN="50"
SPW="0.1"
FILT="0.2"
NUM_TMPL="5"
#MAX_QUES="200"
STRATEGY="sparse_first"
OUT_DIR="output/dump_1hop_test_template_minlen${MINPARALEN}_filt${FILT}"

# Intermediate files
QRY_FILE="squad_template_$IN_QRY"
DOC_FILE="squad_minlen${MINLEN}_$IN_DOC"
python scripts/convert_paragraphs_to_squad.py $BASE_DIR/$IN_DOC $BASE_DIR/$DOC_FILE $MINPARALEN
python scripts/create_templates_1hop.py $BASE_DIR/$IN_QRY $BASE_DIR/$QRY_FILE --template_file $TEMPLATES --num_templates $NUM_TMPL # --max_ques $MAX_QUES

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
    --predict_batch_size 32 \
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

echo "Evaluating"
cd ../
PREDFILE="$(ls ${OUT_DIR}/${PREDDIR}/*.json | tail -1)"
python scripts/aggregate_multiple_answers.py ${BASE_DIR}/dev_qrys.json $PREDFILE $OUT_DIR/$PREDDIR/final_answers.json
