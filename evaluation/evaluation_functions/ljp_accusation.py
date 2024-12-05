import re
from utils.evaluate_CoQA import CoQAEvaluator
from utils.function_utils import split_by_characters, calculate_max_score

def compute_ljp_accusation(content):

    def parse_choice_from_text(text: str):
        result = None
        matches_1 = re.match(r"\[\s*[^]]*\s*\]\s*(.*)", text)
        if matches_1:
            result = matches_1.group(1).replace('.', '').strip().rstrip()
        return result


    scores = 0
    for example in content:
        prediction, answer = example["prediction"], example["answer"]

        prediction_set = list(set(split_by_characters(parse_choice_from_text(prediction), [',', ';'])))
        answer_set = list(set(split_by_characters(parse_choice_from_text(answer), [',', ';'])))
        # print(prediction_set, answer_set)
        score_func = lambda ans, pred: CoQAEvaluator.compute_f1(ans, pred)

        max_score = calculate_max_score(answer_set, prediction_set, score_func)

        prec = max_score / len(prediction_set) if len(prediction_set) > 0 else 0
        rec = max_score / len(answer_set) if len(answer_set) > 0 else 0
        # print(prec, rec, max_score)
        scores += 2 * prec * rec / (prec + rec + 1e-10)
        # print(scores)
        # break


    f1_score_average = scores / len(content)
    f1_score_average
    return {"score": f1_score_average}