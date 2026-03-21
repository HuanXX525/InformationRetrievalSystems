import spacy
import sys
import subprocess

def load_spacy_model(model_name="en_core_web_sm"):
    try:
        return spacy.load(model_name)
    except OSError:
        print(f"找不到模型 {model_name}，正在尝试自动下载...")
        subprocess.run([sys.executable, "-m", "spacy", "download", model_name])
        return spacy.load(model_name)

