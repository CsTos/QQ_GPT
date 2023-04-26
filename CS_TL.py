import json
import requests

url = "http://openapi.turingapi.com/openapi/api/v2"

data = {
    "reqType": 0,
    "perception": {
        "inputText": {
            "text": "我叫什么名字？"
        },
        "inputImage": {
            "url": "imageUrl"
        }
    },
    "userInfo": {
        "apiKey": "da5c408ab0beab40d4a3fd7b89f3da34",
        "userId": "CsTos"
    }
}

headers = {
    "Content-Type": "application/json;charset=utf-8"
}

response = requests.post(url, headers=headers, data=json.dumps(data))
result = json.loads(response.text)
text = result["results"][0]["values"]["text"]
print(text)