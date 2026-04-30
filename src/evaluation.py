import json
import csv
from src.generation import generate_answer
from datetime import datetime

# Evaluation Question Set
EVALUATION_QUESTIONS = [
    # Direct from textbook (10-12)
    {"id": 1, "question": "What is Newton's First Law of Motion?", "type": "direct", "scope": "in"},
    {"id": 2, "question": "State Newton's Second Law of Motion mathematically.", "type": "direct", "scope": "in"},
    {"id": 3, "question": "Define the Third Law of Motion.", "type": "direct", "scope": "in"},
    {"id": 4, "question": "What is the difference between distance and displacement?", "type": "direct", "scope": "in"},
    {"id": 5, "question": "Define velocity and acceleration.", "type": "direct", "scope": "in"},
    {"id": 6, "question": "What are the three equations of motion?", "type": "direct", "scope": "in"},
    {"id": 7, "question": "Explain the concept of friction.", "type": "direct", "scope": "in"},
    {"id": 8, "question": "What is momentum?", "type": "direct", "scope": "in"},
    {"id": 9, "question": "Define weight and how it differs from mass.", "type": "direct", "scope": "in"},
    {"id": 10, "question": "What is the SI unit of force?", "type": "direct", "scope": "in"},
    {"id": 11, "question": "Explain inertia in simple terms.", "type": "direct", "scope": "in"},
    {"id": 12, "question": "What is the relationship between force and acceleration?", "type": "direct", "scope": "in"},
    
    # Paraphrased (2-3)
    {"id": 13, "question": "If no external force acts on a moving object, what happens to its motion?", "type": "paraphrased", "scope": "in"},
    {"id": 14, "question": "How does mass affect the acceleration produced by a given force?", "type": "paraphrased", "scope": "in"},
    {"id": 15, "question": "When you push against a wall, does the wall push back on you?", "type": "paraphrased", "scope": "in"},
    
    # Out-of-scope (3-5)
    {"id": 16, "question": "What is the current Prime Minister of India?", "type": "out-of-scope", "scope": "out"},
    {"id": 17, "question": "How do I bake a chocolate cake?", "type": "out-of-scope", "scope": "out"},
    {"id": 18, "question": "What is the capital of France?", "type": "out-of-scope", "scope": "out"},
    {"id": 19, "question": "Who won the FIFA World Cup in 2022?", "type": "out-of-scope", "scope": "out"},
]

def evaluate_answers():
    """Run evaluation on all questions and score responses."""
    results = []
    
    for q_item in EVALUATION_QUESTIONS:
        print(f"Evaluating Q{q_item['id']}: {q_item['question'][:50]}...")
        
        try:
            response = generate_answer(q_item["question"])
            answer = response["answer"]
            retrieved = response["retrieved"]
            
            result = {
                "id": q_item["id"],
                "question": q_item["question"],
                "type": q_item["type"],
                "scope": q_item["scope"],
                "answer": answer,
                "retrieved_metadata": json.dumps(retrieved),
                "correctness": "",  # To be filled manually
                "grounding": "",    # To be filled manually
                "refusal_appropriate": "",  # For out-of-scope only
                "notes": ""
            }
            results.append(result)
        except Exception as e:
            print(f"Error evaluating Q{q_item['id']}: {str(e)}")
            result = {
                "id": q_item["id"],
                "question": q_item["question"],
                "type": q_item["type"],
                "scope": q_item["scope"],
                "answer": f"ERROR: {str(e)}",
                "retrieved_metadata": "",
                "correctness": "error",
                "grounding": "n/a",
                "refusal_appropriate": "n/a",
                "notes": f"Error: {str(e)}"
            }
            results.append(result)
    
    return results

def save_results_csv(results, filename="evaluation_results.csv"):
    """Save evaluation results as CSV."""
    keys = results[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"Results saved to {filename}")

def save_results_markdown(results, filename="evaluation_results.md"):
    """Save evaluation results as Markdown."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Evaluation Results\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Questions**: {len(results)}\n\n")
        
        for result in results:
            f.write(f"## Q{result['id']}: {result['question']}\n\n")
            f.write(f"**Type**: {result['type']} | **Scope**: {result['scope']}\n\n")
            f.write(f"**Answer**: {result['answer']}\n\n")
            f.write(f"**Correctness**: {result['correctness']}\n\n")
            f.write(f"**Grounding**: {result['grounding']}\n\n")
            if result['scope'] == 'out':
                f.write(f"**Refusal Appropriate**: {result['refusal_appropriate']}\n\n")
            f.write(f"**Notes**: {result['notes']}\n\n")
            f.write("---\n\n")
    
    print(f"Results saved to {filename}")

def analyze_failures(results):
    """Identify working and failing examples."""
    working = []
    failing = []
    
    for result in results:
        if result['correctness'] == 'yes' and result['grounding'] == 'yes':
            working.append(result)
        elif result['correctness'] in ['no', 'partial']:
            failing.append(result)
    
    print(f"\n✓ Working Examples: {len(working)}")
    for w in working[:3]:
        print(f"  Q{w['id']}: {w['question'][:40]}...")
    
    print(f"\n✗ Failing Examples: {len(failing)}")
    for f in failing[:2]:
        print(f"  Q{f['id']}: {f['question'][:40]}...")
        print(f"    Cause: {f['notes']}")

if __name__ == "__main__":
    print("Running evaluation...")
    results = evaluate_answers()
    save_results_csv(results)
    save_results_markdown(results)
    print("Evaluation complete!")
