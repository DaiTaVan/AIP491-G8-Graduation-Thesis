from utils.function_utils import split_by_characters, compute_f1_two_sets, calculate_max_score
from utils.evaluate_CoQA import CoQAEvaluator

def compute_sjjc(content):
    option_list = ['thanh toán', 'lừa dối', 'khám xét', 'yêu cầu', 'bán ra', 'mua vào', 'thu lợi', 'bắt giữ', 'giám định', 
               'đồng ý', 'khai báo', 'đề nghị', 'liên lạc', 'thuê', 'bị thương', 'giả mạo', 'mại dâm', 
               'xâm hại thân thể', 'bồi thường', 'hoàn trả']

    score_list, abstentions = [], 0
    for example in content:
        prediction, answer = example["prediction"], example["answer"]

        answers = split_by_characters(answer, [',', ';'])
        prediction_list = split_by_characters(prediction, [',', ';'])
        for option in option_list:
            if option in prediction:
                prediction_list.append(option)

        if len(prediction_list) == 0:
            abstentions += 1
        gt_set = set(answers)
        pred_set = set(prediction_list)
        score = compute_f1_two_sets(gt_set, pred_set)
        score_list.append(score)
        
    f1_score_average = sum(score_list) / len(score_list)
    fn_result  = {"score": f1_score_average, "abstention_rate": abstentions/len(content)}

    return fn_result

def compute_cfcy(content):
    scores = 0
    for example in content:
        prediction, answer = example["prediction"], example["answer"]

        prediction_set = list(set(split_by_characters(prediction, [',', ';'])))
        answer_set = list(set(split_by_characters(answer, [',', ';'])))
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
    # f1_score_average

    return {"score": f1_score_average}