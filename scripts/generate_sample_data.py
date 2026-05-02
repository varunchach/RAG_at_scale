#!/usr/bin/env python3
# Generate Sample Data for Demo

import json
import random
from pathlib import Path

def generate_sample_documents(num_docs=1000):
    """Generate sample documents for testing"""

    topics = [
        "machine learning", "artificial intelligence", "deep learning",
        "natural language processing", "computer vision", "reinforcement learning",
        "neural networks", "transformers", "large language models",
        "data science", "big data", "distributed computing"
    ]

    documents = []

    for i in range(num_docs):
        # Select random topics
        doc_topics = random.sample(topics, random.randint(1, 3))

        # Generate content
        content = f"This document discusses {', '.join(doc_topics)}. "
        content += "It covers various aspects including theory, implementation, and practical applications. "
        content += "The field has seen significant advancements in recent years."

        doc = {
            "id": f"doc_{i:04d}",
            "content": content,
            "topics": doc_topics,
            "length": len(content),
            "metadata": {
                "source": "generated",
                "created": "2024-01-01",
                "author": f"author_{random.randint(1, 10)}"
            }
        }

        documents.append(doc)

    return documents

def main():
    print("🎯 Generating sample data...")

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Generate documents
    documents = generate_sample_documents(1000)

    # Save to JSON
    with open(data_dir / "sample_documents.json", "w") as f:
        json.dump(documents, f, indent=2)

    # Save to CSV format for Spark
    import csv
    with open(data_dir / "sample_documents.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "content", "topics", "length", "metadata"])
        writer.writeheader()
        for doc in documents:
            writer.writerow({
                "id": doc["id"],
                "content": doc["content"],
                "topics": ",".join(doc["topics"]),
                "length": doc["length"],
                "metadata": json.dumps(doc["metadata"])
            })

    print(f"✅ Generated {len(documents)} sample documents")
    print(f"📁 Files saved to {data_dir}/")

if __name__ == "__main__":
    main()
