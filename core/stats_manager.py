from datetime import datetime
from constants.params import COST_PER_TOKEN, MODEL, MAX_TOKENS, MAX_TOKENS_FR, REASONING, REASONING_FR, TEXT, TEXT_FR, SAFETY_MARGIN, TOKENS_PER_MINUTE


class StatsManager:
    def __init__(self, model: str = MODEL, token_limit: int = TOKENS_PER_MINUTE):
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

    def summary(self) -> str:

        stats = self.summary_dict()
        n_articles = stats['articles']

        duration_total_sec = stats['duration_min'] * 60
        minutes = int(duration_total_sec // 60)
        seconds = int(duration_total_sec % 60)
        duration_readable = f"{minutes} min {seconds} s"

        articles_per_minute = round(n_articles / stats['duration_min'], 2) if stats['duration_min'] else 0
        tokens_article_per_minute = round(stats['avg_tokens'] / stats['duration_min'], 2) if stats['duration_min'] else 0

        est_total_cost = self.total_tokens * COST_PER_TOKEN
        est_cost_per_article = est_total_cost / n_articles if n_articles else 0

        report = (
            f"--- STATISTICS ---\n"
            f"Articles processed     : {n_articles}\n"
            f"Total duration        : {stats['duration_min']} min ({duration_readable})\n"
            f"Articles/minute       : {articles_per_minute}\n"
            f"\n"
            f"Total tokens used     : {stats['total_tokens']}\n"
            f"Average tokens/article: {stats['avg_tokens']}\n"
            f"Tokens per minute     : {stats['tokens_per_min']}\n"
            f"Tokens/article/minute : {tokens_article_per_minute}\n"
            f"\n"
            f"Model                 : {stats['model']}\n"
            f"Token limit / minute  : {stats['token_limit']}\n"
            f"\n"
            f"Estimated total cost  : ${est_total_cost:.2f}\n"
            f"Estimated cost/article: ${est_cost_per_article:.2f}\n"
            f"Total cost            : \n"
            f"Cost per article      : \n"
            f"Cost/article/lang     : "
        )

        model_info = f"""
    # ========================================
    #         Model Configuration Summary     |
    # ========================================
    MODEL            = "{MODEL}"   # main model used for reasoning and quality
    MAX_TOKENS       = {MAX_TOKENS}   # max output tokens per request (EN)
    MAX_TOKENS_FR    = {MAX_TOKENS_FR}   # max output tokens per request (FR)
    REASONING        = "{REASONING.get('effort', 'unknown')}"   # reasoning level for GPT-5 (speed vs depth)
    REASONING_FR     = "{REASONING_FR.get('effort', 'unknown')}"   # reasoning level for French outputs
    TEXT             = "{TEXT.get('verbosity', 'unknown')}"   # verbosity of English responses
    TEXT_FR          = "{TEXT_FR.get('verbosity', 'unknown')}"   # verbosity of French responses
    SAFETY_MARGIN    = {SAFETY_MARGIN}   # use only 95% of token quota for safety
    """

        return f"{report}\n\n{model_info.strip()}"
