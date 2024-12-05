import re
from utils.function_utils import multi_choice_judge

def compute_jec_kd(content):

    def parse_choice_from_text(text: str):
        result = None
        matches_1 = re.match("\[Câu trả lời đúng\][^A-Z]*([A-Z])?", text)

        if matches_1:
            result = matches_1.group(1)
        if not result:
            matches_2 = re.match("Câu trả lời đúng:[^A-Z]*([A-Z])?", text)

            if matches_2:
                result = matches_2.group(1)
        return result


    score_list, abstentions = [], 0
    option_list = ["A", "B", "C", "D"]
    for example in content:
        prediction, answer = example["prediction"], example["answer"]

        answer_letter = parse_choice_from_text(answer)
        prediction_list = [parse_choice_from_text(prediction)]
        judge = multi_choice_judge(prediction_list, option_list, answer_letter)
        score_list.append(judge["score"])
        abstentions += judge["abstention"]

    # compute the accuracy of score_list
    accuracy = sum(score_list) / len(score_list)
    fn_result = {"score": accuracy, "abstention_rate": abstentions / len(content)}
    # result
    return fn_result