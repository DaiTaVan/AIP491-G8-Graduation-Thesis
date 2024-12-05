import re
from utils.function_utils import multi_choice_judge

def compute_zxfl(content):

    def parse_choice_from_text(text: str):
        result = None
        matches_1 = re.match(r"\[thể loại\]\s*(.*)", text)
        if matches_1:
            result = matches_1.group(1).replace('.', '').strip().rstrip()
            
        return result


    score_list, abstentions = [], 0
    option_list = ['Thuế', 'Lao động', 'An toàn lao động', 'Bảo hiểm xã hội', 'Bảo hiểm thất nghiệp', 'Đầu tư', 'Thương mại', 'Doanh nghiệp', 'Kế toán', 
                'Sở hữu trí tuệ', 'Đất đai - Nhà ở', 'Hôn nhân Gia đình', 'Dân sự', 'Hình sự', 'Bảo vệ môi trường', 'Phòng cháy chữa cháy', 'Tư pháp', 'Đấu thầu', 
                'Xây dựng' , 'Tài chính ngân hàng', 'Bảo hiểm y tế', 'Kinh doanh bất động sản' , 'Hóa chất']
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
    # fn_result
    return fn_result