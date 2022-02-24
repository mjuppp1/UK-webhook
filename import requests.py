import requests
import json
webhook_url = "https://discord.com/api/webhooks/946227315225018379/61hCUw4Ed4dH5vr-4D6yE9iWRcnSr5PvQy-z5e_8JHVsxm8YDh0rCJ9k3A9Ubvk7esjc"
data = "hello"

requests.post(
    webhook_url,
    data=json.dumps(data),
    headers={'Content-Type' : 'application/json'})