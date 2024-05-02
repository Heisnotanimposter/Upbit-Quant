import subprocess
import sys

def execute_command(command):
    """
    Execute a shell command with error handling and user feedback.
    """
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print(f"Command executed successfully: {command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}\nError message: {e.stderr}")
        sys.exit(1)

# Install necessary tools and libraries
execute_command("git clone https://github.com/ggerganov/llama.cpp")
execute_command("cd llama.cpp && git pull && make clean && LLAMA_CUBLAS=1 make")
execute_command("pip install -r llama.cpp/requirements.txt")

# Clone the model repository
execute_command("git lfs install")
execute_command(f"git clone https://huggingface.co/{MODEL_ID}")

# Convert model to fp16
MODEL_NAME = MODEL_ID.split('/')[-1]
fp16 = f"{MODEL_NAME}/{MODEL_NAME.lower()}.fp16.bin"
execute_command(f"python llama.cpp/convert.py {MODEL_NAME} --outtype f16 --outfile {fp16}")

# Quantize the model
QUANTIZATION_METHODS = QUANTIZATION_METHODS.replace(" ", "").split(",")
for method in QUANTIZATION_METHODS:
    qtype = f"{MODEL_NAME}/{MODEL_NAME.lower()}.{method.upper()}.gguf"
    execute_command(f"./llama.cpp/quantize {fp16} {qtype} {method}")

# Install Hugging Face Hub library
execute_command("pip install -q huggingface_hub")

from huggingface_hub import create_repo, HfApi
from google.colab import userdata, runtime

# Get token securely
hf_token = userdata.get(token)  # Assumes token is stored securely in Google Colab environment
api = HfApi()

# Create and upload to Hugging Face repo
try:
    create_repo(
        repo_id=f"{username}/{MODEL_NAME}-GGUF",
        repo_type="model",
        exist_ok=True,
        token=hf_token
    )
    print(f"Repository {username}/{MODEL_NAME}-GGUF created successfully.")
    
    api.upload_folder(
        folder_path=MODEL_NAME,
        repo_id=f"{username}/{MODEL_NAME}-GGUF",
        allow_patterns=["*.gguf","$.md"],
        token=hf_token
    )
    print("Files uploaded successfully.")
except Exception as e:
    print(f"Failed to create or upload to the repository. Error: {str(e)}")
    sys.exit(1)

# Terminate the runtime
runtime.unassign()
print("Runtime unassigned and cleaned up successfully.")