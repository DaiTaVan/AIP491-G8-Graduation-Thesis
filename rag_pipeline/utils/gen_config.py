import json

all_llm_type = [
    {
      "type": "openai",
      "model": "gpt-4o",
      "temperature": 0.1
    },
    {
      "type": "openai",
      "model": "gpt-4o-mini",
      "temperature": 0.1
    },
    {
      "type": "ollama",
      "model": "qwen:2.5",
      "temperature": 0.7
    },
]
agent_metadata = {}

agent_metadata["Agent_1"] = {
    "llm": {
      "type": "ollama",
      "model": "qwen:2.5",
      "temperature": 0.7
    },
    "prompt": """
Bạn là chuyên gia tư vấn pháp luật, chuyên giải đáp các câu hỏi liên quan đến pháp luật của người dùng. 
Nhiệm vụ của bạn gồm ba phần như sau:

### Nhiệm vụ 1: Xác định tính liên quan đến pháp luật
Đánh giá xem câu hỏi của người dùng có liên quan đến pháp luật không, dựa trên các yếu tố:
- Câu hỏi chứa yếu tố pháp luật.  
- Ngữ cảnh của câu hỏi liên quan đến pháp luật.  
- Câu hỏi yêu cầu kiến thức pháp luật để giải quyết.  

Trả lời:
- `"Không"` nếu không liên quan đến pháp luật.  
- `"Có"` nếu có liên quan đến pháp luật.  

### Nhiệm vụ 2: Phân loại yêu cầu bổ sung thông tin
Xác định xem câu hỏi có cần thu thập thêm thông tin pháp lý hay không, dựa trên:  
- **"Không"** nếu câu hỏi đã cung cấp đủ thông tin để trả lời, thường áp dụng với các tác vụ như:
  - Tóm tắt văn bản.  
  - Trích xuất thông tin thực tế hoặc hành động.  
  - Phân loại vấn đề.  
- **"Có"** nếu cần bổ sung thông tin, thường áp dụng với các tác vụ như:
  - Trích xuất, sửa lỗi văn bản luật.  
  - Trả lời câu hỏi về luật, tìm kiếm điều luật, dự đoán hình phạt.  
  - Giải quyết các vấn đề yêu cầu kiến thức pháp lý chi tiết.  

### Nhiệm vụ 3: Trả lời theo định dạng JSON
Câu trả lời phải tuân thủ định dạng JSON như sau:  
{format_instructions} 
**Lưu ý:** Nếu `lien_quan_luat` là `"Không"`, thì giá trị của `can_them_thong_tin` luôn là `"Không"`.  
**Không** cung cấp bất kỳ nội dung nào khác ngoài khối JSON.  

Câu hỏi: {query}  
Câu trả lời:
""",
}


