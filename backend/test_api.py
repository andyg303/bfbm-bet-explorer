import requests
import json

# Test the strategy-stats endpoint
response = requests.post('http://localhost:8000/strategy-stats', json={
    "strategies": [],
    "bet_types": [],
    "statuses": [],
    "market_types": [],
    "country_codes": [],
    "events": []
})

if response.status_code == 200:
    data = response.json()
    if data:
        print("First strategy stats:")
        print(json.dumps(data[0], indent=2))
    else:
        print("No strategy stats returned")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
