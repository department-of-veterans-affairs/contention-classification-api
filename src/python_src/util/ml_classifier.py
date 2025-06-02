import os
import re
import string
import onnxruntime as ort
from typing import Optional, Tuple
import boto3
from botocore.exceptions import ClientError

# constants
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
ONNX_FILENAME = 'classifier.onnx'

S3_BUCKET = 'private-bucket-name'
S3_PATHS = {
    ONNX_FILENAME: 'path/in/s3/classifier.onnx'
}

def model_exists_locally(filename: str) -> bool:
    return os.path.exists(os.path.join(MODEL_DIR, filename))


def download_model_from_s3(filename: str):
    """Downloads a single file from S3 into the model folder."""
    s3_key = S3_PATHS[filename]
    local_path = os.path.join(MODEL_DIR, filename)
    s3 = boto3.client('s3')

    try:
        print(f"Downloading {filename} from s3://{S3_BUCKET}/{s3_key}")
        s3.download_file(S3_BUCKET, s3_key, local_path)
    except ClientError as e:
        print(f"Error downloading {filename} from S3: {e}")
        raise RuntimeError(f"Model download failed for {filename}")

def ensure_models_exist():
    """Ensures models are present. Downloads missing ones from S3."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    for filename in [TFIDF_FILENAME, LOGREG_FILENAME]:
        if not model_exists_locally(filename):
            print(f"filename} not found locally. Attempting download...")
            download_model_from_s3(filename)
        else:
            print(f"{filename} found locally.")


# ensure models exist before loading
ensure_models_exist()

# Load ONNX model
ONNX_PATH = os.path.join(MODEL_DIR, ONNX_FILENAME)
session = ort.InferenceSession(ONNX_PATH, providers=["CPUExecutionProvider"])

# get input and output names
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name


# dummy clean text. will be replace by the one used on training pipeline
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(rf"[{re.escape(string.punctuation)}]", "", text) 
    text = re.sub(r"\s+", " ", text)  
    text = text.strip()
    return text

def ml_classify_text(text: str) -> Optional[int]:
    if not text:
        return None

    cleaned = clean_text(text)

    # ONNX model expects a list of strings for text input
    inputs = {input_name: np.array([cleaned])}

    try:
        result = session.run([output_name], inputs)[0]
        prediction = int(result[0])
        return prediction
    except Exception as e:
        print(f"ONNX inference failed: {e}")
        return None