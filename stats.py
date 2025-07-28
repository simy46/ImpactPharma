import re
import argparse
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path("logs")
STATS_DIR = Path("stats")
MODEL_NAME = "gpt-4o"
TOKEN_PER_MIN_LIMIT = 90_000
COST_PER_1K_TOK = 0.005 

ARTICLE_PATTERN = re.compile(r"^------\s+(.+?)\s+------")
TOKEN_PATTERN = re.compile(r"\[TOKEN\] Estimated tokens for request: (\d+)")
WAIT_PATTERN = re.compile(r"\[WAIT\] Waiting ([\d.]+)s")

def list_log_files():
    return sorted(LOGS_DIR.glob("pipeline_*.log"))

def choose_log_file(files, chosen_path=None):
    if chosen_path:
        return Path(chosen_path)
    return files[-1]

def parse_log_file(filepath: Path):
    total_tokens = 0
    total_wait = 0.0
    article_count = 0

    ts_str = filepath.stem.replace("pipeline_", "")
    start_time = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
    end_time = datetime.fromtimestamp(filepath.stat().st_mtime)

    with filepath.open("r", encoding="utf-8") as f:
        for line in f:
            if ARTICLE_PATTERN.match(line):
                article_count += 1
            if m := TOKEN_PATTERN.search(line):
                total_tokens += int(m.group(1))
            if m := WAIT_PATTERN.search(line):
                total_wait += float(m.group(1))

    return {
        "articles": article_count,
        "total_tokens": total_tokens,
        "total_wait_sec": total_wait,
        "start_time": start_time,
        "end_time": end_time
    }

def compute_stats(data: dict):
    art = data["articles"]
    tok = data["total_tokens"]
    start = data["start_time"]
    end = data["end_time"]
    duration_sec = (end - start).total_seconds()
    avg_tok_per_art = tok / art if art else 0
    avg_time_per_art = duration_sec / art if art else 0
    tok_per_min = tok / (duration_sec / 60) if duration_sec else 0
    cost = (tok / 1000) * COST_PER_1K_TOK
    return {
        "total_articles": art,
        "total_tokens": tok,
        "duration_min": duration_sec / 60,
        "avg_tokens_per_article": avg_tok_per_art,
        "avg_time_per_article_min": avg_time_per_art / 60,
        "tokens_per_min": tok_per_min,
        "model": MODEL_NAME,
        "token_min_limit": TOKEN_PER_MIN_LIMIT,
        "estimated_cost": cost
    }

def format_stats(stats: dict, log_file: Path) -> str:
    return "\n".join([
        f"Log analysé             : {log_file.name}",
        f"Modèle                   : {stats['model']}",
        f"Token/min limite         : {stats['token_min_limit']:,}",
        "",
        f"Articles traités         : {stats['total_articles']}",
        f"Tokens totaux utilisés    : {stats['total_tokens']:,}",
        f"Durée totale (min)        : {stats['duration_min']:.2f}",
        f"Tokens / min             : {stats['tokens_per_min']:.2f}",
        f"Tokens / article         : {stats['avg_tokens_per_article']:.2f}",
        f"Durée / article (sec)     : {stats['avg_time_per_article_min']*60:.2f}",
        "",
        f"Coût estimé ($)          : {stats['estimated_cost']:.4f}"
    ])

def save_stats(text: str):
    STATS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = STATS_DIR / f"stats_{ts}.txt"
    out_file.write_text(text, encoding="utf-8")
    print(f"[✅] Statistiques enregistrées dans {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Génère des stats à partir d'un log.")
    parser.add_argument("--log", help="Chemin du fichier log à analyser", type=str)
    args = parser.parse_args()

    logs = list_log_files()
    if not logs:
        print("Aucun fichier log trouvé dans 'logs/'.")
        return

    log_file = choose_log_file(logs, args.log)
    data = parse_log_file(log_file)
    stats = compute_stats(data)
    out = format_stats(stats, log_file)
    print("\n" + out + "\n")
    save_stats(out)

if __name__ == "__main__":
    main()
