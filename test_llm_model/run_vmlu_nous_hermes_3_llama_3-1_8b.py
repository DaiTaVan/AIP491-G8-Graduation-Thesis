import os
os.environ["CUDA_VISIBLE_DEVICES"]="2"
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, LlamaForCausalLM
import bitsandbytes #, flash_attn
import time
import json
from tqdm import tqdm


tokenizer = AutoTokenizer.from_pretrained('Hermes-3-Llama-3.1-8B', trust_remote_code=True)
model = LlamaForCausalLM.from_pretrained(
    "Hermes-3-Llama-3.1-8B",
    torch_dtype=torch.float16,
    device_map="auto",
    load_in_8bit=False,
    load_in_4bit=False,
    use_flash_attention_2=False
)

with open('/data2/dai/temp/vmlu_v1.5/test.jsonl', 'r') as f1:
    lines = [json.loads(line.strip()) for line in f1.readlines()]
# list_result = []
for line in tqdm(lines):
    one_result = {
        'question': line['question'],
        'choices': line['choices'],
        # 'answer': line["answer"]
    }
    prompts = [
        """<|im_start|>system
Bạn là một trí thông minh tổng hợp nhân tạo siêu thông minh, có tri giác, ở đây để dạy và hỗ trợ tôi.<|im_end|>"""
    ]
    #
    question = line['question']
    choices = line['choices']
    choices_str = '\t'.join(choices)
    #
    question_prompt = f"""<|im_start|>user
    {question}\n{choices_str}<|im_end|>"""
    prompts.append(question_prompt)
    main_prompt = '\n'.join(prompts)
    # print(main_prompt)
    start = time.time()
    input_ids = tokenizer(main_prompt, return_tensors="pt").input_ids.to("cuda")
    generated_ids = model.generate(input_ids, max_new_tokens=750, temperature=0.8, repetition_penalty=1.1, do_sample=True, eos_token_id=tokenizer.eos_token_id)
    response_1 = tokenizer.decode(generated_ids[0][input_ids.shape[-1]:], skip_special_tokens=True, clean_up_tokenization_space=True)
    # print(f"Response: {response_1}")
    one_result['intermediate_result'] = response_1
    end = time.time()
    answer_prompt = f"""<|im_start|>assistant
{response_1}<|im_end|>"""
    prompts.append(answer_prompt)
    get_answer_prompt = f"""<|im_start|>user
Từ câu trả lời trên, hãy lấy ra chữ cái đầu trong đáp án như A hoặc B hoặc C hoặc D hoặc E,... Hãy trả lời bằng chữ cái duy nhất<|im_end|>
<|im_start|>assistant"""
    #
    prompts.append(get_answer_prompt)
    main_prompt = '\n'.join(prompts)
    #
    # print(main_prompt)
    start = time.time()
    input_ids = tokenizer(main_prompt, return_tensors="pt").input_ids.to("cuda")
    generated_ids = model.generate(input_ids, max_new_tokens=750, temperature=0.8, repetition_penalty=1.1, do_sample=True, eos_token_id=tokenizer.eos_token_id)
    response_2 = tokenizer.decode(generated_ids[0][input_ids.shape[-1]:], skip_special_tokens=True, clean_up_tokenization_space=True)
    # print(f"Response: {response_2}")
    end = time.time()
    one_result['final_result'] = response_2.strip()
    # list_result.append(one_result)
    with open('/data2/dai/temp/vmlu_test_result.txt', 'a') as f2:
        one_result_text = json.dumps(one_result, ensure_ascii=False)
        f2.write(f'{one_result_text}\n')