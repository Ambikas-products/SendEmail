import requests

domain_name = "YOUR_domain_name_PARAMETER"
url = "https://api.mailgun.net/v3/" + domain_name + "/messages"

data = {
  "from": "string",
  "to": "string",
  "subject": "string"
}

headers = {"Content-Type": "multipart/form-data"}

response = requests.post(url, data=data, headers=headers, auth=('<username>','<password>'))

data = response.json()
print(data)