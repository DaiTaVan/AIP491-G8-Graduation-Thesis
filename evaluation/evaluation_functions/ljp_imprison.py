import re
import math

def compute_ljp_imprison(content):

    def extract_imprision(text: str):
        result = {'year': 0, 'month': 0, 'special': None, 'error': 0}
        if 'từ' in text.lower():
            result['error'] = 1
        elif 'tử hình' in text.lower():
            result['special'] = 'tử hình'
        elif 'chung thân' in text.lower():
            result['special'] = 'chung thân'
        else:
            pattern = r"(\d+)\s*(năm|tháng)"
            matches = re.findall(pattern, text)

            if len(matches) == 0: 
                result['error'] = 1
            
            # print(f"Text: {text}")
            # print(f"Extracted values: {matches}")
            for ele in matches:
                if ele[1] == 'năm':
                    result['year'] = int(ele[0])
                elif ele[1] == 'tháng':
                    result['month'] = int(ele[0])

        return result

    score_list, abstentions = [], 0
    for example in content:
        prediction, answer = example["prediction"], example["answer"]

        prediction_imprision = extract_imprision(prediction)
        answer_imprision = extract_imprision(answer)

        if answer_imprision['error'] == 1:
            raise Exception

        if prediction_imprision['error'] == 1:
            abstentions += 1
            score_list.append(math.log(216))
            continue
        
        
        if answer_imprision['special'] is not None:
            continue

        prediction_digit = prediction_imprision['year'] * 12 + prediction_imprision['month']
        answer_digit = answer_imprision['year'] * 12 + answer_imprision['month']

        score_list.append(abs(math.log(answer_digit +1)- math.log(prediction_digit + 1)))

    # compute the average of score_list (log distance)
    log_distance = sum(score_list) / len(score_list)
    # normalize the score to between 0 and 1
    log_distance = (math.log(216) - log_distance)/math.log(216)
    fn_result = {"score": log_distance, "abstention_rate": abstentions/len(content)}
    # fn_result
    return fn_result