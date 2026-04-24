import json
import csv
from src.retrieval import Retriever
from src.generation import generate_answer
from datetime import datetime

# Evaluation Question Set with Expected Answers
EVALUATION_QUESTIONS = [
    # Direct from textbook (in-scope)
    {"id": 1, "question": "What is motion?", "type": "direct", "scope": "in"},
    {"id": 2, "question": "Define force.", "type": "direct", "scope": "in"},
    {"id": 3, "question": "What is Newton's First Law?", "type": "direct", "scope": "in"},
    {"id": 4, "question": "State Newton's Second Law.", "type": "direct", "scope": "in"},
    {"id": 5, "question": "Explain Newton's Third Law.", "type": "direct", "scope": "in"},
    {"id": 6, "question": "What is the difference between distance and displacement?", "type": "direct", "scope": "in"},
    {"id": 7, "question": "Define velocity.", "type": "direct", "scope": "in"},
    {"id": 8, "question": "What is acceleration?", "type": "direct", "scope": "in"},
    {"id": 9, "question": "What is friction?", "type": "direct", "scope": "in"},
    {"id": 10, "question": "Define momentum.", "type": "direct", "scope": "in"},
    {"id": 11, "question": "What is uniform motion?", "type": "direct", "scope": "in"},
    {"id": 12, "question": "What does non-uniform motion mean?", "type": "direct", "scope": "in"},
    {"id": 13, "question": "Define pressure.", "type": "direct", "scope": "in"},
    {"id": 14, "question": "What is the SI unit of force?", "type": "direct", "scope": "in"},
    
    # Paraphrased (in-scope)
    {"id": 15, "question": "If nothing pushes on an object, does it keep moving?", "type": "paraphrased", "scope": "in"},
    {"id": 16, "question": "How does adding mass affect how fast something speeds up?", "type": "paraphrased", "scope": "in"},
    {"id": 17, "question": "When you jump, what happens to the ground?", "type": "paraphrased", "scope": "in"},
    {"id": 18, "question": "Why does a moving ball slow down?", "type": "paraphrased", "scope": "in"},
    {"id": 19, "question": "What's the difference between how fast you're going and which direction you're going?", "type": "paraphrased", "scope": "in"},
    {"id": 20, "question": "Why is it harder to move a heavy object than a light one?", "type": "paraphrased", "scope": "in"},
    
    # Application/Concept questions (in-scope)
    {"id": 21, "question": "Give an example of Newton's First Law in daily life.", "type": "application", "scope": "in"},
    {"id": 22, "question": "How do seatbelts in a car relate to Newton's First Law?", "type": "application", "scope": "in"},
    {"id": 23, "question": "Why do we need friction in shoes?", "type": "application", "scope": "in"},
    {"id": 24, "question": "What happens when a force acts on an object?", "type": "application", "scope": "in"},
    
    # Comparison questions (in-scope)
    {"id": 25, "question": "What is the difference between speed and velocity?", "type": "comparison", "scope": "in"},
    {"id": 26, "question": "How is mass different from weight?", "type": "comparison", "scope": "in"},
    
    # Out-of-scope (should be refused)
    {"id": 27, "question": "What is the capital of France?", "type": "out-of-scope", "scope": "out"},
    {"id": 28, "question": "How do I bake a cake?", "type": "out-of-scope", "scope": "out"},
    {"id": 29, "question": "Who wrote the Mona Lisa?", "type": "out-of-scope", "scope": "out"},
    {"id": 30, "question": "What is photosynthesis?", "type": "out-of-scope", "scope": "out"},
]

