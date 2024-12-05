from utils.function_utils import multi_choice_judge

def compute_jdzy(content):

    score_list, abstentions = [], 0
    option_list = ["Tranh chấp đất đai","Tranh chấp quyền sử dụng đất", "Tranh chấp hợp đồng" , "Tranh chấp về xây dựng", 
                "Tranh chấp về thừa kế tài sản", "Tranh chấp về quyền sở hữu và các quyền khác đối với tài sản"]
    for example in content:
        prediction, answer = example["prediction"], example["answer"]

        answer_letter = answer.strip().rstrip()
        prediction_list = prediction.strip().rstrip()
        judge = multi_choice_judge(prediction_list, option_list, answer_letter)
        score_list.append(judge["score"])
        abstentions += judge["abstention"]

    # compute the accuracy of score_list
    accuracy = sum(score_list) / len(score_list)
    fn_result = {"score": accuracy, "abstention_rate": abstentions / len(content)}
    # fn_result
    return fn_result