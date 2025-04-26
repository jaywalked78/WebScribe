#!/usr/bin/env python3

import requests
import sys
from bs4 import BeautifulSoup

def test_fetch_url(url):
    print(f"Testing URL: {url}")
    try:
        headers = {
            "User-Agent": "ScientificHTMLParser/1.0 (Testing)"
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        content = resp.content
        print(f"Content received: {len(content)} bytes")
        
        html = content.decode(resp.apparent_encoding or "utf-8", errors="replace")
        print(f"HTML decoded length: {len(html)} characters")
        
        soup = BeautifulSoup(html, "html5lib")
        title = soup.find("title")
        title_text = title.text if title else "No title found"
        print(f"Title: {title_text}")
        
        # Try to find the main article content
        article = soup.find("article")
        if article:
            print(f"Found <article> element with {len(article.text)} chars")
        else:
            print("No <article> element found, searching for largest content block...")
            largest = max(
                soup.find_all(["div", "section"], recursive=True),
                key=lambda t: len(t.get_text(strip=True)),
                default=None
            )
            if largest:
                print(f"Found largest content block ({largest.name}) with {len(largest.text)} chars")
            else:
                print("No content blocks found")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./test_url.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    success = test_fetch_url(url)
    sys.exit(0 if success else 1) 