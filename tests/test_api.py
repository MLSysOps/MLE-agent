import requests

if __name__ == "__main__":
    with requests.get('http://localhost:8000/chat', params={'project': 'test', 'message': 'hello?'}, stream=True) as r:
        for chunk in r.iter_content():
            print(chunk)
