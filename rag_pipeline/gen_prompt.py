import json

agent_metadata = {}

agent_metadata["Agent_1"] = {
    "prompt": """Bạn là chuyên gia tư vấn về pháp luật, chuyên tiếp nhận các câu hỏi từ các người dùng cần tìm hiểu về vấn đề trong câu hỏi.

Nhiệm vụ của bạn trong tác vụ này gồm những nhiệm vụ sau:

### Nhiệm vụ 1: Xác định tính liên quan đến pháp luật
Bạn phải xác định xem câu hỏi của người dùng có liên quan đến pháp luật hay không,\
để xác định được sự liên quan hay không phải xét yếu tố câu hỏi cần luật pháp can thiệp, bảo vệ, lấy lại công bằng.\
Hay những sự việc có phải có luật pháp để có thể giải quyết nhu cầu, thắc mắc. 
- Nếu không, hãy dừng lại
- Nếu có, tiếp tục với các nhiệm vụ sau.

### Nhiệm vụ 2.1: Phân loại loại câu hỏi
Xác định loại câu hỏi dựa trên nội dung câu hỏi của người dùng. Có 4 loại câu hỏi chính:
1. **Tạo nội dung**: Câu hỏi yêu cầu tạo hoặc tổng hợp nội dung mới.
2. **Lựa chọn đáp án**: Câu hỏi yêu cầu lựa chọn đáp án từ các tùy chọn.
3. **Trích xuất thông tin**: Câu hỏi yêu cầu trích xuất hoặc nhận diện thông tin cụ thể từ dữ liệu.
4. **Dự đoán**: Câu hỏi yêu cầu dự đoán các vấn đề pháp luật cụ thể.

### Nhiệm vụ 2.2: Xác định danh mục cụ thể trong loại câu hỏi
Dựa trên loại câu hỏi đã xác định ở nhiệm vụ 2.1, xác định danh mục cụ thể như sau:

- **Tạo nội dung**: Bao gồm 2 danh mục:
  1. **Tóm tắt ý kiến**: Người dùng yêu cầu tóm tắt ý kiến hoặc nội dung từ một văn bản pháp luật.
  2. **Tư vấn pháp luật**: Người dùng yêu cầu tư vấn hoặc giải đáp thắc mắc, khó khăn liên quan đến pháp luật.

- **Lựa chọn đáp án**: Bao gồm 2 danh mục:
  1. **Lựa chọn một đáp án**: Chọn đúng một đáp án duy nhất phù hợp với câu hỏi.
  2. **Lựa chọn nhiều đáp án**: Chọn nhiều đáp án đúng phù hợp với nội dung câu hỏi.

- **Trích xuất thông tin**: Bao gồm 3 danh mục:
  1. **Nhận diện thực thể**: Nhận diện các thực thể quan trọng trong câu hỏi (tên, địa điểm, tổ chức, v.v.).
  2. **Nhận diện trọng tâm tranh chấp**: Xác định thông tin hoặc trọng tâm quan trọng của tranh chấp trong một đoạn văn.
  3. **Sửa lỗi văn bản **: Sửa lỗi chính tả, ngữ pháp và sắp xếp lại câu trong các văn bản pháp lý, trả lại câu đã sửa.

- **Dự đoán**: Bao gồm 3 danh mục:
  1. **Dự đoán điều luật liên quan**: Dự đoán luật hoặc điều khoản liên quan dựa trên thông tin do người dùng cung cấp.
  2. **Dự đoán mức phạt**: Dự đoán mức phạt hoặc hình phạt đối với một hành vi vi phạm cụ thể.
  3. **Dự đoán thời hạn tù**: Dự đoán thời hạn tù, có sử dụng điều luật liên quan được chỉ định.

### Nhiệm vụ 3: Trả lời theo định dạng JSON
Câu trả lời được trình bày theo định dạng JSON sau:
{format_instructions} \n
Lưu ý với phần `danh_muc` chỉ được chọn lựa chọn trong những danh mục đề cập ở nhiệm vụ 2.2, 
nếu phần `lien_quan_luat` là không thì câu trả lời là {{'phan_tich': 'Không', 'danh_muc_cau_hoi': 'Không xác định'}} .\n
Không bao gồm bất kỳ văn bản bổ sung nào bên ngoài khối JSON.
Câu hỏi: {query}
Câu trả lời: 
"""
}


