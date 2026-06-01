import requests
import json

def test_api():
    url = "http://127.0.0.1:8000/generate_document"
    payload = {
        "files": [
            {
                "name": "project_brief.md",
                "content": "Project Overview: Atlas platform for real-time logistics. Goal: reduce latency by 25%. Timeline: 8 weeks."
            },
            {
                "name": "budget.json",
                "content": '{"total_budget": 150000, "currency": "USD"}'
            }
        ]
    }
    
    print("Sending POST request to:", url)
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print("\nResponse Structure is Valid!")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("Error Response:", response.text)

if __name__ == "__main__":
    test_api()
