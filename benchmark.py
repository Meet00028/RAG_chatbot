#!/usr/bin/env python3

import os
import sys
import time
import uuid
from typing import Dict, List

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from dotenv import load_dotenv
load_dotenv()

# Import our modules
import ingest
import retriever
from openai import OpenAI


CANONICAL_QUERIES = [
    "What is the engagement rate of each video?",
    "Why did Video A get more engagement than Video B?",
    "Compare the hooks in the first 5 seconds.",
    "Who is the creator of Video B and what is their follower count?",
    "Suggest improvements for B based on what worked in A.",
]


def evaluate_response_quality(response: str, query: str) -> Dict[str, float]:
    """Evaluate response quality using GPT-4o-mini as a judge."""
    client = OpenAI()
    prompt = f"""
You are a judge evaluating the quality of a RAG chatbot response.

Query: {query}
Response: {response}

Please score the response on 5 metrics, each from 1-5:
1. Factual Accuracy (no hallucinations)
2. Citation Presence (includes [Video X | Chunk N])
3. Specificity (uses concrete numbers and details)
4. Actionability (suggestions are concrete)
5. Conciseness (no padding or repetition)

Only return a JSON object with the 5 scores and no other text.
Example:
{{
    "factual_accuracy": 4,
    "citation_presence": 5,
    "specificity": 3,
    "actionability": 4,
    "conciseness": 5
}}
"""
    try:
        judge_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        import json
        return json.loads(judge_response.choices[0].message.content)
    except Exception as e:
        print(f"Error evaluating response: {e}")
        return {k: 0 for k in ["factual_accuracy", "citation_presence", "specificity", "actionability", "conciseness"]}


def main():
    print("=== RAG Video Comparator Benchmark ===\n")

    # Step 1: Ingest videos and track embedding cost
    print("Step 1: Ingesting videos...")
    start_ingest = time.time()
    
    # Use sample videos
    test_video_a = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    test_video_b = "https://www.youtube.com/watch?v=9bZkp7q19f0"
    
    try:
        metadata = ingest.ingest_videos(test_video_a, test_video_b)
        ingest_time = time.time() - start_ingest
        print(f"✅ Ingestion complete in {ingest_time:.2f}s")
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        return

    session_id = str(uuid.uuid4())
    import main
    main.SESSION_METADATA[session_id] = metadata

    # Step 2: Run all canonical queries and evaluate quality
    print("\nStep 2: Running canonical queries...")
    all_scores: List[Dict[str, float]] = []
    total_input_tokens = 0
    total_output_tokens = 0

    import graph
    for i, query in enumerate(CANONICAL_QUERIES):
        print(f"  Query {i+1}/{len(CANONICAL_QUERIES)}: {query}")
        try:
            full_response = ""
            async def get_response():
                nonlocal full_response
                async for token in graph.run_graph_streaming(
                    query=query,
                    session_id=session_id,
                    video_metadata=metadata
                ):
                    full_response += token
            
            import asyncio
            asyncio.run(get_response())

            print(f"    Response length: {len(full_response)} chars")
            
            # Evaluate quality
            scores = evaluate_response_quality(full_response, query)
            all_scores.append(scores)
            print(f"    Scores: {scores}")

        except Exception as e:
            print(f"    ❌ Query failed: {e}")

    # Step 3: Calculate overall quality
    print("\nStep 3: Calculating overall quality...")
    if all_scores:
        avg_scores = {}
        for key in all_scores[0].keys():
            avg_scores[key] = sum(s[key] for s in all_scores) / len(all_scores)
        overall_avg = sum(avg_scores.values()) / len(avg_scores)
        print(f"✅ Average quality score: {overall_avg:.1f}/5")
        print(f"   Breakdown: {avg_scores}")

    # Step 4: Print cost analysis
    print("\n=== Cost Analysis ===")
    print("Note: This is a simplified estimate. For exact costs, use OpenAI's usage dashboard.")
    # Text-embedding-3-small: $0.02 per 1M tokens
    # GPT-4o-mini: $0.15/1M input, $0.60/1M output
    print("\n=== Final Benchmark Table ===")
    print("| Metric                          | Value       |")
    print("|---------------------------------|-------------|")
    print(f"| Avg quality score               | {overall_avg:.1f}/5     |")
    print("| Cost per creator (ingest+5q)    | $0.XX       |")
    print("| Cost at 1000 creators/day       | $XX.XX      |")
    print("| Cost at 10000 creators/day      | $XXX.XX     |")
    print("| Recommended stack               | GPT-4o-mini + text-embedding-3-small |")


if __name__ == "__main__":
    main()
