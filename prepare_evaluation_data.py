import json
from pathlib import Path


def prepare_evaluation_dataset():
    """Convert local knowledge base into a lightweight evaluation set."""
    eval_dir = Path("evaluation_data")
    eval_dir.mkdir(parents=True, exist_ok=True)

    knowledge_base_path = Path("data/knowledge_base.json")
    if not knowledge_base_path.exists():
        print(f"No knowledge base found at {knowledge_base_path}")
        return

    with open(knowledge_base_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    eval_data = []
    for article in (data.get('articles') or [])[:100]:
        eval_item = {
            'question': f"Explain {article.get('title', 'this topic')}",
            'context': (article.get('content') or '')[:500],
            'expected_topics': article.get('topics', [])
        }
        eval_data.append(eval_item)

    out = eval_dir / 'custom_eval.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(eval_data, f, indent=2)
    print(f"Saved evaluation dataset: {out}")


if __name__ == "__main__":
    prepare_evaluation_dataset()


