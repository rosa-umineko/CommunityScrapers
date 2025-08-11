import json
import sys
import re
from bs4 import BeautifulSoup
import requests

try:
    import stashapi.log as log
except ModuleNotFoundError:
    print(
        "You need to install the stashapi module. (pip install stashapp-tools)",
        file=sys.stderr,
    )

def get_post(post_id):
    url = f"https://dl.getchu.com/i/item{post_id}"
    log.info("Requesting from url " + str(url))
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    log.info("Soup response: " + str(soup))

    title = soup.find("meta", {"property": "og:title"})["content"]
    
    code_url = soup.find("meta", {"property": "og:url"})["content"]
    code = re.sub(r'https:\/\/dl\.getchu\.com\/i\/item(\d+)', r'getchu-\1', code_url)
    
    date_raw = soup.find("td", text="配信開始日")
    if date_raw is not None:
        date_raw = date_raw.find_next_sibling("td").text
        date_match = re.search(r'(\d{4})/(\d{2})/(\d{2})', date_raw)
        if date_match:
            date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
    else:
        date = None
    
    description = soup.find("meta", {"name": "description"})["content"]
    
    tags_elements = soup.find("td", text="趣向")
    if tags_elements is None:
        tags = []
    else:
        tags_elements = tags_elements.find_next_sibling("td", class_="item-key").find_all("a")
        tags = [{"name": tag.text} for tag in tags_elements]
    
    studio_name = soup.find("td", text="サークル")
    if studio_name is None:
        studio = None
    else:
        studio_name = studio_name.find_next_sibling("td").find("a").text
        studio = {"name": studio_name}
    
    cover = soup.find("img", src=re.compile(r"/data/item_img/.*top\.jpg"))["src"]
    cover = f"https://dl.getchu.com{cover}"

    return {
        "title": title,
        "code": code,
        "details": description,
        "url": url,
        "image": cover,
        "tags": tags,
        "date": date,
        "studio": studio
    }

def scrape(post_id):
    log.info(f"Scraping post ID: {post_id}")
    return get_post(post_id)

def main():
    if len(sys.argv) == 1:
        log.error("No arguments provided.")
        sys.exit(1)
    
    stdin = sys.stdin.read()
    log.info(f"Stdin: {stdin}")

    try:
        inputJSON = json.loads(stdin)
    except json.JSONDecodeError as e:
        log.error(f"JSON decode error from stdin: {e}")
        sys.exit(1)

    log.info("Args" + str(sys.argv))

    scene = None

    if "scene-by-url" in sys.argv:
        log.info("Processing scene by URL")
        log.info(stdin)
        url = inputJSON.get("url", None)
        
        if url:
            pattern = r'\d{4,}'
            log.info("Searching for URL " + url)
            match = re.search(pattern, url)
            if match:
                post_id = match.group(0)
                scene = scrape(post_id)
            else:
                log.error("Improper URL format")
        else:
            log.error("Missing URL...")

    elif "scene-by-fragment" in sys.argv:
        log.info("Processing scene by fragment")
        log.info(stdin)
        title = inputJSON.get("title", None)

        if title:
            pattern = r'\b\d{4,}\b'
            match = re.search(pattern, title)
            if match:
                post_id = match.group(0)
                scene = scrape(post_id)
            else:
                log.error("Fragment scraping scene title but it doesn't include search term (>= 4 digit number as item id)")
        else:
            log.error("Missing title...")
    else:
        log.error("No argument processed")
        log.info(stdin)

    print(json.dumps(scene))


if __name__ == "__main__":
    main()