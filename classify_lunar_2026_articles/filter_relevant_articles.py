from openai import OpenAI
import os
import time
from pathlib import Path
from datetime import datetime

# Initialize OpenAI client
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# Batch size
BATCH_SIZE = 10

# Article directory
ARTICLE_DIR = "lunar_2026_articles"


def extract_content_from_article(filepath: str) -> tuple:
    """
    Extract article_id and content from structured article file
    
    Args:
        filepath: Path to article file
        
    Returns:
        Tuple of (article_id, content) or (None, None) if extraction fails
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        article_id = None
        content_started = False
        content_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Extract article_id
            if line.startswith("article_id:"):
                article_id = line.split(":", 1)[1].strip()
            
            # Start collecting content after "content:" line
            if line == "content:":
                content_started = True
                continue
            
            # Collect content lines
            if content_started:
                content_lines.append(line)
        
        if article_id and content_lines:
            content = "\n".join(content_lines).strip()
            return (article_id, content)
        
        return (None, None)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return (None, None)


def check_relevance_batch(batch):
    """
    Check if articles in batch are relevant to Lunar New Year
    
    Args:
        batch: list of (article_id, text)
    Returns:
        dict {article_id: "yes" or "no"}
    """
    system_prompt = """You are an article relevance checker.
Please determine if each article is related to Lunar New Year (Chinese New Year, Spring Festival).
An article is relevant if it discusses:
- New Year customs and traditions (e.g., pasting spring couplets, setting off firecrackers, giving red envelopes)
- New Year's Eve dinner, reunion dinner
- Returning to parents' home, visiting relatives
- Lunar New Year celebrations and activities
- Traditional festival customs
- Spring Festival related cultural activities

Output only "yes" or "no" for each article ID in the format "ID: yes" or "ID: no".
Only return the results, no explanations."""

    # Build user prompt
    user_prompt = "The following are multiple articles, please determine if each is related to Lunar New Year:\n\n"
    for article_id, text in batch:
        snippet = text[:800]  # Use more content for better judgment
        user_prompt += f"{article_id}: {snippet}\n\n"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        output = response.choices[0].message.content.strip()
        results = {}
        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                try:
                    aid, relevance = line.split(":", 1)
                    aid = aid.strip()
                    relevance = relevance.strip().lower()
                    # Normalize to yes/no
                    if relevance in ["yes", "y", "相關", "是"]:
                        results[aid] = "yes"
                    else:
                        results[aid] = "no"
                except:
                    continue
        return results
    except Exception as e:
        print(f"API error: {e}")
        return {}


def collect_articles(article_dir: str) -> list:
    """
    Collect all article files from the article directory
    
    Args:
        article_dir: Base directory containing article subdirectories
        
    Returns:
        List of tuples (filepath, article_id, content)
    """
    articles = []
    article_path = Path(article_dir)
    
    if not article_path.exists():
        print(f"Error: Article directory {article_dir} does not exist")
        return articles
    
    # Find all .txt files in subdirectories
    for txt_file in article_path.rglob("*.txt"):
        article_id, content = extract_content_from_article(str(txt_file))
        if article_id and content:
            articles.append((str(txt_file), article_id, content))
    
    return articles


# Main execution
if __name__ == "__main__":
    start_time = time.time()
    
    # Determine article directory (relative to script location or absolute)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    if os.path.isabs(ARTICLE_DIR):
        article_dir = ARTICLE_DIR
    else:
        article_dir = os.path.join(project_root, ARTICLE_DIR)
    
    # Collect all articles
    print("Collecting articles...")
    all_articles = collect_articles(article_dir)
    
    if not all_articles:
        print("No articles found!")
        exit(1)
    
    print(f"Found {len(all_articles)} articles")
    print(f"Starting relevance filtering...\n")
    
    # Sort articles by article_id for consistent processing
    all_articles.sort(key=lambda x: x[1])
    
    relevant_article_ids = []
    irrelevant_count = 0
    error_count = 0
    
    total_articles = len(all_articles)
    processed = 0
    
    # Process in batches
    for i in range(0, total_articles, BATCH_SIZE):
        batch_articles = all_articles[i:i+BATCH_SIZE]
        batch_data = []
        for filepath, article_id, content in batch_articles:
            batch_data.append((article_id, content))
        
        batch_results = check_relevance_batch(batch_data)
        
        for article_id, content in batch_data:
            result = batch_results.get(article_id, "no")
            if result == "yes":
                relevant_article_ids.append(article_id)
            else:
                irrelevant_count += 1
        
        processed += len(batch_data)
        if processed % 20 == 0 or processed == total_articles:
            percent = processed / total_articles * 100
            print(f"Progress: {processed}/{total_articles} ({percent:.2f}%)")
        
        # Delay between batches to avoid rate limiting
        if i + BATCH_SIZE < total_articles:
            time.sleep(0.5)
    
    # Calculate statistics
    relevant_count = len(relevant_article_ids)
    total_processed = relevant_count + irrelevant_count
    relevance_ratio = (relevant_count / total_processed * 100) if total_processed > 0 else 0
    elapsed_time = time.time() - start_time
    
    # Output relevant articles
    output_dir = os.path.dirname(os.path.abspath(__file__))
    relevant_file = os.path.join(output_dir, "relevant_articles.txt")
    stats_file = os.path.join(output_dir, "filter_statistics.txt")
    
    with open(relevant_file, "w", encoding="utf-8") as f:
        for article_id in relevant_article_ids:
            f.write(f"{article_id}\n")
    
    # Output statistics
    with open(stats_file, "w", encoding="utf-8") as f:
        f.write(f"Filter Statistics\n")
        f.write(f"{'='*60}\n")
        f.write(f"Total articles: {total_articles}\n")
        f.write(f"Relevant articles: {relevant_count}\n")
        f.write(f"Irrelevant articles: {irrelevant_count}\n")
        f.write(f"Relevance ratio: {relevance_ratio:.2f}%\n")
        f.write(f"Processing time: {elapsed_time:.2f} seconds\n")
        f.write(f"Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Filtering Summary:")
    print("=" * 60)
    print(f"Total articles: {total_articles}")
    print(f"Relevant articles: {relevant_count}")
    print(f"Irrelevant articles: {irrelevant_count}")
    print(f"Relevance ratio: {relevance_ratio:.2f}%")
    print(f"Processing time: {elapsed_time:.2f} seconds")
    print(f"\nRelevant article IDs saved to: relevant_articles.txt")
    print(f"Statistics saved to: filter_statistics.txt")
    print("=" * 60)
