import json
import sys
import re
from datetime import datetime
import requests

try:
    import stashapi.log as log
except ModuleNotFoundError:
    print(
        "You need to install the stashapi module. (pip install stashapp-tools)",
        file=sys.stderr,
    )

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"

def get_scene_data(dvd_id):
    """fetch scene data from r18.dev api"""
    url = f"https://r18.dev/videos/vod/movies/detail/-/dvd_id={dvd_id}/json"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    log.info(f"Requesting from url: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        log.error(f"Failed to fetch data. Status code: {response.status_code}")
        return None
    
    return response.json()

def scrape_scene(dvd_id, original_code=None):
    """scrape scene metadata"""
    log.info(f"Scraping scene with DVD ID: {dvd_id}")
    result = get_scene_data(dvd_id)
    
    if not result:
        return None
    
    # basic fields
    title = result.get('title', '')
    # use original_code if provided, otherwise use dvd_id
    code = original_code if original_code else dvd_id
    details = result.get('title', '')
    date = result.get('release_date', '')
    
    # image - prefer large2 from jacket_image
    image = None
    images = result.get('images', {})
    jacket = images.get('jacket_image', {})
    image = jacket.get('large2', jacket.get('large', ''))
    
    # director
    director = result.get('director', '')
    
    # studio - from maker
    studio = None
    maker = result.get('maker')
    if maker and maker.get('name'):
        studio = {"name": maker['name']}
    
    # performers - from actresses
    performers = []
    for actress in result.get('actresses', []):
        name = actress.get('name', '')
        if name:
            performers.append({"name": name})
    
    # tags - from categories
    tags = []
    for category in result.get('categories', []):
        tag_name = category.get('name', '')
        if tag_name:
            tags.append({"name": tag_name})
    
    # url
    content_id = result.get('content_id', '')
    url = f"https://r18.dev/videos/vod/movies/detail/-/id={content_id}" if content_id else ''
    
    # runtime (optional - convert minutes to seconds or leave as is)
    duration = result.get('runtime_minutes')
    if duration:
        duration = duration * 60  # convert to seconds if needed
    
    log.info(f"Successfully scraped: {title}")
    
    scene_data = {
        "title": title,
        "code": code,
        "details": details,
        "url": url,
        "image": image,
        "tags": tags,
        "date": date,
        "studio": studio,
        "performers": performers
    }
    
    # add optional fields only if they exist
    if director:
        scene_data["director"] = director
    
    if duration:
        scene_data["duration"] = duration
    
    return scene_data

def extract_dvd_id_from_filename(filename):
    """extract jav code from filename using regex"""
    # regex from original yaml
    pattern = r'.*?([a-zA-Z|tT28]+)-?(\d+)[zZ]?[eE]?(?:-pt)?(\d{1,2})?.*'
    match = re.search(pattern, filename)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    return None

def extract_dvd_id_from_url(url):
    """extract content id from r18.dev url"""
    pattern = r'.+/id=(.+)/?$'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

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
    
    log.info(f"Args: {sys.argv}")
    
    scene = None
    
    if "scene-by-url" in sys.argv:
        log.info("Processing scene by URL")
        url = inputJSON.get("url", None)
        
        if url:
            dvd_id = extract_dvd_id_from_url(url)
            if dvd_id:
                scene = scrape_scene(dvd_id)
            else:
                log.error("Could not extract DVD ID from URL")
        else:
            log.error("Missing URL...")
    
    elif "scene-by-fragment" in sys.argv:
        log.info("Processing scene by fragment")
        
        # get the original code from fragment
        fragment = inputJSON
        original_code = fragment.get("code") or fragment.get("title")
        
        if original_code:
            log.info(f"Original code from fragment: {original_code}")
            # extract regex'd version for API search
            dvd_id = extract_dvd_id_from_filename(original_code)
            if dvd_id:
                log.info(f"Using regex'd DVD ID for search: {dvd_id}")
                # pass both: regex'd for search, original for return
                scene = scrape_scene(dvd_id, original_code=original_code)
            else:
                log.error("Could not extract DVD ID from code using regex")
        else:
            log.error("Could not find code in fragment")
            log.info(f"Fragment keys available: {list(fragment.keys())}")
    
    elif "scene-by-name" in sys.argv:
        log.info("Processing scene by name")
        name = inputJSON.get("name", None)
        
        if name:
            # directly use the name as dvd_id
            scene = scrape_scene(name)
        else:
            log.error("Missing name...")
    
    else:
        log.error("No valid argument processed")
    
    print(json.dumps(scene))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Unhandled exception: {e}")
        import traceback
        log.error(traceback.format_exc())
        sys.exit(1)