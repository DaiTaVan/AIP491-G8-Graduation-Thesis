import os
import json
import math
from embedding import BGEEmbedding
import multiprocessing
multiprocessing.freeze_support()

embedding_model = BGEEmbedding(
        model_name='/datadriver/dai/temp/AIP491-G8-Graduation-Thesis/bge-m3'
    )

with open('/datadriver/dai/temp/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/all_contents_mapping.json') as f1:
    content = json.load(f1)

if not os.path.exists('/datadriver/dai/temp/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/list_ids.json'):
    list_ids = list(content.keys())
    with open('/datadriver/dai/temp/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/list_ids.json', 'w') as f1:
        json.dump(list_ids, f1, indent=2)
else:
    with open('/datadriver/dai/temp/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/list_ids.json') as f1:
        list_ids = json.load(f1)

batch = 50000
num_batch = math.ceil(len(list_ids) / batch)

for i in range(num_batch):
    result = {}
    batch_ids = list_ids[i * batch: (i+1) * batch]
    batch_contexts = [content[ele] for ele in batch_ids]

    list_embedding = embedding_model.embed(batch_contexts)

    for content_id, embedding in zip(batch_ids, list_embedding):
        result[content_id] = embedding
    
    with open(f"/datadriver/dai/temp/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/output/{i}.json", 'w') as f1:
        json.dump(result, f1)
    