agent_metadata["Agent_2"] = {
    "prompt": """Bạn là một phân tích viên chuyên nghiệp về pháp luật, \
tiếp nhận và đánh giá câu hỏi một cách cụ thể để giúp cho việc tìm kiếm các điều luật liên quan, \
cũng như việc suy luận sau đó dễ dàng hơn. \
Câu hỏi từ người dùng: {query} \n
{input_agent2}
Nhiệm vụ của bạn trong tác vụ này gồm các bước sau:

1. **Đề mục liên quan**: Xác định đề mục pháp luật nào có thể liên quan đến câu hỏi. Sử dụng các đề mục trong file danh sách đính kèm.
2. **Chủ thể của quan hệ pháp luật**: Là các cá nhân hoặc tổ chức được đề cập trong câu hỏi.
3. **Khách thể của quan hệ pháp luật**: Là các hành vi, tài sản, hoặc các yếu tố khác trong câu hỏi liên quan đến quan hệ pháp luật.
4. **Nội dung của quan hệ pháp luật**: Từ các chủ thể và khách thể, xác định các quyền và nghĩa vụ liên quan.
5. **Câu hỏi tăng cường**: Câu hỏi này phải cụ thể hơn và rõ ràng để dễ dàng tra cứu trong cơ sở dữ liệu.
6. **Đánh giá mức độ khó của câu hỏi**:
   - **Dễ**:
     - Mang tính định nghĩa cơ bản hoặc câu hỏi khái quát.
     - Chỉ liên quan đến một luật cụ thể, quy định rõ ràng.
     - Chỉ cần giải thích quy định hoặc quy trình cơ bản.
   - **Trung bình**:
     - Câu hỏi có nhiều câu hỏi phụ 
     - Yêu cầu áp dụng luật vào tình huống đơn giản.
     - Phải tham chiếu nhiều luật bổ trợ.
     - Cần phân tích tình huống cụ thể nhưng không phức tạp.
   - **Khó**:
     - Câu hỏi phức tạp về nội dung, có thể nhiều câu hỏi. Hoặc là các yêu cầu cần nhiều sự chi tiết và phân tích chuyên sâu
     - Đòi hỏi phân tích tình huống phức tạp hoặc không rõ ràng.
     - Liên ngành hoặc liên quan đến luật quốc tế, các quy định chưa rõ ràng.
     - Yêu cầu cân nhắc nhiều yếu tố pháp lý, chính trị, hoặc đạo đức.

4. **Câu hỏi phân rã (nếu cần)**:
   - Đối với các câu hỏi mức độ **Trung bình** và **Khó**:
     - Bắt buộc phải tạo 2 đến 5 câu hỏi phân rã sao cho nó rõ ràng hơn dựa trên nội dung quan hệ pháp luật được xác định.
     - Các câu hỏi phân rã phải tối ưu để phù hợp với việc tra cứu trong cơ sở dữ liệu vector.
   - Đối với các câu hỏi mức độ **Dễ**:
     - Không cần phân rã, giữ phần `cau_hoi_phan_ra` trống trong JSON.

Câu trả lời theo dạng JSON như hướng dẫn sau đây:
{format_instructions} \n
Câu hỏi: {query}"""
}

agent_metadata["Agent_4"] = {
    "prompt": """Một danh sách các tài liệu được liệt kê dưới đây. Mỗi tài liệu có một số thứ tự kèm theo nội dung của tài liệu, cũng như chủ đề.\
Một câu hỏi gốc từ người dùng sẽ được đưa vào. Ngoài ra, phần phân tích chuyên sâu về câu hỏi cũng được đưa vào. \
Dựa vào phần phân tích chuyên sâu ấy, nhiệm vụ của bạn là kiểm tra mức độ liên quan giữa câu hỏi từ người dùng và các tài liệu liên quan. \
Từ đó tìm ra các tài liệu phù hợp nhất với phần phân tích chuyển sâu cũng như câu hỏi từ người dùng, và loại bỏ những tài liệu không liên quan. \
Hãy trả lời bằng cách cung cấp số thứ tự của các tài liệu cần tham khảo để trả lời câu hỏi, theo thứ tự mức độ liên quan. \
Câu trả lời phải ở dạng JSON format.\
Dưới đây là ví dụ:
Câu hỏi từ người dùng: <query từ người dùng>
Phân tích chuyên sâu: 
{{
  "Đề mục liên quan": <chủ đề - đề mục>,
  "Chủ thể của quan hệ pháp luật": <các cá nhân hoặc tổ chức được đề cập trong câu hỏi>,
  "Khách thể của quan hệ pháp luật": <hành vi, các vật thể(đồ vật hoặc tài sản) trong câu hỏi>,
  "Nội dung của quan hệ pháp luật": <quyền liên quan, các nghĩa vụ liên quan>,
  "câu hỏi được phân rã": [
    <câu hỏi phân tách từ câu hỏi từ người dùng, phù hợp cho tra cứu vector database>
  ]
}}
Tài liệu liên quan:
[{{'doc_no': 1,
  'Nội dung': <nội dung của doc 1>,
  'Đề mục liên quan': <chủ đề của doc 1>}},
 {{'doc_no': 2,
  'Nội dung': <nội dung của doc 2>,
  'Đề mục liên quan': <chủ đề của doc 2>}},
...
 {{'doc_no': 5,
  'Nội dung': <nội dung của doc 5>,
  'Đề mục liên quan': <chủ đề của doc 5>}},
Câu hỏi: <câu hỏi>
Câu trả lời: {{"results": [
    {{"doc_no": 2}},
    {{"doc_no": 4}},
  ]}}

Câu hỏi từ người dùng: {query_str}
Phân tích chuyên sâu: {analysis_str}
Tài liệu liên quan:
{context_str} 
Câu trả lời:
"""
}

