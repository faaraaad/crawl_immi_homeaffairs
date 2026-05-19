import os
from immi_crawler.parser import get_occupation_and_visa


def test_parser_sample_html() -> None:
    # Resolve absolute path to the fixture file
    fixture_dir = os.path.dirname(os.path.abspath(__file__))
    fixture_path = os.path.join(fixture_dir, "fixtures", "sample_table.html")
    
    with open(fixture_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    results = get_occupation_and_visa(html_content)
    
    # Assertions
    # There are 2 valid tr rows, representing:
    # 1. Software Engineer (189, 190, 482 - Medium Term Stream) -> 3 entries
    # 2. Chef (482 - Short Term Stream, 491) -> 2 entries
    # Total: 5 parsed records
    assert len(results) == 5
    
    # Verify exact parsed contents
    assert results[0] == {
        "occupation": "Software Engineer",
        "visa_subclass": "189",
        "stream": "State or Territory nominated"
    }
    assert results[1] == {
        "occupation": "Software Engineer",
        "visa_subclass": "190",
        "stream": "State or Territory nominated"
    }
    assert results[2] == {
        "occupation": "Software Engineer",
        "visa_subclass": "482",
        "stream": "Medium Term Stream"
    }
    assert results[3] == {
        "occupation": "Chef",
        "visa_subclass": "482",
        "stream": "Short Term Stream"
    }
    assert results[4] == {
        "occupation": "Chef",
        "visa_subclass": "491",
        "stream": "State or Territory nominated"
    }
