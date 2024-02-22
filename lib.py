import requests

API_KEY = "API_KEY"

def get_instagram_data(_id, fields, after_pag = None):
    url = f"https://graph.facebook.com/v19.0/{_id}"
    params = {
        'access_token': API_KEY,
        'debug': 'all',
        'fields': fields,
        'format': 'json',
        'method': 'get',
        'pretty': '0',
        'suppress_http_code': '1',
        'transport': 'cors',
        'after': after_pag

    }
    response = requests.get(url, params=params)
    return response.json()


def extract_comments(post_id, after_pag = None):
    data = get_instagram_data(_id=post_id, fields='comments_count,comments{text,media,from,like_count,timestamp}', after_pag=after_pag)
    return data


def extract_initial_data(insta_id):
    data = get_instagram_data(_id=insta_id, fields='followers_count,media')
    return data
