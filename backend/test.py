import requests

r = requests.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    params={"key": "AIzaSyAPNhTeKhmFD6A5ii_EyHcgyHOXIiU5xLk"}
)
print(r.status_code)
print(r.text)
