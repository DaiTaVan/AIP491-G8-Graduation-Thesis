import re

def compute_wbfl(content):

    def parse_choice_from_text(text: str):
        result = None
        matches_1 = re.match(r"\[Thể loại\]\s*(.*)", text)
        fn_result = []
        if matches_1:
            result = matches_1.group(1).replace('.', '').strip().rstrip()
            result = [ele.strip().rstrip() for ele in result.split(';')]
            fn_result = []
            for ele in result:
                if "khác" not in ele and "sinh sản" not in ele and "về xác định cha" not in ele:
                    fn_result.extend([sub_ele.strip().rstrip() for sub_ele in ele.split(',')])
                else:
                    fn_result.append(ele)
        if not result:
            matches_2 = re.match("\[(.*?)\]", text)

            if matches_2:
                result = matches_2.group(1).replace('.', '')
                result = [ele.strip().rstrip() for ele in result.split(';')]
                fn_result = []
                for ele in result:
                    if "khác" not in ele and "sinh sản" not in ele and "về xác định cha" not in ele:
                        fn_result.extend([sub_ele.strip().rstrip() for sub_ele in ele.split(',')])
                    else:
                        fn_result.append(ele)
        return fn_result


    score_list, abstentions = [], 0
    option_list = ['Ly hôn và tranh chấp về nuôi con khi ly hôn', 'Ly hôn và tranh chấp chia tài sản khi ly hôn', 'Ly hôn và chia tài sản sau khi ly hôn', 
                'Tranh chấp về chia tài sản chung của vợ chồng trong thời kỳ hôn nhân', 'Tranh chấp tài sản trước hôn nhân', 'Tranh chấp về thay đổi người trực tiếp nuôi con sau khi ly hôn', 
                'Tranh chấp về xác định cha, mẹ cho con hoặc xác định con cho cha, mẹ',  'Tranh chấp về cấp dưỡng', 'Tranh chấp về sinh con bằng kỹ thuật hỗ trợ sinh sản, mang thai hộ vì mục đích nhân đạo',  
                'Tranh chấp về nuôi con của nam, nữ chung sống với nhau như vợ chồng mà không đăng ký kết hôn hoặc khi hủy kết hôn trái pháp luật', 
                'Tranh chấp về chia tài sản của nam, nữ chung sống với nhau như vợ chồng mà không đăng ký kết hôn hoặc khi hủy kết hôn trái pháp luật', 
                'Các tranh chấp khác về hôn nhân và gia đình, trừ trường hợp thuộc thẩm quyền giải quyết của cơ quan, tổ chức khác theo quy định của pháp luật']

    for example in content:
        prediction, answer = example["prediction"], example["answer"]
        gt_list = parse_choice_from_text(answer)
        for ele in gt_list:
            assert ele in option_list, print(ele, answer)

        gt_set = set(gt_list)

        prediction = parse_choice_from_text(prediction)
        prediction_list = []
        for option in option_list:
            if option in prediction:
                prediction_list.append(option)
        if len(prediction_list) == 0:
            abstentions += 1
        predict_set = set(prediction_list)
        precision = len(gt_set.intersection(predict_set)) / len(predict_set) if len(predict_set) != 0 else 0
        recall = len(gt_set.intersection(predict_set)) / len(gt_set) if len(gt_set) != 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) != 0 else 0
        score_list.append(f1_score)

    # compute the accuracy of score_list
    final_f1_score = sum(score_list) / len(score_list)
    fn_result = {'score': final_f1_score, 'abstention_rate': abstentions / len(content)}
    # fn_result
    return fn_result