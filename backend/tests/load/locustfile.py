from locust import HttpUser, task, between
import uuid


class VideoAnalysisUser(HttpUser):
    wait_time = between(1, 3)
    session_id = None
    canonical_queries = [
        "What is the engagement rate of each video?",
        "Why did Video A get more engagement than Video B?",
        "Compare the hooks in the first 5 seconds.",
        "Who is the creator of Video B and what is their follower count?",
        "Suggest improvements for B based on what worked in A.",
    ]

    def on_start(self):
        """On user start, ingest test videos to get a session ID."""
        # Note: For real load tests, use mock ingestion or pre-ingested data
        try:
            response = self.client.post(
                "/ingest",
                json={
                    "url_a": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "url_b": "https://www.youtube.com/watch?v=9bZkp7q19f0"
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
        except Exception:
            pass

    @task(1)
    def health_check(self):
        """Low weight health check task."""
        self.client.get("/health")

    @task(5)
    def stream_query(self):
        """High weight query streaming task."""
        if not self.session_id:
            return
        import random
        query = random.choice(self.canonical_queries)
        self.client.get(
            "/stream",
            params={"session_id": self.session_id, "query": query},
            stream=True
        )
