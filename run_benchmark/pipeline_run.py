import os
import glob
import json
from tqdm import tqdm
from rag_pipeline.src.pipeline import Pipeline

pipeline = Pipeline(
    openai_api_key=os.environ["OPENAI_API_KEY"],
    legal_topics_path="rag_pipeline/config/list_chude_demuc.txt",
    config_path="rag_pipeline/config/agent.json")

output_folder = '../benchmark_output/rag-pipeline-v1'

files = glob.glob('../benchmark_v2/*')
files

for file in files:
    with open(file) as f1:
        standard_dict = json.load(f1)
    file_name = file.split('/')[-1]
    if os.path.exists(f'{output_folder}/{file_name}'):
        print(f'{output_folder}/{file_name} exist')
        with open(f'{output_folder}/{file_name}') as f1:
            standard_dict = json.load(f1)
    standard_dict_with_answer = standard_dict.copy()

    for ix, element in tqdm(enumerate(standard_dict_with_answer)):
        if "prediction" in standard_dict_with_answer[ix].keys(): continue
        query = f"{element['instruction']}\n{element['question']}"
        answer = pipeline.run(query)['agent6_output']
        standard_dict_with_answer[ix]['prediction'] = answer

        with open(f'{output_folder}/{file_name}', 'w') as f1:
            json.dump(standard_dict_with_answer, f1, indent=4, ensure_ascii=False)