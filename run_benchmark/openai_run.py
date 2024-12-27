import os
import json
import glob
from tqdm import tqdm

from rag_pipeline.src.llm import OpenAI

llm_engine = OpenAI(api_key="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",
                    model_name='gpt-4o', 
                    temperature=0.2)

output_folder = '../benchmark_output/GPT-4o'

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