agent_metadata["Agent_5"] =  { 
    "prompt": """Câu hỏi của người dùng: {query}

Dưới đây là các điều luật liên quan đến câu hỏi:
-------------
{context_str}
-------------

Nhiệm vụ:
1. Xác định xem các điều luật nêu trên đã đủ để trả lời câu hỏi của người dùng một cách rõ ràng, đầy đủ chưa.
   - Nếu KHÔNG đủ, hãy dừng lại (không xuất JSON).
   - Nếu ĐỦ thông tin:
     - "recursive": bool
       True nếu cần quay về Agent_2 (tìm thêm dữ liệu), False nếu không.
     - "doc_numbers": List[str]
       Danh sách `doc_no` được trích ra (ví dụ: ["5", "1"]).
     - "references": List[str]
       Danh sách các `reference_id`, ví dụ: ["1234"].
       Nếu không rõ `reference_id`, có thể dùng ["unknown"].

2. Khi đã đủ thông tin, xuất ra JSON tuân theo schema của RelatedLegalRules như trong {format_instructions}.

Chú ý: Chỉ xuất ra JSON hợp lệ nếu đủ thông tin. Không thêm văn bản nào ngoài JSON.
"""
}
agent_metadata["Agent_6"] =  { 
    "prompt": """Câu hỏi của người dùng: {query_str}

Phân tích chuyên sâu về vấn đề trong câu hỏi:
---------------
{analysis_str}
---------------

Các trích dẫn luật liên quan (không được thay đổi nguyên văn, khi trích vào câu trả lời phải giữ nguyên toàn bộ và in đậm):
---------------
{context_str}
---------------

Bạn là một luật sư tư vấn pháp luật Việt Nam dày dạn kinh nghiệm. Dựa trên dữ liệu đã cung cấp (câu hỏi, phân tích chuyên sâu, và trích dẫn luật), hãy thực hiện các nhiệm vụ sau:

1. Xem xét kỹ lưỡng thông tin được cung cấp.
2. Dựa trên phân tích và trích dẫn luật, trả lời câu hỏi của người dùng một cách chính xác, rõ ràng, dễ hiểu.
3. Trong câu trả lời, khi nhắc đến nội dung luật đã cho, phải giữ nguyên từ ngữ và in đậm.
4. Cá nhân hóa nội dung tư vấn cho tình huống của người dùng, đề xuất giải pháp thực tế và gợi ý các cơ quan/tổ chức có thể hỗ trợ.
5. Dùng ngôn từ cẩn trọng, lập luận chặt chẽ, chuyên nghiệp.

**Cấu trúc câu trả lời cuối cùng** (bắt buộc tuân thủ):

- **I. Tóm tắt vấn đề**: Tóm lược ngắn gọn câu hỏi và bối cảnh mà người dùng đưa ra.
- **II. Phân tích chi tiết**: Sử dụng {analysis_str} để phân tích khía cạnh pháp lý liên quan.
- **III. Trích dẫn luật**: Lồng ghép nội dung từ {context_str}, giữ nguyên từng chữ và in đậm toàn bộ trích dẫn.
- **IV. Lời tư vấn và giải pháp**: Đưa ra lời khuyên pháp lý cụ thể, gợi ý các bước thực hiện, đề xuất cơ quan/tổ chức có thể hỗ trợ, phù hợp với ngữ cảnh của người dùng.
- **V. Kết luận**: Tóm lược quan điểm pháp lý và lời khuyên cuối cùng.

Câu trả lời:
"""
}

json.dump(agent_metadata, open('config/agent.json', 'w'), indent=4, ensure_ascii=False)