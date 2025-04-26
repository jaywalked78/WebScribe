#!/usr/bin/env bash

URL="${1:-https://pmc.ncbi.nlm.nih.gov/articles/PMC8998800/}"
OUTPUT_FOLDER="output/md"

# Create output folder if it doesn't exist
mkdir -p "$OUTPUT_FOLDER"

echo "Using test URL: $URL"

# Create a temporary Python script
TMP_SCRIPT=$(mktemp)

cat > "$TMP_SCRIPT" << 'PYTHONSCRIPT'
import sys
import requests
import json
import re
import os
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path='.env')

def sanitize_filename(name):
    # Replace invalid filename characters with underscores
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()

def get_domain(url):
    """Extract the domain name from URL, e.g., 'pubmed.ncbi.nlm.nih.gov' -> 'PubMed'"""
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc.lower()
    
    # Extract domain from common scientific sites
    if 'pubmed' in hostname:
        return 'PubMed'
    elif 'pmc' in hostname:
        return 'PMC'
    elif 'nature.com' in hostname:
        return 'Nature'
    elif 'science' in hostname:
        return 'Science'
    elif 'sciencedirect' in hostname:
        return 'ScienceDirect'
    elif 'springer' in hostname:
        return 'Springer'
    elif 'wiley' in hostname:
        return 'Wiley'
    elif 'cell.com' in hostname:
        return 'Cell'
    elif 'acs.org' in hostname:
        return 'ACS'
    elif 'nejm.org' in hostname:
        return 'NEJM'
    elif 'bmj.com' in hostname:
        return 'BMJ'
    elif 'jamanetwork' in hostname:
        return 'JAMA'
    elif 'thelancet' in hostname:
        return 'Lancet'
    else:
        # Extract first part of hostname before first dot
        domain = hostname.split('.')[0]
        return domain.capitalize()

def send_to_webhook(webhook_url, markdown_content, source_url, filepath):
    """Send markdown content to webhook"""
    if not webhook_url:
        print("No webhook URL provided, skipping webhook")
        return False
        
    try:
        payload = {
            "content": markdown_content,
            "source_url": source_url,
            "filename": os.path.basename(filepath),
            "timestamp": datetime.now().isoformat()
        }
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Disable SSL verification for localhost
        verify_ssl = not webhook_url.startswith('http://localhost')
        
        print(f"Sending data to webhook: {webhook_url}")
        response = requests.post(webhook_url, json=payload, headers=headers, verify=verify_ssl)
        response.raise_for_status()
        
        print(f"Webhook response: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending to webhook: {e}")
        return False

def main():
    url = sys.argv[1]
    output_folder = sys.argv[2]
    
    # Get webhook URL from environment with hardcoded fallback
    webhook_url = os.environ.get('WEBHOOK_URL')
    
    # Force the webhook URL to use the one from .env file
    if not webhook_url:
        webhook_url = "http://localhost:5678/webhook-test/ef0622ad-db42-4bde-a1b1-dbb094a55314"
    
    print(f"Using webhook URL: {webhook_url}")
    
    # Extract domain for filename prefix
    domain_prefix = get_domain(url)

    # Create domain-specific subfolder
    domain_folder = os.path.join(output_folder, domain_prefix)
    os.makedirs(domain_folder, exist_ok=True)
    print(f'Using domain folder: {domain_folder}')

    print(f'Fetching {url}')

    try:
        r = requests.get(url, headers={'User-Agent': 'ScientificParser/1.0'})
        r.raise_for_status()
        html = r.text
        
        soup = BeautifulSoup(html, 'html5lib')
        
        # Find the title from meta tags or title tag
        meta_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'citation_title'})
        title_tag = soup.find('title')
        
        if meta_title and meta_title.get('content'):
            page_title = meta_title.get('content').strip()
        elif title_tag:
            page_title = title_tag.text.strip()
        else:
            page_title = 'Untitled'
        
        # Store original title for markdown
        original_title = page_title
        
        article_tag = soup.find('article')
        main_content = None
        
        if article_tag:
            main_content = article_tag
            print(f'Found <article> element with {len(article_tag.text)} chars')
        else:
            print("No <article> element found, searching for main content...")
            
            # Try to find main content containers
            for selector in ['main', '#content', '.content', '#main', '.main', '#mainContent', '.main-content']:
                main = soup.select_one(selector)
                if main and len(main.text.strip()) > 500:  # Must have substantial text
                    main_content = main
                    print(f'Found main content in {selector} with {len(main.text)} chars')
                    break
                    
            # If still not found, look for largest div or section
            if not main_content:
                candidates = soup.find_all(['div', 'section'], class_=lambda c: c and ('content' in c.lower() or 'main' in c.lower() or 'article' in c.lower()))
                if not candidates:
                    candidates = soup.find_all(['div', 'section'])
                    
                if candidates:
                    # Find the largest text container
                    main_content = max(candidates, key=lambda t: len(t.get_text(strip=True)), default=None)
                    if main_content:
                        print(f'Found largest content in {main_content.name} with {len(main_content.text)} chars')
        
        if main_content:
            # Try to find the first h1 in the article to use as filename
            h1 = main_content.find('h1')
            if h1 and h1.text.strip():
                article_title = h1.text.strip()
            else:
                # Try other heading levels
                for heading_level in range(1, 4):
                    heading = main_content.find(f'h{heading_level}')
                    if heading and heading.text.strip():
                        article_title = heading.text.strip()
                        break
                else:
                    # If no headings found, use page title
                    article_title = page_title
                    
            # Sanitize for filename use - no character limit
            file_title = sanitize_filename(article_title)
            
            # Create filename (no longer need domain prefix in filename)
            filename = f'{file_title}.md'
            filepath = os.path.join(domain_folder, filename)
            
            # Delete any existing file with the same name
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f'Removed existing file with same name')
            
            print(f'Article title: {article_title}')
            
            # Generate markdown
            md = f'# {original_title}\n\n'
            
            # Add paragraphs
            for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if p.name.startswith('h'):
                    level = int(p.name[1])
                    md += '\n' + ('#' * level) + ' ' + p.get_text().strip() + '\n\n'
                else:
                    md += p.get_text().strip() + '\n\n'
            
            # Save the file
            with open(filepath, 'w') as f:
                f.write(md)
            print(f'Saved output to {filepath}')
            
            # Send to webhook if URL is provided
            if webhook_url:
                send_to_webhook(webhook_url, md, url, filepath)
            
            # Preview
            print('\n== MARKDOWN PREVIEW ==')
            print(md[:300] + '...')
        else:
            print('No main content found in the page')
            
    except Exception as e:
        print(f'Error: {e}')
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
PYTHONSCRIPT

# Execute the Python script with our parameters
python3 "$TMP_SCRIPT" "$URL" "$OUTPUT_FOLDER"

# Clean up
rm "$TMP_SCRIPT" 