from bs4 import BeautifulSoup


def get_occupation_and_visa(html: str) -> list[dict[str, str]]:
    """Parse the Skill Occupation List HTML table to extract occupation-visa stream pairs.
    
    Args:
        html: Raw HTML content of the page.
        
    Returns:
        A list of dictionaries containing 'occupation', 'visa_subclass', and 'stream'.
    """
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    # Target rows representing occupations in the accordion table
    trs = soup.find_all("tr", attrs={'tabindex': '-1', 'aria-expanded': 'false'})
    for tr in trs:
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue
            
        occupation = tds[0].get_text(strip=True)
        lis = tds[2].find_all("li")
        
        for li in lis:
            text = li.get_text(strip=True)
            if not text:
                continue
                
            subclass_str = text[:3]
            try:
                # Ensure the first 3 characters represent a valid integer subclass
                int(subclass_str)
                
                # Check stream classification logic
                if subclass_str == "482":
                    if "Medium Term Stream" in text:
                        stream = "Medium Term Stream"
                    else:
                        stream = "Short Term Stream"
                else:
                    stream = "State or Territory nominated"
                    
                results.append({
                    "occupation": occupation,
                    "visa_subclass": subclass_str,
                    "stream": stream
                })
            except ValueError:
                # Non-subclass list items are skipped
                pass
                
    return results
