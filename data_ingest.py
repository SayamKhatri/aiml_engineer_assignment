# import requests, json, os
# from dotenv import load_dotenv
# load_dotenv()

# API_URL = os.getenv('url')
# os.makedirs("data", exist_ok=True)

# resp = requests.get(API_URL)
# resp.raise_for_status()
# data = resp.json()
# total = data.get("total", len(data.get("items", [])))

# print(f"Total messages available: {total}")

# resp = requests.get(API_URL, params={"limit": total}) 
# resp.raise_for_status()
# data = resp.json()
# messages = data["items"]

# print(f"Total messages fetched: {len(messages)}")

# with open("data/messages.json", "w") as f:
#     json.dump(messages, f, indent=2)





