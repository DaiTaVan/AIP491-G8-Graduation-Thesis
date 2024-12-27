import os
import json
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate

# Set up directories
input_dir = '../benchmark'
output_dir = '../benchmark_output/Gemini-1.5-Flash'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Initialize the LLM
llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key="")

# Define your prompt template
# Here we assume the data has "instruction" and "question" fields and you want to get the LLM's answer.
# Modify as needed.
template = ChatPromptTemplate.from_messages([
    SystemMessage(content="Bạn là một chuyên gia về luật Việt Nam. Hãy trả lời câu hỏi dưới đây cũng như theo hướng dẫn người dùng"),
    HumanMessagePromptTemplate.from_template("{instruction}\n{question}")
])

chain = LLMChain(llm=llm, prompt=template)

def process_chunk(chunk):
    results = []
    for _, row in chunk.iterrows():
        # Each row has 'instruction', 'question', 'answer' fields (from your given format)
        # You can choose whether you want to verify or just regenerate the answer.
        # For demonstration, we call the LLM with the instruction and question.
        user_instruction = row['instruction']
        user_question = row['question']
        
        # Call the chain
        response = chain.run(instruction=user_instruction, question=user_question)
        
        # Store the response along with the original data if you wish
        results.append({
            "instruction": user_instruction,
            "question": user_question,
            "prediction": response,
            "answer": row['answer']
        })
    return results

def process_file(file_path):
    # Load data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to DataFrame for easy chunking (if data is large)
    df = pd.DataFrame(data)
    
    num_threads = 30
    # Determine chunk size
    chunk_size = max(1, len(df) // num_threads)
    if chunk_size == 0:
        chunk_size = len(df)
    
    chunks = [df.iloc[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
    
    results = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        for fut in tqdm(futures, desc=f"Processing {os.path.basename(file_path)}"):
            results.extend(fut.result())
    
    # Save the results in the output folder with the same filename
    output_file = os.path.join(output_dir, os.path.basename(file_path))
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Processing of {file_path} completed. Results saved to {output_file}")

# Iterate over all JSON files in the benchmark directory
for filename in os.listdir(input_dir):
    if filename.endswith('.json'):
        input_file_path = os.path.join(input_dir, filename)
        process_file(input_file_path)
