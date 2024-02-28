import logging
import json
import requests

from lib import extract_comments, extract_initial_data
import azure.functions as func
from azure.eventhub import EventHubProducerClient, EventData

INSTAGRAM_ACCOUNT_ID = "INSTAGRAM_ACCOUNT_ID"
EVT_HUB_CONN_STR = "EVT_HUB_CONN_STR"

app = func.FunctionApp()


def send_to_eventhub(data):
    # Create a producer client
    producer = EventHubProducerClient.from_connection_string(EVT_HUB_CONN_STR)
    
    # Create a batch and add events to it
    with producer:
        batch = producer.create_batch()
        for obj in data:
            batch.add(EventData(json.dumps(obj)))
        producer.send_batch(batch)


@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    
    if myTimer.past_due:
        logging.info('The timer is past due!')

    get_initial_data = extract_initial_data(INSTAGRAM_ACCOUNT_ID)
    all_comments = []

    for media in get_initial_data.get('media', {}).get('data', []):
        post_id = media.get('id')
        comments_data = extract_comments(post_id, 'comments_count,comments{text,media,from,like_count,timestamp}')

        comments_count = comments_data.get('comments_count', 0)

        if comments_count < 0 or comments_data.get('comments') is None:
            continue
        
        comments_pagination = comments_data.get('comments', {}).get('paging', {})

        print(comments_pagination)

        comments = comments_data.get('comments', {}).get('data', [])
        for comment in comments:
            all_comments.append({
                "followers_count": get_initial_data.get("followers_count"),
                "text": comment["text"],
                "username": comment.get("from", {}).get("username"),
                "like_count": comment["like_count"],
                "timestamp": comment["timestamp"],
                "user_id": comment.get("from", {}).get("id"),
                "post_id": comment["id"],
            })

        while len(comments_pagination.keys()) > 0:
            comments_after = comments_pagination.get('cursors', {}).get('after', {})
            get_comments_next = extract_comments(f'{post_id}/comments', 'text,media,from,like_count,timestamp', comments_after)
            comments_count = get_comments_next.get('comments_count', 0)
            print(get_comments_next)

            if comments_pagination is None:
                continue

            comments = get_comments_next.get('data', [])
            for comment in comments:
                all_comments.append({
                    "followers_count": get_initial_data.get("followers_count"),
                    "text": comment["text"],
                    "username": comment.get("from", {}).get("username"),
                    "like_count": comment["like_count"],
                    "timestamp": comment["timestamp"],
                    "user_id": comment.get("from", {}).get("id"),
                    "post_id": comment["id"],
                })

            comments_pagination = get_comments_next.get('comments', {}).get('paging', {})

    # print(all_comments)
    send_to_eventhub(all_comments)
