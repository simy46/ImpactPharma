from datetime import datetime
from typing import Union

class StatsManager:
    def __init__(self, model: str = "gpt-4o", token_limit: int = 450000):
        self.model = model
        self.token_limit = token_limit
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.article_count = 0
        self.total_tokens = 0

    def start(self):
        self.start_time = datetime.now()

    def add_article(self):
        self.article_count += 1

    def add_tokens(self, n: int):
        self.total_tokens += n

    def stop(self):
        self.end_time = datetime.now()
        
    
    def summary_dict(self) -> dict:
        duration_min = (
            (self.end_time - self.start_time).total_seconds() / 60
            if self.start_time and self.end_time else 0
        )
        avg_tokens = self.total_tokens / self.article_count if self.article_count else 0
        tpm = self.total_tokens / duration_min if duration_min else 0
        return {
            "articles": self.article_count,
            "duration_min": round(duration_min, 2),
            "total_tokens": self.total_tokens,
            "avg_tokens": round(avg_tokens, 2),
            "tokens_per_min": round(tpm, 2),
            "model": self.model,
            "token_limit": self.token_limit,
        }

    def summary(self, as_markdown: bool = False) -> Union[str, dict]:
        stats = self.summary_dict()
        if not as_markdown:
            return (
                f"--- STATISTICS ---\n"
                f"Articles processed     : {stats['articles']}\n"
                f"Total duration        : {stats['duration_min']} min\n"
                f"Total tokens used     : {stats['total_tokens']}\n"
                f"Average tokens/article: {stats['avg_tokens']}\n"
                f"Tokens per minute     : {stats['tokens_per_min']}\n"
                f"Model                 : {stats['model']}\n"
                f"Token limit / minute  : {stats['token_limit']}"
            )
        else:
            # Tableau Markdown
            md = [
                "| Metric                   | Value |",
                "|--------------------------|-------|",
                f"| Articles processed       | {stats['articles']} |",
                f"| Total duration (min)     | {stats['duration_min']} |",
                f"| Total tokens used        | {stats['total_tokens']} |",
                f"| Avg tokens/article       | {stats['avg_tokens']} |",
                f"| Tokens per minute        | {stats['tokens_per_min']} |",
                f"| Model                    | {stats['model']} |",
                f"| Token limit / minute     | {stats['token_limit']} |",
            ]
            return "\n".join(md)