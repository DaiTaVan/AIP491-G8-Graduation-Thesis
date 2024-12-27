from fastapi import FastAPI, HTTPException
# from typing import List, Dict
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# FastAPI app instance
app = FastAPI()

# model_name = "Qwen/Qwen2.5-7B-Instruct"
model_name = "daitavan/Qwen2.5-7B-Instruct-finetune-llamafactory-bf16"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Define the request schema
class MessageRequest(BaseModel):
    messages: list  # List of message dicts with "role" and "content"
    temperature: float = 0.7
    top_p: float = 0.8
    max_new_tokens: int = 4096

# API route to receive messages and generate answers
@app.post("/generate")
async def generate_answer(request: MessageRequest):
    try:
        # Prepare the input messages
        text = tokenizer.apply_chat_template(
            request.messages,
            tokenize=False,
            add_generation_prompt=True,
            max_length=3072
        )
        
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_p=request.top_p

        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return {"answer": response}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
