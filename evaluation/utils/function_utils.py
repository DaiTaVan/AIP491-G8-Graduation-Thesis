import re
from rouge import Rouge
from munkres import Munkres
from .evaluate_CoQA import CoQAEvaluator

def compute_rouge(hyps, refs):
    assert len(hyps) == len(refs)
    rouge_scores =  Rouge().get_scores(hyps, refs)
    rouge_ls = [score["rouge-l"]["f"] for score in rouge_scores]
    average_rouge_l = sum(rouge_ls) / len(rouge_ls)
    return {"score": average_rouge_l}

def multi_choice_judge(prediction, option_list, answer_token):
    # a dict, key: letters in the option list, value: count of the letter in the prediction
    count_dict, abstention, accuracy = {}, 0, 0
    for option in option_list:
        option_count = prediction.count(option)
        count_dict[option] = 1 if option_count > 0 else 0  # multiple occurrence of the same letter is counted as 1

    if sum(count_dict.values()) == 0:
        abstention = 1
    # if the answer token is the only predicted token, the prediction is correct 
    elif count_dict[answer_token] == 1 and sum(count_dict.values()) == 1:
        accuracy = 1
    return {"score": accuracy, "abstention": abstention}

def split_by_characters(input_string, characters):
    """
    Splits a string by any character in a given list of characters.
    
    Args:
        input_string (str): The string to split.
        characters (list): A list of characters to split by.
    
    Returns:
        list: A list of substrings after splitting.
    """

    # Create a regex pattern to match any character in the list
    pattern = f"[{''.join(re.escape(char) for char in characters)}]"
    # Split the string using the regex pattern
    return [ele.strip().rstrip() for ele in re.split(pattern, input_string)]


def calculate_max_score(set_a, set_b, score_func):
    """
    Calculates the maximum score using the Hungarian Algorithm.
    
    Args:
        set_a (list): The first set of elements.
        set_b (list): The second set of elements.
        score_func (function): A function that computes the score between two elements.
        
    Returns:
        float: The maximum score.
        list: The optimal matching pairs.
    """
    # Ensure the sets have the same size by padding the smaller one with dummy elements
    size = max(len(set_a), len(set_b))
    padded_a = set_a + [None] * (size - len(set_a))
    padded_b = set_b + [None] * (size - len(set_b))
    
    # Create the cost matrix (negative of score for maximization)
    cost_matrix = []
    for a in padded_a:
        row = []
        for b in padded_b:
            if a is None or b is None:
                row.append(0)  # No score for dummy elements
            else:
                row.append(-score_func(a, b))  # Use negative score for maximization
        cost_matrix.append(row)
    
    # Apply the Hungarian Algorithm
    m = Munkres()
    indexes = m.compute(cost_matrix)
    
    # Calculate the maximum score
    max_score = 0
    pairs = []
    for row, col in indexes:
        if padded_a[row] is not None and padded_b[col] is not None:
            max_score += -cost_matrix[row][col]  # Convert back to positive score
            pairs.append((padded_a[row], padded_b[col]))
    
    return max_score

# Example usage
# set_a = [1, 2, 3]
# set_b = [10, 20]
# score_func = lambda a, b: abs(a - b)  # Example score function: negative absolute difference

# max_score = calculate_max_score(set_a, set_b, score_func)
# print(f"Maximum Score: {max_score}")


def extract_entities_from_text(text, entity_labels):
    dict_entity = {}
    for entity_label in entity_labels:
        pattern = f"{entity_label}:\s*(.+)"
        match = re.search(pattern, text)
        if match:
            dict_entity[entity_label] = match.group(1).strip().rstrip()
    
    return dict_entity

def compute_ie_f1(hyps, refs, entity_types):
    assert (len(hyps) == len(refs))
    scores, abstentions = 0, 0
    for h, r in zip(hyps, refs):
        h = extract_entities_from_text(h, entity_types)
        r = extract_entities_from_text(r, entity_types)
        if r == {}:
            scores += 1 if h == {} else 0
            continue
        if h == {}:
            abstentions += 1
        intersected = [CoQAEvaluator.compute_f1(r[etype], einstance) for etype, einstance in h.items() if etype in r]
        prec = sum(intersected) / len(h) if len(h) > 0 else 0
        rec = sum(intersected) / len(r) if len(r) > 0 else 0
        # print(prec, rec, intersected)
        scores += 2 * prec * rec / (prec + rec + 1e-10)
    return {'score': scores / len(hyps), "anstention_rate": abstentions / len(hyps)}

# extract_entities_from_text("""Thông tin thực thể từ câu:
#     - Tổ chức pháp lý: Cơ quan công an
#     - Nạn nhân: Ông/bà Hiếu và Bà Ngân
#     - Tài sản bị đánh cắp: Điện thoại""",
#     ['Nghi phạm', 'Nạn nhân', 'Tài sản bị đánh cắp', 'Công cụ gây án', 'Thời gian', 
#                  'Địa điểm', 'Tổ chức pháp lý', 'Tội danh', 'Phán quyết'])

def compute_rc_f1(hyps, refs):
    scores = 0
    for h, r in zip(hyps, refs):
        scores += CoQAEvaluator.compute_f1(r, h)
    return {'score': scores / len(hyps)}

def compute_f1_two_sets(pred_set, gt_set):
    precision = len(pred_set.intersection(gt_set)) / len(pred_set) if len(pred_set) > 0 else 0
    recall = len(pred_set.intersection(gt_set)) / len(gt_set) if len(gt_set) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0
    return f1