import json


def my_http_error(http_error, message):
    text = json.dumps({'error': message})
    content_type = 'application/json'
    error = http_error(text=text, content_type=content_type)
    return error
