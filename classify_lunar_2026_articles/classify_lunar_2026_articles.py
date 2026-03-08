from openai import OpenAI
import os
from collections import Counter, defaultdict
import time
from pathlib import Path
from datetime import datetime

# Initialize OpenAI client
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# Batch size
BATCH_SIZE = 5

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


def classify_batch(batch):
    """
    Classify a batch of articles using GPT
    
    Args:
        batch: list of (article_id, text)
    Returns:
        dict {article_id: label}
    """
    system_prompt = """You are a news article classification assistant.
Please classify each article according to the following rules, output only the article ID and corresponding category number in the format "ID: Category".

Classification rules:
1 - Lunar New Year and Cultural Celebration: Articles directly discussing Lunar New Year celebrations, traditions, customs, and festival-related content
2 - Politics and Policy: Articles about government policies, political figures, diplomatic relations, and political events
3 - Conflict and Security: Articles about wars, terrorism, military conflicts, and major criminal incidents
4 - Economy and Business: Articles about economic policies, business activities, financial markets, and corporate-related content
5 - Other/Unrelated: Articles unrelated to the above categories, or articles that are too short or missing content

Only return classification results, no explanations."""

    # Build user prompt
    user_prompt = "The following are multiple articles, please output classifications according to the rules:\n\n"
    for article_id, text in batch:
        snippet = text[:500]  # Avoid too long
        user_prompt += f"{article_id}: {snippet}\n"

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
                    aid, label = line.split(":", 1)
                    results[aid.strip()] = label.strip()
                except:
                    continue
        return results
    except Exception as e:
        print(f"API error: {e}")
        return {}


def classify_batch_with_majority(batch, trials=3):
    """
    Classify a batch with majority voting
    
    Args:
        batch: list of (article_id, text)
        trials: number of classification attempts
    Returns:
        dict {article_id: (final_label, [trial_results])}
    """
    all_results = []
    for _ in range(trials):
        res = classify_batch(batch)
        all_results.append(res)
        time.sleep(0.5)

    results_dict = {}
    for article_id, _ in batch:
        votes = [res.get(article_id, "error") for res in all_results]
        counter = Counter(votes)
        most_common = counter.most_common()
        if len(most_common) == 1:
            results_dict[article_id] = (most_common[0][0], votes)
        elif most_common[0][1] > most_common[1][1]:
            results_dict[article_id] = (most_common[0][0], votes)
        else:
            results_dict[article_id] = ("需要人工判斷", votes)
    return results_dict


def load_relevant_article_ids(relevant_file: str) -> set:
    """
    Load relevant article IDs from file
    
    Args:
        relevant_file: Path to relevant_articles.txt
        
    Returns:
        Set of relevant article IDs
    """
    relevant_ids = set()
    if os.path.exists(relevant_file):
        try:
            with open(relevant_file, "r", encoding="utf-8") as f:
                for line in f:
                    article_id = line.strip()
                    if article_id:
                        relevant_ids.add(article_id)
        except Exception as e:
            print(f"Error reading relevant articles file: {e}")
    else:
        print(f"Warning: Relevant articles file not found: {relevant_file}")
        print("Will process all articles.")
    return relevant_ids


