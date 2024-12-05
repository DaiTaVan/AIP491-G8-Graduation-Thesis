from utils.function_utils import compute_rouge

def compute_yqzy(content):
    references, predictions = [], []
    for example in content:
        predictions.append(example["prediction"])
        references.append(example["answer"])

    result = compute_rouge(predictions, references)
    # result
    return result