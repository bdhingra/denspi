"""Script to read TFIDF counts matrix and reorder them according to titles."""

import argparse
import json
import numpy as np
import scipy.sparse as sp

from drqa import retriever


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('tfidf_file', type=str, default=None,
                        help='File holding Tfidf counts.')
    parser.add_argument('data_file', type=str, default=None,
                        help='File with original documents in order.')
    parser.add_argument('out_file', type=str, default=None,
                        help='File to store reordered counts to.')
    args = parser.parse_args()

    # Counts matrix and metadata
    doc_mat, metadata = retriever.utils.load_sparse_csr(args.tfidf_file)
    id2doc = metadata["doc_dict"][1]
    
    # Original ids and titles
    title2id = {}
    with open(args.data_file) as f:
        for ii, line in enumerate(f):
            item = json.loads(line.strip())
            title2id[item["id"]] = ii

    # Create new sparse matrix.
    doc_mat = doc_mat.tocoo()
    new_cols = np.zeros_like(doc_mat.col)
    for ii in range(new_cols.shape[0]):
        new_cols[ii] = title2id[id2doc[doc_mat.col[ii]]]
    new_mat = sp.csr_matrix((doc_mat.data, (new_rows, doc_mat.col)), shape=doc_mat.shape)
    print("new shape:", new_mat.shape)

    # Get metadata for permuted counts.
    metadata["doc_dict"][0] = title2id
    metadata["doc_dict"][1] = sorted(title2id.keys(), key=lambda x: title2id[x])

    # Save
    retriever.utils.save_sparse_csr(args.out_file, new_mat, metadata)
