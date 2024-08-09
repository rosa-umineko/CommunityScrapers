import json
import sys
import re
from lxml import html
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
    tree = html.fromstring(response.content)

    log.info("Tree response: " + str(tree))

    title = tree.xpath("//meta[@property='og:title']/@content")[0]
    
    code_url = tree.xpath("//meta[@property='og:url']/@content")[0]
    code = re.sub(r'https:\/\/dl\.getchu\.com\/i\/item(\d+)', r'getchu-\1', code_url)
    
    date_raw = tree.xpath("//td[text()='配信開始日']/following-sibling::td/text()")[0]
    date_match = re.search(r'(\d{4})/(\d{2})/(\d{2})', date_raw)
    if date_match:
        date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
    
    description = tree.xpath("//meta[@name='description']/@content")[0]
    
    tags_elements = tree.xpath("//td[text()='趣向']/following-sibling::td[@class='item-key']/a")
    tags = [{"name": tag.text_content()} for tag in tags_elements]
    
    studio_name = tree.xpath("//td[text()='サークル']/following-sibling::td/a/text()")[0]
    studio = {"name": studio_name}
    
    cover = tree.xpath("//img[contains(@src, 'top') and contains(@src, 'item_img')]/@src")[0]
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