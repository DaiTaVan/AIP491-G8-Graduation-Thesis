from utils.function_utils import compute_rouge

def compute_flzx(content):
    references, predictions = [], []
    for example in content:
        predictions.append(example["prediction"])
        references.append(example["answer"])

    average_rouge_l = compute_rouge(predictions, references)
    # average_rouge_l
    return  average_rouge_l