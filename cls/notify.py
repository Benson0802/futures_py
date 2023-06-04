import requests

# token = 'wGMbR1lfhORDv3MeNo2UD8YK2htvlTXknXzK6mYYgJe'
token = '1QKVLNZLBaiWJAZWwP98M1boYdUUCr8dCViSyIJdEOF'
message = '這是用 Python 發送的訊息'
headers = { "Authorization": "Bearer " + token }

def sendMessage(message):
    data = { 'message': message }
    requests.post("https://notify-api.line.me/api/notify",headers = headers, data = data)

# sendMessage(message)