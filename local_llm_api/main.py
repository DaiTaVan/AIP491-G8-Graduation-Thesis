# import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "1"
import uvicorn

if __name__ == "__main__":
    uvicorn.run("runner:app", host="0.0.0.0", port=9999, reload=False, timeout_keep_alive=300)
