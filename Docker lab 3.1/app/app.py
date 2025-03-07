
from flask import Flask, request, jsonify

import random
import time
from threading import Thread
from prometheus_client import Counter, Gauge, start_http_server

from app.db import driver

app = Flask(__name__)

HASHTAGS = ['travel', 'food', 'beauty', 'fitness','nature', 'fashion']

post_counter = Counter('generated_posts_total', 'Total generated posts')
likes_gauge = Gauge('post_likes', 'Likes per post', ['hashtag'])


def generate_random_posts():
    while True:
        hashtag = random.choice(HASHTAGS)
        likes = random.randint(0, 100)
        query = (
            "MERGE (h:Hashtag {name: $hashtag}) "
            "CREATE (p:Post {likes: $likes, createdAt: timestamp()})-[:TAGGED]->(h)"
        )
        with driver.session() as session:
            session.run(query, hashtag=hashtag, likes=likes)
        post_counter.inc()
        likes_gauge.labels(hashtag).set(likes)
        time.sleep(5)

Thread(target=generate_random_posts, daemon=True).start()

@app.route('/query', methods=['POST'])
def execute_query():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    try:
        with driver.session() as session:
            result = session.run(query)
            data = [record.data() for record in result]
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/hashtags/popularity', methods=['GET'])
def get_hashtag_popularity():
    query = """
    MATCH (h:Hashtag)<-[:TAGGED]-(p:Post)
    RETURN h.name AS hashtag, COUNT(p) AS popularity
    ORDER BY popularity DESC
    LIMIT 10
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            data = [record.data() for record in result]
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

