from urllib.parse import urlparse, urljoin
import json
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_links_from_page(session, url, retry_count=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": urlparse(url).scheme + "://" + urlparse(url).netloc
    }
    
    for _ in range(retry_count):
        try:
            response = session.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            links = [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]
            return set(links), False
        except requests.RequestException as e:
            logging.error(f"Failed to fetch {url}, retrying... ({e})")
            time.sleep(random.uniform(0.1, 0.5))
    
    logging.error(f"Giving up on {url} after {retry_count} failed attempts.")
    return set(), True

def categorize_url(url, start_domain):
    parsed_url = urlparse(url)
    category = None
    domain = parsed_url.netloc.replace('www.', '')
    if parsed_url.scheme.lower() in ['http', 'https']:
        if domain == start_domain.replace('www.', ''):
            category = 'Internal'
        else:
            category = 'External'
    elif parsed_url.scheme.lower() in ['mailto', 'tel']:
        category = 'Special'
    elif parsed_url.scheme.lower() == 'ftp':
        category = 'FTP'
    exts = ['.jpg', '.jpeg']
    if any(url.lower().endswith(ext) for ext in exts):
        category = 'Media or Documents'
    if not category:
        category = 'Others'
    return category

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    organized_content = {}
    heading_stack = []

    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'span']):
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(element.name[1])
            heading_text = element.get_text(separator=' ', strip=True)

            heading_stack = heading_stack[:level-1] + [heading_text]
            current_heading = " - ".join(heading_stack)

            if current_heading not in organized_content:
                organized_content[current_heading] = []
        elif element.name in ['p', 'ul', 'span']:
            text = element.get_text(separator=' ', strip=True)
            if heading_stack:
                current_heading = " - ".join(heading_stack)
                organized_content[current_heading].append(text)

    return organized_content

def create_content_dict(organized_content, url):
    full_text = ""
    for heading, contents in organized_content.items():
        full_text += "start\n" + heading + "\n\n" + "\n".join(contents) + "\nend\n\n"

    return {
        "webpage_url": url,
        "text_chunk": full_text.strip()
    }

def process_internal_url(session, url, start_domain):
    try:
        if categorize_url(url, start_domain) == 'Internal':
            response = session.get(url)
            response.raise_for_status()
            organized_content = parse_html(response.content)
            content_dict = create_content_dict(organized_content, url)
            return content_dict
    except requests.RequestException as e:
        logging.error(f"Error processing URL {url}: {e}")
    return None

def main(start_url):
    start_time = time.time()
    setup_logging()
    start_domain = urlparse(start_url).netloc
    to_visit, all_urls = {start_url}, set()
    url_categories = {'Internal': set(), 'External': set(), 'Special': set(), 'FTP': set(), 'Media or Documents': set(), 'Others': set()}
    all_data = []  # To store structured content for JSON output

    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=30)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    MAX_THREADS = 13

    totalvisited_urls= 0

    while to_visit:
        current_url = to_visit.pop()
        logging.info(f"Visiting: {current_url}")
        all_urls.add(current_url)
        category = categorize_url(current_url, start_domain)
        url_categories[category].add(current_url)
        logging.info(f"URL: {current_url} added to category: {category}")

        if category == 'Internal':
                with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                    future_to_url = {executor.submit(process_internal_url, session, url, start_domain): url for url in [current_url]}
                    for future in as_completed(future_to_url):
                        data = future.result()
                        if data:
                            all_data.append(data)

        new_links, is_failed = get_links_from_page(session, current_url)
        if not is_failed:
            filtered_links = set(filter(lambda url: categorize_url(url, start_domain) != 'Others', new_links))
            to_visit.update(filtered_links - all_urls)

        time.sleep(random.uniform(0.005, 0.05))

        totalvisited_urls +=1
        if len(all_data) >=10:
            break

    save_to_json(all_data, 'oberoirealty.json')
    print(f"Total number of Internal URLs processed: {len(all_data)}")
    print("externallllll",len(url_categories['External']))
    print("internalllllll",len(url_categories['Internal']))
    print("Total number of visited urls processed:",totalvisited_urls)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total execution time: {total_time} seconds")
    logging.info("Happy Scrapping.")


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    start_url = "https://www.prestigeconstructions.com/"
    main(start_url)