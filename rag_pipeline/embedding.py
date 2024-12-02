from typing import List
from FlagEmbedding import BGEM3FlagModel
import torch


class BGEEmbedding:
    def __init__(
            self,
            model_name: str,
            max_length: int = 8192,
            use_fp16: bool = True,
            device: str = None
    ):
        self.model_name = model_name
        self.max_length = max_length
        self.use_fp16 = use_fp16
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
    
        self.model = BGEM3FlagModel(
            model_name_or_path=self.model_name,  
            use_fp16=self.use_fp16,
            devices=self.device,
            query_max_length=self.max_length,
            passage_max_length=self.max_length
        ) # Setting use_fp16 to True speeds up computation with a slight performance degradation
    
    def tokenizer(self):
        return self.model.tokenizer

    def embed(
            self,
            sentences: List[str],
            use_dense: bool = True,
            use_sparse: bool = True,
            use_colbert_vecs=False
    ):
        outputs = self.model.encode(sentences, return_dense=use_dense,return_sparse=use_sparse, return_colbert_vecs=use_colbert_vecs)

        fn_outputs = []
        for i in range(len(sentences)):
            fn_outputs.append({
                'dense': outputs['dense_vecs'][i].tolist(),
                'sparse': {k: float(v) for k, v in outputs['lexical_weights'][i].items()}
            })
        
        return fn_outputs


if __name__ == '__main__':
    bge_embedding = BGEEmbedding(
        model_name='/media/tavandai/DATA10/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/bge-m3'
    )
    sentences_1 = ["What is BGE M3?", "Defination of BM25", 
                "BGE M3 is an embedding model supporting dense retrieval, lexical matching and multi-vector interaction.", 
                "BM25 is a bag-of-words retrieval function that ranks a set of documents based on the query terms appearing in each document"]


    output = bge_embedding.embed(sentences=sentences_1)
    print(output)
