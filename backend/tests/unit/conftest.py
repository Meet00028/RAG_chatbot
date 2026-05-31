import pytest
import tiktoken


@pytest.fixture(scope="session")
def tiktoken_encoder():
    """Fixture providing a tiktoken encoder for cl100k_base (used for chunk size checks)."""
    return tiktoken.get_encoding("cl100k_base")


@pytest.fixture
def sample_short_transcript():
    """Fixture for a short transcript (< 300 tokens)."""
    return """
    Hey everyone, welcome back to my channel! Today we're going to talk about
    how to grow your audience on social media. First, you need to make great
    content that people actually want to watch. Then you need to be consistent
    with your posting schedule. Finally, engage with your audience in the
    comments section. Let's dive in!
    """.strip()


@pytest.fixture
def sample_long_transcript():
    """Fixture for a longer transcript (~1000 tokens) with emojis and unicode."""
    return (
        "Hey everyone! 🎉 Welcome back! " * 20
        + "Today we're going to cover: 1. Hooks 2. Content Quality 3. Consistency 4. Engagement "
        * 5
        + "Let's start with hooks! A great hook is the first 3-5 seconds of your video. "
        * 3
        + "You need to grab attention immediately! 💥"
    )
