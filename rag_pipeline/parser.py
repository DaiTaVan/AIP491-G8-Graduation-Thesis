class SentenceSplitter:
    def __init__(
            self,
            tokenizer,
            seperator: str = "\n",
            chunk_size: int = 500,
    ):
        self.tokenizer = tokenizer
        self.seperator = seperator
        self.chunk_size = chunk_size
    
    def split(self, title: str, content: str):
        title_len = self._token_size(title)
        effective_chunk_size = self.chunk_size - title_len

        content_len = self._token_size(content)
        if content_len < effective_chunk_size:
            return [f"{title}\n{content}"]
        
        list_sub_text = content.split(self.seperator)
        list_merge_text = []

        text_complete = title
        for ix, text in enumerate(list_sub_text):
            text_complete += '\n' + text
            if self._token_size(text_complete) > self.chunk_size or ix + 1 == len(list_sub_text):
                list_merge_text.append(text_complete)
                text_complete = title
    
        return list_merge_text

    
    def _token_size(self, text: str) -> int:
        return len(self.tokenizer(text)['input_ids'])

if __name__ == '__main__':
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained('/media/tavandai/DATA10/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/bge-m3')
    parser = SentenceSplitter(tokenizer = tokenizer, chunk_size=128)

    title = 'Điều 1.2.TT.1.3. Nội dung chi phục vụ nhiệm vụ chuyên môn công tác bảo vệ bí mật nhà nước'
    content = """ 1. Chi soạn thảo các văn bản quy phạm pháp luật về bảo vệ bí mật nhà nước.

    2. Chi kiểm tra, xử lý, rà soát, hệ thống hóa văn bản quy phạm pháp luật có nội dung thuộc bí mật nhà nước.

    3. Chi tuyên truyền, phổ biến, giáo dục pháp luật về bảo vệ bí mật nhà nước.

    4. Chi tập huấn, bồi dưỡng kỹ năng, nghiệp vụ về công tác bảo vệ bí mật nhà nước.

    5. Chi hội nghị, hội thảo, tọa đàm, sơ kết, tổng kết về công tác bảo vệ bí mật nhà nước.

    6. Chi mua sắm trang thiết bị, máy móc, ứng dụng công nghệ thông tin phục vụ công tác bảo vệ bí mật nhà nước, bao gồm: hòm, tủ, máy tính, biển hiệu, con dấu; phần mềm bảo mật thiết bị, đường truyền bảo mật theo quy định của Luật Cơ yếu; thiết bị lưu giữ và bảo quản tin, tài liệu mật; vật mang bí mật nhà nước; thiết bị bảo vệ và giám sát; tem kiểm tra an ninh; thiết bị tiêu hủy tài liệu, vật mang bí mật nhà nước.

    7. Chi khảo sát, vẽ sơ đồ và xây dựng Báo cáo xác định khu vực, địa điểm cấm theo quy định của Pháp lệnh Bảo vệ bí mật Nhà nước và các văn bản hướng dẫn để báo cáo cấp có thẩm quyền xem xét phê duyệt.

    8. Chi thu thập tin, tài liệu phục vụ công tác xác minh, điều tra các vụ lộ, lọt bí mật nhà nước.

    9. Chi điều tra, khảo sát thống kê số liệu trong nước liên quan đến bảo vệ bí mật nhà nước.

    10. Chi hoạt động đàm phán, ký kết và thực hiện các điều ước quốc tế, thỏa thuận quốc tế về việc cùng bảo vệ thông tin mật.

    11. Chi kiểm tra an ninh các thiết bị điện tử, phương tiện trước khi đưa vào sử dụng phục vụ công tác bảo vệ bí mật nhà nước, gồm: Thuê chuyên gia, phương tiện, thiết bị (trong trường hợp cán bộ, phương tiện, thiết bị của cơ quan an ninh không đáp ứng được yêu cầu kiểm tra thì người đứng đầu đơn vị kỹ thuật, nghiệp vụ quyết định việc thuê số lượng chuyên gia, phương tiện, thiết bị để thực hiện).

    12. Chi thực hiện giảm mật, giải mật, tiêu hủy bí mật nhà nước theo quy định, gồm:

    a) Phân loại, tập hợp lập danh mục, rà soát tài liệu, vật mang bí mật nhà nước cần giảm mật, giải mật, tiêu hủy để xây dựng Báo cáo thuyết minh tài liệu, vật mang bí mật cần tiêu hủy;

    b) Họp Hội đồng xác định giá trị tài liệu mật, xét hủy tài liệu mật phải tiêu hủy;

    c) Thuê phương tiện vận chuyển tài liệu, vật mang bí mật từ địa điểm lưu giữ đến nơi tiêu hủy; thuê thiết bị thực hiện tiêu hủy.

    13. Chi khen thưởng cho các tập thể, cá nhân có thành tích trong công tác bảo vệ bí mật nhà nước."""

    list_texts = parser.split(title, content)
    print(list_texts)