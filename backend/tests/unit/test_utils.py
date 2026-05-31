import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from utils import engagement_rate, safe_int, safe_str, safe_list_str, normalize_yt_dlp_metadata


class TestEngagementRate:
    """Tests for the engagement_rate calculation function."""

    def test_normal_case(self):
        """Test normal case with 800 likes, 200 comments, 10000 views: (1000 / 10000) *100 =10.0%"""
        result = engagement_rate(views=10000, likes=800, comments=200)
        assert isinstance(result, float)
        assert result == 10.0

    def test_zero_views(self):
        """Test zero views prevents division by zero and returns 0.0."""
        result = engagement_rate(views=0, likes=100, comments=50)
        assert isinstance(result, float)
        assert result == 0.0

    def test_zero_likes_comments(self):
        """Test when both likes and comments are zero, returns 0.0."""
        result = engagement_rate(views=1000, likes=0, comments=0)
        assert isinstance(result, float)
        assert result == 0.0

    def test_large_numbers(self):
        """Test large numbers (10M views, 500K likes, 50K comments) calculate correctly."""
        views = 10_000_000
        likes = 500_000
        comments = 50_000
        total = likes + comments
        expected = round((total / views) * 100, 4)
        result = engagement_rate(views=views, likes=likes, comments=comments)
        assert isinstance(result, float)
        assert result == expected

    def test_all_zeros(self):
        """Test all zeros (views, likes, comments) returns 0.0."""
        result = engagement_rate(views=0, likes=0, comments=0)
        assert isinstance(result, float)
        assert result == 0.0

    def test_return_type_float(self):
        """Test return type is always float, even when it's an integer value."""
        result1 = engagement_rate(views=100, likes=10, comments=0)
        result2 = engagement_rate(views=0, likes=0, comments=0)
        assert isinstance(result1, float)
        assert isinstance(result2, float)

    def test_rounded_to_4_decimals(self):
        """Test result is always rounded to 4 decimal places."""
        # 123/9876 = ~0.012454, times 100 = 1.2454 → rounded to 4 decimals is 1.2454
        result = engagement_rate(views=9876, likes=123, comments=0)
        assert round(result, 4) == result


class TestSafeInt:
    """Tests for safe_int conversion function."""

    def test_safe_int_int_input(self):
        assert safe_int(123) == 123

    def test_safe_int_float_input(self):
        assert safe_int(123.99) == 123

    def test_safe_int_none_input(self):
        assert safe_int(None) == 0
        assert safe_int(None, default=5) == 5

    def test_safe_int_bool_input(self):
        assert safe_int(True) == 1
        assert safe_int(False) == 0

    def test_safe_int_str_input(self):
        assert safe_int("123") == 123
        assert safe_int("123.45") == 123
        assert safe_int("invalid") == 0


class TestSafeStr:
    """Tests for safe_str conversion function."""

    def test_safe_str_str_input(self):
        assert safe_str("hello") == "hello"
        assert safe_str("   hello   ") == "hello"

    def test_safe_str_none_input(self):
        assert safe_str(None) == ""
        assert safe_str(None, default="default") == "default"

    def test_safe_str_empty_input(self):
        assert safe_str("") == ""


class TestSafeListStr:
    """Tests for safe_list_str conversion function."""

    def test_safe_list_str_list_input(self):
        assert safe_list_str(["tag1", "tag2"]) == ["tag1", "tag2"]
        assert safe_list_str(["tag1", "", "tag2"]) == ["tag1", "tag2"]

    def test_safe_list_str_none_input(self):
        assert safe_list_str(None) == []

    def test_safe_list_str_str_input(self):
        assert safe_list_str("tag1, tag2 tag3") == ["tag1", "tag2", "tag3"]


class TestNormalizeYtDlpMetadata:
    """Tests for normalize_yt_dlp_metadata function."""

    def test_normalize_complete_metadata(self):
        raw = {
            "title": "Test Video",
            "uploader": "Test Creator",
            "view_count": 1000,
            "like_count": 100,
            "comment_count": 50,
            "upload_date": "20240101",
            "duration": 120,
            "thumbnail": "https://example.com/thumb.jpg",
            "channel_follower_count": 10000,
            "tags": ["tag1", "tag2"],
        }
        normalized = normalize_yt_dlp_metadata(raw)
        assert normalized["title"] == "Test Video"
        assert normalized["creator"] == "Test Creator"
        assert normalized["views"] == 1000
        assert normalized["likes"] == 100
        assert normalized["comments"] == 50
        assert normalized["hashtags"] == ["tag1", "tag2"]
