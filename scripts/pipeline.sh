#!/bin/bash -e

BASE_DIR="downloads/slot-filling-1hop-template"
QRY_FILE="squad_template_dev_qrys.json"
DOC_FILE="squad_paragraphs-00000-of-00010_10Kdev.json"
OUT_DIR="output/dump_sf1hop_template"

export HDF5_USE_FILE_LOCKING=FALSE

echo "Converting to DrQA format"
python scripts/to_drqa.py $BASE_DIR/$DOC_FILE $BASE_DIR/drqa_$DOC_FILE
echo "Creating TFIDF index"
./scripts/create_drqa_tfidf.sh $BASE_DIR/drqa_$DOC_FILE $BASE_DIR

echo "Indexing phrases"
./scripts/run_indexing.sh $BASE_DIR $DOC_FILE $OUT_DIR

echo "Indexing questions"
./scripts/run_indexing.sh $BASE_DIR $QRY_FILE $OUT_DIR

cd open/
echo "Dumping tfidf vectors"
TFIDF=$(ls ${BASE_DIR}/*.npz | tail -1)
./run_dump.sh $OUT_DIR $OUT_DIR/tfidf/ $TFIDF

echo "Running predictions"
./run_predictions.sh $OUT_DIR $QRY_FILE $OUT_DIR/question.hdf5 $TFIDF