def evaluate_system():
    """End-to-end evaluation of retrieval + generation."""
    retriever = Retriever()
    results = []
    
    print("\n" + "="*70)
    print("COMPREHENSIVE EVALUATION - RETRIEVAL + ANSWER GENERATION")
    print("="*70)
    
    for q_item in EVALUATION_QUESTIONS:
        print(f"\n[Q{q_item['id']}] {q_item['question']}")
        
        try:
            # Step 1: Retrieve relevant chunks
            retrieved = retriever.retrieve(q_item["question"], top_k=2)
            
            # Step 2: Generate answer using API
            result_obj = generate_answer(q_item["question"], retriever)
            answer = result_obj.get("answer", "No answer")
            retrieved_chunks = result_obj.get("retrieved_chunks", [])
            
            # Step 3: Evaluate quality
            is_concise = len(answer.split()) <= 100  # Good answers are concise
            has_answer = len(answer) > 20 and "not available" not in answer.lower()
            is_grounded = len(retrieved_chunks) > 0
            
            # Check for appropriate refusal on out-of-scope
            is_appropriate = True
            if q_item["scope"] == "out":
                is_appropriate = "not available" in answer.lower() or "ncert" in answer.lower()
            elif q_item["scope"] == "in":
                is_appropriate = has_answer
            
            result = {
                "id": q_item["id"],
                "question": q_item["question"],
                "type": q_item["type"],
                "scope": q_item["scope"],
                "answer_length": len(answer.split()),
                "is_concise": "yes" if is_concise else "no",
                "is_grounded": "yes" if is_grounded else "no",
                "is_appropriate": "yes" if is_appropriate else "no",
                "answer": answer[:200],  # Truncate for CSV
                "chunks_retrieved": len(retrieved_chunks)
            }
            results.append(result)
            
            # Print summary
            status = "[OK]" if is_appropriate else "[FAIL]"
            print(f"{status} Answer Length: {result['answer_length']} words | Grounded: {is_grounded} | Concise: {is_concise}")
            print(f"   Answer: {answer[:120]}...")
            
        except Exception as e:
            print(f"[ERROR] Error: {str(e)}")
            result = {
                "id": q_item["id"],
                "question": q_item["question"],
                "type": q_item["type"],
                "scope": q_item["scope"],
                "answer_length": 0,
                "is_concise": "error",
                "is_grounded": "error",
                "is_appropriate": "error",
                "answer": f"ERROR: {str(e)}",
                "chunks_retrieved": 0
            }
            results.append(result)
    
    return results

def save_evaluation_results(results, filename="evaluation_results.md"):
    """Save evaluation results as Markdown."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Evaluation Results - End-to-End System\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Questions**: {len(results)}\n")
        f.write(f"**Evaluation Type**: Complete Pipeline (Retrieval + Answer Generation)\n\n")
        
        # Summary statistics
        in_scope = [r for r in results if r['scope'] == 'in']
        out_scope = [r for r in results if r['scope'] == 'out']
        appropriate = [r for r in results if r['is_appropriate'] == 'yes']
        grounded = [r for r in results if r['is_grounded'] == 'yes']
        concise = [r for r in results if r['is_concise'] == 'yes']
        
        f.write("## Summary Statistics\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total Questions | {len(results)} |\n")
        f.write(f"| In-Scope Questions | {len(in_scope)} |\n")
        f.write(f"| Out-of-Scope Questions | {len(out_scope)} |\n")
        f.write(f"| Appropriate Responses | {len(appropriate)}/{len(results)} ({100*len(appropriate)//len(results)}%) |\n")
        f.write(f"| Well-Grounded Answers | {len(grounded)}/{len(results)} ({100*len(grounded)//len(results)}%) |\n")
        f.write(f"| Concise Answers | {len(concise)}/{len(results)} ({100*len(concise)//len(results)}%) |\n")
        f.write(f"| Average Answer Length | {sum(r['answer_length'] for r in results)//len(results)} words |\n\n")
        
        # Detailed results
        f.write("## Detailed Results\n\n")
        for result in results:
            f.write(f"### Q{result['id']}: {result['question']}\n\n")
            f.write(f"| Property | Value |\n")
            f.write(f"|----------|-------|\n")
            f.write(f"| Type | {result['type']} |\n")
            f.write(f"| Scope | {result['scope']} |\n")
            f.write(f"| Appropriate | {result['is_appropriate']} |\n")
            f.write(f"| Grounded | {result['is_grounded']} |\n")
            f.write(f"| Concise | {result['is_concise']} |\n")
            f.write(f"| Answer Length | {result['answer_length']} words |\n")
            f.write(f"| Chunks Retrieved | {result['chunks_retrieved']} |\n\n")
            
            f.write(f"**Generated Answer**:\n\n> {result['answer']}\n\n")
            f.write("---\n\n")
    
    print(f"\n[SAVE] Results saved to {filename}")

def save_evaluation_csv(results, filename="evaluation_results.csv"):
    """Save evaluation results as CSV."""
    keys = ["id", "question", "type", "scope", "is_appropriate", "is_grounded", "is_concise", "answer_length", "chunks_retrieved"]
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for result in results:
            row = {k: result.get(k, "") for k in keys}
            writer.writerow(row)
    print(f"[SAVE] Results saved to {filename}")

if __name__ == "__main__":
    print("Starting Comprehensive System Evaluation...")
    results = evaluate_system()
    save_evaluation_csv(results)
    save_evaluation_results(results)
