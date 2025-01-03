import gradio as gr
import logging
import os
from dotenv import load_dotenv


from src.pipeline import Pipeline  # Giả sử bạn có file pipeline.py chứa class Pipeline

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Khởi tạo pipeline (giá trị các tham số có thể tuỳ chỉnh theo nhu cầu thực tế)
pipeline = Pipeline(
    openai_api_key=os.environ["OPENAI_API_KEY"],
    qdrant_url="http://localhost:6333",
    qdrant_api_key=None,
    neo4j_uri="neo4j://localhost",
    neo4j_auth=("neo4j", "Abc12345"),
    config_path=os.environ["CONFIG_PATH"],
    legal_topics_path="config/list_chude_demuc.txt",
)

def run_pipeline(query):
    """
    Hàm này sẽ gọi pipeline và trả về kết quả cuối cùng.
    """
    try:
        result = pipeline.run(query=query)
        final_answer = result.get("final_answer_state", "Không tìm thấy câu trả lời.")
        intermediate_steps = result.get("intermediate_steps", [])
        # Trả về nội dung kết quả cuối cùng và bước trung gian
        return final_answer, "\n".join(intermediate_steps)
    except Exception as e:
        logging.error(f"Lỗi khi chạy pipeline: {e}")
        return "Có lỗi xảy ra trong quá trình xử lý.", ""

# Tạo giao diện Gradio
with gr.Blocks() as demo:
    gr.Markdown("# Demo Pipeline với Gradio")
    query_input = gr.Textbox(
        label="Nhập câu hỏi của bạn",
        placeholder="Ví dụ: Quy trình đăng ký kinh doanh tại Việt Nam như thế nào?",
    )
    answer_output = gr.Textbox(label="Câu trả lời cuối cùng")
    steps_output = gr.Textbox(label="Các bước trung gian")

    run_button = gr.Button("Chạy Pipeline")
    run_button.click(fn=run_pipeline, inputs=query_input, outputs=[answer_output, steps_output])

if __name__ == "__main__":
    # Chạy server Gradio
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
