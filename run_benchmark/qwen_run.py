import os
import json
import glob
from tqdm import tqdm

from rag_pipeline.src.llm import Qwen

llm_engine = Qwen(
    temperature=0.7,
    top_p=0.8,
)

output_folder = '../benchmark_output/Qwen2.5-7B-Instruct'
output_folder = '../benchmark_output/Qwen2.5-7B-Instruct-Finetune-Law'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

list_benchmark_files = glob.glob('../benchmark/*')

for benchmark_file in list_benchmark_files:
    with open(benchmark_file) as f1:
        standard_dict = json.load(f1)
    
    standard_dict_with_answer = standard_dict.copy()

    for ix, element in tqdm(enumerate(standard_dict_with_answer)):
        query = f"{element['instruction']}\n{element['question']}"
        answer = llm_engine.generate(query)
        standard_dict_with_answer[ix]['prediction'] = answer

    benchmark_file_name = benchmark_file.split('/')[-1]
    with open(f'{output_folder}/{benchmark_file_name}', 'w') as f1:
        json.dump(standard_dict_with_answer, f1, indent=4, ensure_ascii=False)