agent_metadata["Agent_2"] = {
    "llm": {
      "type": "openai",
      "model": "gpt-4o-mini",
      "temperature": 0.1
    },
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
Câu hỏi: {query}""",
}


agent_metadata["Agent_5"] =  { 
    "llm": {
      "type": "ollama",
      "model": "qwen:2.5",
      "temperature": 0.7
    },
    "prompt": """Câu hỏi của người dùng: {query}
Phân tích chuyên sâu: {analysis_str}
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
       Danh sách `doc_no` của các tài liêu liên quan được trích ra và sắp xếp theo thứ tự độ liên quan giảm dần, \
        những tài liệu không liên quan cần được loại bỏ.
       (ví dụ: ["5", "1"]).

2. Khi đã đủ thông tin, xuất ra JSON tuân theo schema của RelatedLegalRules như trong {format_instructions}.

Chú ý: Chỉ xuất ra JSON hợp lệ nếu đủ thông tin. Không thêm văn bản nào ngoài JSON.
"""
}
agent_metadata["Agent_6"] =  {
    "llm": {
      "type": "ollama",
      "model": "qwen:2.5",
      "temperature": 0.7
    },
    "prompt_check_instruct": """Xác định liệu yêu cầu đầu vào có chứa hướng dẫn cụ thể về yêu cầu đầu ra hay không. Phân loại đầu vào thành hai loại:
    Có hướng dẫn cụ thể: Nếu yêu cầu đầu vào có đưa ra chỉ dẫn rõ ràng về cách trình bày hoặc định dạng kết quả. Ví dụ: chỉ ghi thời hạn bản án, liệt kê các loại thực thể, hoặc trả lời trong một định dạng cố định.
    Không có hướng dẫn cụ thể: Nếu yêu cầu đầu vào không cung cấp thông tin chi tiết về cách trình bày kết quả và chỉ yêu cầu câu trả lời chung hoặc lập luận mở.

Trả lời chỉ bằng 'Có' hoặc 'Không'.

Ví dụ:

    Câu hỏi của người dùng: Dựa trên các sự kiện, cáo buộc và điều luật sau đây của bộ luật hình sự, hãy dự đoán thời hạn của bản án. Chỉ cung cấp thời hạn của bản án.
    Trả lời: Có

    Câu hỏi của người dùng: Tôi muốn hỏi danh mục xe ưu tiên được quy định như thế nào?
    Trả lời: Không

Câu hỏi của người dùng: {query_str}
Trả lời:
""",
    "prompt": """Câu hỏi của người dùng: {query_str}

Phân tích chuyên sâu về vấn đề trong câu hỏi:
---------------
{analysis_str}
---------------

Các trích dẫn luật liên quan (không được thay đổi nguyên văn, khi trích vào câu trả lời phải giữ nguyên toàn bộ và in đậm):
---------------
{context_str}
---------------

Bạn là một luật sư tư vấn pháp luật Việt Nam dày dạn kinh nghiệm. Dựa trên các dữ liệu đã cung cấp, hãy phân tích các tình huống theo IRAC method, sau đó đưa ra câu trả lời với đầy đủ thông tin, hãy đảm bảo câu trả lời với các yêu cầu sau sau:

1. Xem xét kỹ lưỡng thông tin được cung cấp.
2. Dựa trên phân tích và trích dẫn luật, trả lời câu hỏi của người dùng một cách chính xác, rõ ràng, dễ hiểu.
3. Trong câu trả lời, khi nhắc đến nội dung luật đã cho, phải giữ nguyên từ ngữ và in đậm.
4. Cá nhân hóa nội dung tư vấn cho tình huống của người dùng, đề xuất giải pháp thực tế và gợi ý các cơ quan/tổ chức có thể hỗ trợ.
5. Dùng ngôn từ cẩn trọng, lập luận chặt chẽ, chuyên nghiệp.

Bạn hãy thực hiện lần lượt các nhiệm vụ sau: 

- Vấn đề được nhắc tới: Liên quan tới các vấn đề về pháp luật liên quan nào
- Trích dẫn luật: đưa các nội dung của các điều luật từ {context_str}, giữ nguyên từng chữ và in đậm toàn bộ trích dẫn.
- Phân tích và áp dụng: Sử dụng {analysis_str} để phân tích khía cạnh pháp lý liên quan, sau đó dựa vào các trích dẫn luật để áp dụng vào tình huống người dùng cung cấp trong {query_str}.
- Kết luận: Từ những phân tích trên và sau khi áp dụng điều luật vào tình huống của người dùng, hãy kết luận 1 cách rõ ràng( trả lời câu hỏi người dùng cần), chính xác về tình huống này theo đúng pháp luật. Sau đó, có thể cung cấp cho người dùng các thông tin về đơn vị/ tổ chức/ cá nhân có thể giúp đỡ người dùng tư vấn chi tiết và kĩ càng hơn.


Câu trả lời:
""",
  "prompt_instruct": """Câu hỏi của người dùng: {query_str}

Phân tích chuyên sâu về vấn đề trong câu hỏi:
---------------
{analysis_str}
---------------

Các trích dẫn luật liên quan (không được thay đổi nguyên văn, khi trích vào câu trả lời phải giữ nguyên toàn bộ và in đậm):
---------------
{context_str}
---------------

Bạn là một luật sư tư vấn pháp luật Việt Nam dày dạn kinh nghiệm. Dựa trên dữ liệu đã cung cấp (câu hỏi, phân tích chuyên sâu, và trích dẫn luật), hãy thực hiện \
chính xác yêu cầu câu hỏi của người dùng, không thêm bất kỳ văn bản bổ sung nào ngoài yêu cầu câu hỏi 

Câu trả lời:
"""
}

json.dump(agent_metadata, open('../config/agent.json', 'w'), indent=4, ensure_ascii=False)

