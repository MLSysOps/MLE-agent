from flask import Flask, Response, request
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)


@app.route('/chat', methods=['GET'])
def chat():
    project = request.args.get('project')
    message = request.args.get('message')

    def generate():
        responses = ["Of ", "course! ", "Based ", "on ", "the ", "message ", "you ", "sent, ", "here ", "is ", "a ",
                     "chunked ", "response."]
        for chunk in responses:
            yield chunk
            time.sleep(0.5)  # Simulate delay for each chunk

    return Response(generate(), content_type='text/plain')


if __name__ == '__main__':
    app.run(port=8000)
