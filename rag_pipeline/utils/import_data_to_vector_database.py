import json
import glob
from tqdm import tqdm
from rag_pipeline.src.vector_database import LawBGEM3QdrantDatabase, Node
from rag_pipeline.src.utils import dictionary_to_node

vector_database = LawBGEM3QdrantDatabase(
    url = "http://localhost:6333",
    api_key=None
)
# vector_database = LawBGEM3QdrantDatabase(
#     url = "https://8c074658-8279-4154-a433-4a2f08dcc302.us-east4-0.gcp.cloud.qdrant.io:6333",
#     api_key= "pTXoTpbYs3eyxgonOLWbWVwQNBFMOL5k85wcGAaiO0-P1Y3RnqfwjQ"
# )
vector_database.clear()

# all_embedding_dict = {}
# list_data_file = glob.glob('/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/output/*.json')
# for data_file in list_data_file:
#     with open(data_file) as f1:
#         all_embedding_dict.update(json.load(f1))

current_file_output = 0
with open(f'/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/output/{current_file_output}.json') as f1:
    all_embedding_dict = json.load(f1)


with open('/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/list_ids.json') as f1:
    list_ids = json.load(f1)

with open('/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/Phapdien/dieu_phap_dien_fix.json') as f1:
    all_dieu = json.load(f1)

with open('/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/all_contents_mapping.json') as f1:
    all_contents_mapping = json.load(f1)

with open('/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/all_contents.json') as f1:
    all_contents = json.load(f1)

for ix, value in all_dieu.items():
    print(ix)

    for ele in tqdm(value):
        dieu_id = ele['id']
        vbpl_goc_id = ele['itemId']
        vbpl_goc_location = ele['locationInVbpl']
        demucId = ele['demucId']
        chuongId = ele['chuongId']
        mucId = ele['mucID']

        list_nodes = []
        for sub_id in all_contents[dieu_id]:
            location_file_output = list_ids.index(sub_id) // 50000
            # print('location_file_output', location_file_output)
            if location_file_output != current_file_output:
                with open(f'/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/output/{location_file_output}.json') as f1:
                    all_embedding_dict = json.load(f1)

            sub_text = all_contents_mapping[sub_id]
            dense_vector = all_embedding_dict[sub_id]['dense']
            sparse_vector = all_embedding_dict[sub_id]['sparse']
            new_node = Node(
                id = sub_id,
                dense_vector = dense_vector,
                sparse_vector = sparse_vector,
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
            list_nodes.append(new_node)
            current_file_output = location_file_output
        
        vector_database.insert_nodes(list_nodes)