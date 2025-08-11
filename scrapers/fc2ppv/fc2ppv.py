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
    
# Match FC2 - any number of strings followed by '-(number pattern)'
def validate_title(title):
    pattern = r"^FC2-(?:[A-Za-z]+-)?(\d+)$"
    match = re.match(pattern, title)
    if match:
        log.info(f"Valid title: {title}")
        return match.group(1)
    else:
        log.error(f"Invalid title: {title}")
        return None

def get_post(code):
    if code.startswith("http"):
        url = code
    else:
        url = f"https://adult.contents.fc2.com/article/{code}/"
    
    log.info(f"Fetching URL: {url}")
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    title = soup.find('meta', {'property': 'og:title'}).get('content', '').split(' FC2')[0]
    image = soup.find('meta', attrs={'property': 'og:image'})["content"]
    description = soup.find('meta', attrs={'name': 'description'})["content"]
    url = soup.find('meta', {'property': 'og:url'}).get('content', '')
    code = "FC2-" + url.split('/')[-2]
    studio = soup.select_one('.items_article_headerInfo a[href^="https://adult.contents.fc2.com/users/"]').text
    date = soup.select_one('.items_article_Releasedate p').text.split(': ')[1].replace('/', '-')
    
    tags = [tag.text for tag in soup.select('.items_article_TagArea .tagTag')]
  
    log.info(f"Title: {title}")
    log.info(f"Description: {description}")
    log.info(f"Image: {image}")
    log.info(f"URL: {url}")
    log.info(f"Studio: {studio}")
    log.info(f"Date: {date}")
    
    log.info(f"Tags: {tags}")
    log.info(f"Code: {code}")
    
    return {
        "title": title,
        "image": image,
        "details": description,
        "url": url,
        "studio": { "name": studio },
        "date": date,
        "tags": [{"name": a.strip()} for a in tags],
        "code": code,
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
            matched = validate_title(title)
            if matched:
              scene = scrape(matched)
            else:
              log.error("Invalid title...")
        else:
            log.error("Missing title...")
    else:
        log.error("No argument processed")
        log.info(stdin)

    print(json.dumps(scene))


if __name__ == "__main__":
    main()