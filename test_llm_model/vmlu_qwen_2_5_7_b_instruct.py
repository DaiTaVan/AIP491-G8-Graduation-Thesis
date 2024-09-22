# make sure to use vllm 0.3.3 and transformers 4.40+
import os
os.environ["CUDA_VISIBLE_DEVICES"]="2"
import json
# from vllm import LLM, SamplingParams
import csv
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from tqdm import tqdm

device = "cuda" # the device to load the model onto
model_path = "Qwen2.5-7B-Instruct"
model = AutoModelForCausalLM.from_pretrained(
  model_path, # can change to "SeaLLMs/SeaLLMs-v3-1.5B-Chat" if your resource is limited
  torch_dtype="auto", 
  device_map=device
)
tokenizer = AutoTokenizer.from_pretrained(model_path)

jsonl_path = f"/data2/dai/temp/vmlu_v1.5/test.jsonl"
out_csv_path = f"/data2/dai/temp/vmlu_v1.5/Qwen2-5_7B_Instruct_vmlu_pred.csv"

def read_json(json_file):
    print(f'Reading : {json_file}')
    with open(json_file, 'r', encoding='utf-8') as f:
        rows = [json.loads(x) for x in f]
    return rows

questions = read_json(jsonl_path)



eos_token = "<|im_end|>"
CHAT_TEMPLATE = """<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
"""

# sampling_params = SamplingParams(temperature=0.0, max_tokens=5, stop=[eos_token])
# model = LLM(model_path, dtype="bfloat16", device=f"cuda:2")


question_template = """Chỉ đưa ra chữ cái đứng trước câu trả lời đúng (A, B, C, D hoặc E) của câu hỏi trắc nghiệm sau:

{question}
{choices}
Đáp án:"""

def to_prompt(item):
    question = question_template.format(
        question=item['question'],
        choices="\n".join(item['choices'])
    )
    prompt = CHAT_TEMPLATE.format(prompt=question)
    return prompt


prompts = [to_prompt(q) for q in questions]

print(prompts[0])

# generated = model.generate(prompts, sampling_params)
# responses = [g.outputs[0].text for g in generated]

responses = []

for prompt in tqdm(prompts):
    model_inputs = tokenizer([prompt], return_tensors="pt").to(device)
    generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=5, do_sample=False, eos_token_id=tokenizer.eos_token_id, temperature=0.0)
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
    responses.append(response[0])
    # print(response[0])

answers = [r.strip() for r in responses]
# first output can be "A" or " A" (2 different token)
# extract first character, empty '' if nothing in the answer
answers = [(r[0] if len(r) > 0 else '') for r in answers]


assert len(answers) == len(questions)
print(answers[:10])

with open(out_csv_path, 'w', encoding='utf-8') as f:
    write = csv.writer(f)
    _ = write.writerow(["id", "answer"])
    for q, pred in zip(questions, answers):
        _ = write.writerow([q['id'], pred])


print(f"prediction saved at {out_csv_path}")
