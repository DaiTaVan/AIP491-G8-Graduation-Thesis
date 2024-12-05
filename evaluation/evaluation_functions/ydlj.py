from utils.function_utils import compute_rc_f1

def compute_ydlj(content):
    references, predictions = [], []
    for example in content:
        predictions.append(example["prediction"])
        references.append(example["answer"])

    f1_score = compute_rc_f1(predictions, references)
    # f1_score

    return f1_score
