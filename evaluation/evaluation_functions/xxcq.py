from utils.function_utils import compute_ie_f1

def compute_xxcq(content):

    entity_types = ['Nghi phạm', 'Nạn nhân', 'Tài sản bị đánh cắp', 'Công cụ gây án', 'Thời gian', 'Địa điểm', 'Tổ chức pháp lý', 
                'Tội danh', 'Phán quyết']
    references, predictions = [], []
    for example in content:
        predictions.append(example["prediction"])
        references.append(example["answer"])

    result = compute_ie_f1(predictions, references, entity_types)
    # result
    return result