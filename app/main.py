from flask import Flask, Response
import os
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

BLOB_URL = os.getenv('BLOB_URL')

@app.route('/')
def serve_blob():
    if not BLOB_URL:
        logging.error("BLOB_URL not configured")
        return Response("Server misconfiguration", status=500)
    logging.info(f"Fetching content from {BLOB_URL}")
    resp = requests.get(BLOB_URL)
    return Response(resp.text, mimetype='text/html', status=resp.status_code)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)