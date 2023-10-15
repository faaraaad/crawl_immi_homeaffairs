from unittest.mock import patch, MagicMock
from immi_crawler.tasks import get_page, save_occupation_visa


def test_get_page_task_successful() -> None:
    """Verify that get_page executes fully and caches progress in Redis when not already crawled."""
    with patch("immi_crawler.tasks.run_async_in_background") as mock_run, \
         patch("immi_crawler.tasks.get_occupation_and_visa") as mock_parser, \
         patch("immi_crawler.tasks.get_redis_client") as mock_redis:
         
        # Mock Redis client
        mock_redis_client = MagicMock()
        mock_redis_client.sismember.return_value = False
        mock_redis.return_value = mock_redis_client
        
        # Mock background playwright execution and BS4 parser
        mock_run.return_value = "<html>HTML source</html>"
        mock_parser.return_value = [
            {"occupation": "Software Engineer", "visa_subclass": "189", "stream": "State Nominated"}
        ]
        
        # Execute the task locally in synchronous mode
        result = get_page.apply(args=("https://example.com", 0)).get()
        
        # Assertions
        assert result == [{"occupation": "Software Engineer", "visa_subclass": "189", "stream": "State Nominated"}]
        mock_run.assert_called_once()
        mock_redis_client.sadd.assert_called_once_with("crawled_pages", "0")


def test_get_page_task_already_crawled() -> None:
    """Verify that get_page skips execution if the page has already been marked crawled in Redis."""
    with patch("immi_crawler.tasks.run_async_in_background") as mock_run, \
         patch("immi_crawler.tasks.get_redis_client") as mock_redis:
         
        mock_redis_client = MagicMock()
        mock_redis_client.sismember.return_value = True
        mock_redis.return_value = mock_redis_client
        
        result = get_page.apply(args=("https://example.com", 0)).get()
        
        # Should return an empty list and skip running playwright
        assert result == []
        mock_run.assert_not_called()
