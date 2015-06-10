"""EasyEngine JSON to Dict"""
from urllib.request import urlopen
import json


def api_return(url):
    try:
        response = urlopen(url)
        data = str(response.read().decode('utf-8'))
        return json.loads(data)
    except Exception as e:
        return False
