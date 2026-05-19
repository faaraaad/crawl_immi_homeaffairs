class WebDriverException(Exception):
    """Base exception for crawler web driver errors."""
    pass


class TimeoutException(WebDriverException):
    """Exception raised when a page load or element wait times out."""
    pass


class NoSuchElementException(WebDriverException):
    """Exception raised when a expected element is not found on the page."""
    pass
