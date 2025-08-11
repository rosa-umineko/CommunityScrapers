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

def get_post(code):
    if code.startswith("http"):
        url = code
    else:
        url = f"https://www.avbase.net/works/{code}"
    
    log.info(f"Fetching URL: {url}")
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract values using BeautifulSoup
    title = soup.select_one("h1.text-lg").text.strip() if soup.select_one("h1.text-lg") else None
    code = soup.select_one("span:contains('名寄せID:') + div > span").text.strip() if soup.select_one("span:contains('名寄せID:') + div > span") else None
    date = soup.select_one("div:contains('発売日') + div a").text.strip() if soup.select_one("div:contains('発売日') + div a") else None
    image = soup.select_one("img.max-w-full.max-h-full")["src"] if soup.select_one("img.max-w-full.max-h-full") else None
    studio = soup.select_one("div:contains('レーベル') + div a").text.strip() if soup.select_one("div:contains('レーベル') + div a") else None

    # Canonical URL
    canonical_url = soup.select_one("link[rel='canonical']")["href"] if soup.select_one("link[rel='canonical']") else url

    # Tags
    tag_section = soup.select_one("div.mx-2.my-4 > div.flex.flex-wrap.gap-2.px-2")
    tags = tag_section.find_all("a") if tag_section else []
    
    # Performers
    performers_section = soup.select_one("div.mx-2.my-4 > div.flex.flex-wrap.gap-2")
    performers = []
    if performers_section:
        performer_links = performers_section.find_all("a", class_="chip")
        for performer in performer_links:
            name = performer.find("span").text.strip() if performer.find("span") else None
            performers.append({"name": name})
    elif performers_section and performers_section.find("span", class_="text-sm"):
        # Handle case where no performers are registered
        performers = []
  
    log.info(f"Title: {title}")
    log.info(f"Code: {code}")
    log.info(f"Date: {date}")
    log.info(f"Image: {image}")
    log.info(f"Studio: {studio}")
    log.info(f"URL: {canonical_url}")
    
    log.info(f"Tags: {tags}")
    
    return {
        "title": title,
        "code": code,
        "date": date.replace("/", "-") if date else None,
        "image": image,
        "studio": { "name": studio },
        "url": canonical_url,
        "tags": [{"name": a.text.strip()} for a in tags],
        "performers": performers,
        # "details": description,
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

    # Scrape via URL
    if "scene-by-url" in sys.argv:
        log.info("Processing scene by URL")
        log.info(stdin)
        url = inputJSON.get("url", None)
        
        if url:
            scene = scrape(url)
        else:
            log.error("Missing URL...")

    # Scrape Via Title
    elif "scene-by-fragment" in sys.argv:
        log.info("Processing scene by fragment")
        log.info(stdin)
        title = inputJSON.get("title", None)

        if title:
            scene = scrape(title)
        else:
            log.error("Missing title...")
    else:
        log.error("No argument processed")
        log.info(stdin)

    print(json.dumps(scene))


if __name__ == "__main__":
    main()