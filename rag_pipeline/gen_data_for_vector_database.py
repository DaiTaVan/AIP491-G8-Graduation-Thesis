import json
from tqdm import tqdm
from uuid import uuid4

from embedding import BGEEmbedding
from parser import SentenceSplitter
from vector_database import Node
from utils import node_to_dictionary

embedding_model = BGEEmbedding(
        model_name='/media/tavandai/DATA10/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/bge-m3'
    )

parser = SentenceSplitter(tokenizer = embedding_model.tokenizer(), chunk_size=128)

with open('/media/tavandai/DATA10/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/Phapdien/dieu_phap_dien.json') as f1:
    all_dieu = json.load(f1)


for ix, value in all_dieu.items():
    print(ix)
    list_nodes = []
    for ele in tqdm(value):
        dieu_id = ele['id']
        vbpl_goc_id = ele['itemId']
        vbpl_goc_location = ele['locationInVbpl']
        demucId = ele['demucId']
        chuongId = ele['chuongId']
        mucId = ele['mucID']

        dieu_index = ele['sourceTitle'][1:-1]
        dieu_title = ' '.join(ele['title'].split()[2:])
        dieu_title = f"{dieu_index}: {dieu_title}"
        dieu_content = ele['content']

        list_sub_texts = parser.split(title = dieu_title, content = dieu_content)
        list_embedding = embedding_model.embed(list_sub_texts)
        for sub_text, embedding  in zip(list_sub_texts, list_embedding):
            new_node = Node(
                id = str(uuid4()),
                dense_vector = embedding['dense'],
                sparse_vector = embedding['sparse'],
                metadata = {
                    'content': sub_text,
                    'dieu_id': dieu_id,
                    'vbpl_goc_id': vbpl_goc_id,
                    'vbpl_goc_location': vbpl_goc_location,
                    'demucId': demucId,
                    'chuongId': chuongId,
                    'mucId': mucId
                }
            )
            list_nodes.append(node_to_dictionary(new_node))
        with open(f'/media/tavandai/DATA10/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data/{ix}.json', 'w') as f1:
            json.dump(list_nodes, f1, indent=4, ensure_ascii=False)

        

        