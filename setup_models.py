from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    base_dir = Path("base_models")
    base_dir.mkdir(parents=True, exist_ok=True)

    models_to_download = [
        "microsoft/phi-2",  # 2.7B params
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "google/gemma-2b"
    ]

    for model_name in models_to_download:
        print(f"Downloading {model_name}...")
        model = AutoModelForCausalLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        out = base_dir / model_name.replace('/', '_')
        out.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(out)
        tokenizer.save_pretrained(out)
        print(f"Saved to {out}")


if __name__ == "__main__":
    main()


