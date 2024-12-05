from utils.function_utils import compute_rouge

def compute_ftcs(content):
    groundtruths = []
    predictions = []
    for ele in content:
        groundtruths.append(ele['answer'])
        predictions.append(ele['prediction'])

    average_rouge_l = compute_rouge(predictions, groundtruths)
    # average_rouge_l
    return average_rouge_l