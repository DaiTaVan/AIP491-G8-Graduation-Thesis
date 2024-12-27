# AIP491_G8 Graduation Thesis

## Setup
### Install library
```
pip install -r requirements.txt
```
### Download database and model
```
wget https://huggingface.co/datasets/daitavan/Vietnam-Law-Raw-Data/resolve/main/database.zip
unzip database.zip
rm database.zip
cd rag_pipeline
git clone daitavan/bge-m3-finetune
```
### Setup env
Create file ```.env``` from ```.env.example``` and enter (or edit) parameters

## Run demo
### Run database
```
docker compose up
```
### Run main demo
#### Not using local LLM
Edit config_path in ```.env```
```
CONFIG_PATH=config/sample_agent.json
```
#### Using local LLM
Run llm api first
```
python local_llm_api/main.py
```
#### Run demo code
```
cd rag_pipeline
python demo.py
```

## Run benchmark 
Run code in folder ```run_benchmark```

## Evaluation benchmark
Following the instruction in ```evaluation```



