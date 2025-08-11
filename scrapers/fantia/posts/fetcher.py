import requests

# Define constants for cookie, user-agent, and x-csrf-token
COOKIE = "jp_chatplus_vtoken=pgz3nm5hvp6w20t8zcwhab404376; _f_v_k_1=f5b0e23e0d580175695830189aedb0c3fe9def271a15301f2c8ad23a85e59545; _session_id=86068d265c217efc901f10d49252b88bf1067ee13c3e5573e529a1b671f5509e"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
X_CSRF_TOKEN = "tjnSIrbIrNRpI8wzk9Qrb6kd24E6KjawYMEdn1DMXvltfu0MtpYk0q51W4qR7plwesVxfGYUk0qE3Yfwbg_7LA"

def get_post(post_id):
    url = f"https://fantia.jp/api/v1/posts/{post_id}"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cookie": COOKIE,
        "user-agent": USER_AGENT,
        "x-csrf-token": X_CSRF_TOKEN,
        "x-requested-with": "XMLHttpRequest"
    }
    
    response = requests.get(url, headers=headers)
    return response.json()
