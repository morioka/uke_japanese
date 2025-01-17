import argparse
import json
import sys

from japanese.embedding import encode_sentences, get_cadidate_embeddings
from japanese.tokenizer import extract_keyphrase_candidates
from japanese.ranker import DirectedCentralityRank

from transformers import AutoTokenizer
from transformers import AutoModel


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--input_file', type=str)
    parser.add_argument('--output_file', type=str)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.input_file is None:
        sys.exit('input_file is None')
    if args.output_file is None:
        sys.exit('output_file is None')

    # load model
    model = AutoModel.from_pretrained('cl-tohoku/bert-base-japanese')
    tokenizer = AutoTokenizer.from_pretrained('cl-tohoku/bert-base-japanese')

    # load input documents
    with open(args.input_file, 'r') as f:
        documents = json.load(f)

    phrases = {}

    for idx, texts in documents.items():
        text = '\n'.join(texts[:5]) + '\n' + '\n'.join(texts[-5:])
        tokens, keyphrases = extract_keyphrase_candidates(text, tokenizer)
        if len(tokens) == 0 or len(keyphrases) == 0:
            continue

        document_embs = encode_sentences([tokens], tokenizer, model)
        document_feats = get_cadidate_embeddings([keyphrases], document_embs, [tokens])
        ranker = DirectedCentralityRank(document_feats, beta=0.1, lambda1=1, lambda2=0.9, alpha=1.2, processors=8)
        phrases[idx] = ranker.extract_summary()
    

    with open(args.output_file, 'w') as f:
        json.dump(phrases, f, ensure_ascii=False)
        
