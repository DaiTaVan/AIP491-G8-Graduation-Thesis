import re

def compute_ljp_article(content):
    score_list, abstentions = [], 0
    for example in content:
        prediction = example["prediction"]
        reference = example["answer"]

        prediction_numbers = [int(ele) for ele in re.findall(r'\d+', prediction)]
        reference_numbers = [int(ele) for ele in re.findall(r'\d+', reference)]

        gt_set = set(reference_numbers)
        pred_set = set(prediction_numbers)

        if len(pred_set) == 0:
            abstentions += 1

        precision = len(gt_set.intersection(pred_set)) / len(pred_set) if len(pred_set) != 0 else 0
        recall = len(gt_set.intersection(pred_set)) / len(gt_set) if len(gt_set) != 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) != 0 else 0
        score_list.append(f1_score)

    # compute the accuracy of score_list
    average_f1 = sum(score_list) / len(score_list)
    fn_result = {'score': average_f1, 'abstention_rate': abstentions/len(content)}
    # fn_result
    return fn_result