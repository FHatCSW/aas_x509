import requests
import json

def create_aas(url, payload):
    headers = {
        "Content-Type": "application/json",
    }

    response = requests.put(url, headers=headers, data=json.dumps(payload))

    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(response.text)

def read_json_from_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Example usage:
url = "http://localhost:4001/aasServer/shells/industrial_device"
template_file_path = 'aas_template.json'

# Read JSON content from the external file
payload = read_json_from_file(template_file_path)

create_aas(url, payload)
