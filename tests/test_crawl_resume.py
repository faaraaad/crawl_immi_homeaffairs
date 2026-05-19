from unittest.mock import patch, MagicMock
from immi_crawler.tasks import get_page


def test_crawl_resume_logic() -> None:
    """Integration test to verify that the Redis-backed crawl resume logic accurately
    differentiates between already-completed and new/pending pages.
    """
    with patch("immi_crawler.tasks.get_redis_client") as mock_redis, \
         patch("immi_crawler.tasks.run_async_in_background") as mock_run, \
         patch("immi_crawler.tasks.get_occupation_and_visa") as mock_parser:
         
        # Configure Redis mock: Page "0" is already crawled, but Page "1" is not
        mock_redis_client = MagicMock()
        mock_redis_client.sismember.side_effect = lambda name, value: value == "0"
        mock_redis.return_value = mock_redis_client
        
        mock_run.return_value = "<html>Sample source</html>"
        mock_parser.return_value = [{"occupation": "Accountant", "visa_subclass": "189", "stream": "General"}]
        
        # 1. Try crawling Page 0 (should bypass completely)
        result_page_0 = get_page.apply(args=("https://example.com", 0)).get()
        assert result_page_0 == []
        mock_run.assert_not_called()
        
        # 2. Try crawling Page 1 (should fetch and insert)
        result_page_1 = get_page.apply(args=("https://example.com", 1)).get()
        assert len(result_page_1) == 1
        assert result_page_1[0]["occupation"] == "Accountant"
        
        # Verify that run_async_in_background was executed for page 1 and saved to Redis
        mock_run.assert_called_once()
        mock_redis_client.sadd.assert_called_once_with("crawled_pages", "1")
