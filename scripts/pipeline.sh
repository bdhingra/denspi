#!/bin/bash -e

BASE_DIR="downloads/slot-filling-2hop-template"
QRY_FILE="gold_1st_hop_templates.json"
DOC_FILE="squad_twohop-longparagraphs-00000-of-00010_120K.json"
#OUT_DIR="output/dump_sf2hop_1st_hop_para50_template"
OUT_DIR="output/dump_sf2hop_1st_hop_para50_template_filt0.2"

export HDF5_USE_FILE_LOCKING=FALSE

echo "Converting to DrQA format"
python scripts/to_drqa.py $BASE_DIR/$DOC_FILE $BASE_DIR/drqa_$DOC_FILE
echo "Creating TFIDF index"
./scripts/create_drqa_tfidf.sh $BASE_DIR/drqa_$DOC_FILE $BASE_DIR

echo "Indexing phrases"
./scripts/run_indexing.sh $BASE_DIR $DOC_FILE $OUT_DIR

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
./run_predictions.sh "$OUT_DIR" "$QRY_FILE" "$OUT_DIR/question.hdf5" $TFIDF
