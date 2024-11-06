import json
import glob
from tqdm import tqdm

from vector_database import LawBGEM3QdrantDatabase
from utils import dictionary_to_node

vector_database = LawBGEM3QdrantDatabase(
    url = "http://localhost:6333"
)
vector_database.clear()

list_data_file = glob.glob('/media/tavandai/DATA10/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data/*.json')

for data_file in tqdm(list_data_file):
    with open(data_file) as f1:
        data_content = json.load(f1)
    
    list_nodes = [dictionary_to_node(ele) for ele in data_content]

    vector_database.insert_nodes(list_nodes)
    
