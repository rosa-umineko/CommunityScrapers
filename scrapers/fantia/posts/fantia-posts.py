import json
import sys
import re
from datetime import datetime

from fetcher import get_post

try:
    import stashapi.log as log
except ModuleNotFoundError:
    print(
        "You need to install the stashapi module. (pip install stashapp-tools)",
        file=sys.stderr,
    )

def scrape(post_id):
    log.info(f"Scraping post ID: {post_id}")
    result = get_post(post_id)

    title = result['post']['title']
    description = result['post']['comment']
    cover = result['post']['thumb']['main']
    tags = [{"name": tag['name']} for tag in result['post']['tags']]
    date = datetime.strptime(result['post']['posted_at'], "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
    studio = { "name": result['post']['fanclub']['user']['name'] }

    log.info("Parsed Result: ")
    log.info(f"Title: {title}")
    log.info(f"Description: {description}")
    log.info(f"Cover: {cover}")
    log.info(f"Tags: {tags}")
    log.info(f"Date: {date}")
    log.info(f"Studio: {studio}")

    return {
        "title": title,
        "code": f"fantia-{post_id}",
        "details": description,
        "url": f"https://fantia.jp/posts/{post_id}",
        "image": cover,
        "tags": tags,
        "date": date,
        "studio": studio
    }

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
            pattern = r'https://fantia\.jp/posts/(\d+)'
            match = re.search(pattern, url)
            if match:
                post_id = match.group(1)
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
            pattern = r'fantia[-_](\d+)'
            match = re.search(pattern, title)
            if match:
                post_id = match.group(1)
                scene = scrape(post_id)
            else:
                log.error("Fragment scraping scene title but it doesn't include search term (fantia-<number> or fantia_<number>)")
        else:
            log.error("Missing title...")
    else:
        log.error("No argument processed")
        log.info(stdin)
    
    print(json.dumps(scene))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Unhandled exception: {e}")