def collect_articles(article_dir: str, relevant_ids: set = None) -> list:
    """
    Collect article files from the article directory
    
    Args:
        article_dir: Base directory containing article subdirectories
        relevant_ids: Set of relevant article IDs to filter (if None, process all)
        
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
            # If relevant_ids is provided, only include articles in the set
            if relevant_ids is None or article_id in relevant_ids:
                articles.append((str(txt_file), article_id, content))
        else:
            print(f"Warning: Failed to extract content from {txt_file}")
    
    return articles


# Main execution
if __name__ == "__main__":
    # Determine paths (relative to script location or absolute)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    if os.path.isabs(ARTICLE_DIR):
        article_dir = ARTICLE_DIR
    else:
        article_dir = os.path.join(project_root, ARTICLE_DIR)
    
    # Load relevant article IDs
    relevant_file = os.path.join(script_dir, "relevant_articles.txt")
    print("Loading relevant article IDs...")
    relevant_ids = load_relevant_article_ids(relevant_file)
    
    if relevant_ids:
        print(f"Found {len(relevant_ids)} relevant articles to process")
    else:
        print("No relevant articles file found. Processing all articles.")
    
    # Collect articles (only relevant ones if filter file exists)
    print("Collecting articles...")
    all_articles = collect_articles(article_dir, relevant_ids if relevant_ids else None)
    
    if not all_articles:
        print("No articles found!")
        exit(1)
    
    print(f"Found {len(all_articles)} articles to classify")
    print(f"Starting classification...\n")
    
    # Sort articles by article_id for consistent processing
    all_articles.sort(key=lambda x: x[1])
    
    classified_groups = defaultdict(list)
    disputed_cases = []
    
    total_articles = len(all_articles)
    processed = 0
    
    # Process in batches
    for i in range(0, total_articles, BATCH_SIZE):
        batch_articles = all_articles[i:i+BATCH_SIZE]
        batch_data = []
        for filepath, article_id, content in batch_articles:
            batch_data.append((article_id, content))
        
        batch_results = classify_batch_with_majority(batch_data)
        
        for article_id, (label, votes) in batch_results.items():
            if label == "需要人工判斷":
                # Find corresponding article text
                article_text = ""
                for aid, text in batch_data:
                    if aid == article_id:
                        article_text = text[:50]
                        break
                disputed_cases.append({"id": article_id, "results": votes, "text": article_text})
            else:
                classified_groups[label].append(article_id)
        
        processed += len(batch_data)
        if processed % 10 == 0 or processed == total_articles:
            percent = processed / total_articles * 100
            print(f"Progress: {processed}/{total_articles} ({percent:.2f}%)")
    
    # Output classification results
    output_dir = os.path.dirname(os.path.abspath(__file__))
    classified_file = os.path.join(output_dir, "classified_articles.txt")
    disputed_file = os.path.join(output_dir, "disputed_articles.txt")
    stats_file = os.path.join(output_dir, "classification_statistics.txt")
    
    with open(classified_file, "w", encoding="utf-8") as f:
        for label in sorted(classified_groups.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            ids = " ".join(classified_groups[label])
            f.write(f"{label} {ids}\n")
    
    # Output disputed cases
    with open(disputed_file, "w", encoding="utf-8") as f:
        for case in disputed_cases:
            f.write(f"ID: {case['id']} | Results: {case['results']} | First 50 chars: {case['text']}\n")
    
    # Statistics
    total = sum(len(v) for v in classified_groups.values())
    
    category_names = {
        "1": "Lunar New Year and Cultural Celebration",
        "2": "Politics and Policy",
        "3": "Conflict and Security",
        "4": "Economy and Business",
        "5": "Other/Unrelated"
    }
    
    # Output statistics to file
    with open(stats_file, "w", encoding="utf-8") as f:
        f.write("Classification Statistics\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total articles classified: {total}\n")
        f.write(f"Requires manual review: {len(disputed_cases)}\n")
        f.write(f"Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\nCategory Breakdown:\n")
        f.write("-" * 60 + "\n")
        
        for label in sorted(classified_groups.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            count = len(classified_groups[label])
            ratio = count / total * 100 if total > 0 else 0
            category_name = category_names.get(label, "Unknown")
            f.write(f"Category {label} ({category_name}): {count} articles ({ratio:.2f}%)\n")
    
    # Print statistics to console
    print("\n" + "=" * 60)
    print("Classification Statistics:")
    print("=" * 60)
    
    for label in sorted(classified_groups.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        count = len(classified_groups[label])
        ratio = count / total * 100 if total > 0 else 0
        category_name = category_names.get(label, "Unknown")
        print(f"Category {label} ({category_name}): {count} articles ({ratio:.2f}%)")
    
    print(f"\nRequires manual review: {len(disputed_cases)} articles, saved to disputed_articles.txt")
    print(f"Classification complete, results saved to classified_articles.txt")
    print(f"Statistics saved to classification_statistics.txt")
    print("=" * 60)
