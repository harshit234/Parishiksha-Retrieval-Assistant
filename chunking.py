import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

def create_chunks():
    text = ""
    for file in ["data/processed/motion_ch8.txt", "data/processed/force_ch9.txt"]:
        with open(file, "r", encoding="utf-8") as f:
            text += f.read() + "\n"

    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=128)
    raw_chunks = splitter.split_text(text)

    chunks = []
    for i, chunk in enumerate(raw_chunks):
        # Determine chapter
        chapter = "Motion" if "motion" in chunk.lower() else "Force and Laws of Motion"
        
        # Better type classification
        chunk_type = "concept"
        if re.search(r'definition|define|is|are', chunk, re.I):
            chunk_type = "definition"
        elif re.search(r'example|solution|instance', chunk, re.I):
            chunk_type = "example"
        elif re.search(r'law|laws|principle', chunk, re.I):
            chunk_type = "law"
        elif re.search(r'formula|equation|express|mathematically', chunk, re.I):
            chunk_type = "equation"
        elif re.search(r'type|kinds|categories|characteristic|properties', chunk, re.I):
            chunk_type = "characteristics"
        
        chunks.append({
            "id": i,
            "content": chunk,
            "metadata": {
                "chapter": chapter,
                "type": chunk_type,
                "length": len(chunk)
            }
        })
    with open("data/processed/chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"Created {len(chunks)} chunks")
    return chunks