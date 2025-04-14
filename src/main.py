import urllib.parse
import base64
import boto3
import logging
from supporting import aws
import uuid
import time
import json

formatter = logging.Formatter('[%(levelname)s] %(message)s')
log = logging.getLogger()
log.setLevel("INFO")
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
for handler in log.handlers:
    log.removeHandler(handler)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)

def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    if method == "GET":
        event_list = []

        events = aws.all_events('events')

        # Create the dropdown options dynamically
        options_html = ""
        for e in events:

            # If each item is a string:
            event_name = e.get("name", "Unnamed Event")
            event_id = e.get("id", "")
            if event_id != "demo_event":
                result = {
                    "event_name": event_name,
                    "event_id": event_id
                }
                event_list.append(result)

        sorted_events = sorted(event_list, key=lambda x: x['event_name'].lower())

        for item in sorted_events:
            event_id = item["event_id"]
            event_name = item["event_name"]
            options_html += f'<option value="{event_id}:{event_name}">{event_name}</option>\n'

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": f"""
            <html>
            <head>
              <title>Subscription form</title>
              <style>
                body {{
                  font-family: "Segoe UI", sans-serif;
                  background: #f5f7fa;
                  display: flex;
                  justify-content: center;
                  align-items: center;
                  height: 100vh;
                  margin: 0;
                }}
                .form-container {{
                  background: white;
                  padding: 2rem;
                  border-radius: 12px;
                  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                  max-width: 400px;
                  width: 100%;
                }}
                h1 {{
                  font-size: 1.5rem;
                  margin-bottom: 1.5rem;
                  text-align: center;
                }}
                label {{
                  display: block;
                  margin-bottom: 0.5rem;
                  font-weight: 600;
                }}
                input, select {{
                  width: 100%;
                  padding: 0.75rem;
                  margin-bottom: 1.25rem;
                  border: 1px solid #ccc;
                  border-radius: 8px;
                  font-size: 1rem;
                }}
                input[type="submit"] {{
                  background-color: #007bff;
                  color: white;
                  border: none;
                  cursor: pointer;
                  transition: background-color 0.2s ease-in-out;
                }}
                input[type="submit"]:hover {{
                  background-color: #0056b3;
                }}
              </style>
            </head>
            <body>
              <div class="form-container">
                <h1>Subscription Form</h1>
                <form method="POST">
            
                  <label for="email">Email</label>
                  <input type="email" id="email" name="email" required />
            
                  <label for="event">Event</label>
                  <select name="event" id="event">
                    {options_html}
                  </select>
            
                  <input type="submit" value="Subscribe" />
                </form>
              </div>
            </body>
            </html>
            """
        }

    elif method == "POST":
        lambda_client = boto3.client('lambda')
        body = event.get("body", "")
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode('utf-8')

        data = urllib.parse.parse_qs(body)
        name = data.get("name", [""])[0]
        email = data.get("email", [""])[0]
        event_string = data.get("event", [""])[0]
        event_id, event_name = event_string.split(":")
        sub_id = str(uuid.uuid4()).replace('-', '')
        table_name = 'subscribe_confirm'  # Replace with your table name.
        valid_until = int(time.time()) + 30*60

        item = {
            'id': sub_id,
            'valid_until': valid_until,
            'event_id': event_id,
            'email': email
        }
        aws.put_item_dynamodb(table_name, item)
        payload = {
            "to": email,
            "from": "runningeventswarning@gmail.com",
            "subject": f"Bevestig inschrijving {event_name}",
            "content": f"Bevestig je inschrijving voor notificaties omtrent {event_name} <a href='http://example.test.com?id={sub_id}'>HIER</a>"
        }
        lambda_client.invoke(
            FunctionName='sendMail',  # Replace with the name of your sendMail function
            InvocationType='Event',  # Use 'RequestResponse' for synchronous invocation
            Payload=json.dumps(payload)
        )
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": f"""
            <html>
            <head>
              <title>Thank You</title>
              <style>
                body {{
                  font-family: "Segoe UI", sans-serif;
                  background: #f5f7fa;
                  display: flex;
                  justify-content: center;
                  align-items: center;
                  height: 100vh;
                  margin: 0;
                }}
                .response-container {{
                  background: white;
                  padding: 2rem;
                  border-radius: 12px;
                  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                  max-width: 400px;
                  width: 100%;
                  text-align: center;
                }}
                h1 {{
                  font-size: 1.75rem;
                  color: #28a745;
                  margin-bottom: 1rem;
                }}
                p {{
                  font-size: 1rem;
                  margin-bottom: 1rem;
                  color: #333;
                }}
                a {{
                  display: inline-block;
                  margin-top: 1rem;
                  text-decoration: none;
                  color: #007bff;
                  font-weight: 600;
                  transition: color 0.2s ease-in-out;
                }}
                a:hover {{
                  color: #0056b3;
                }}
              </style>
            </head>
            <body>
              <div class="response-container">
                <p>We received your email: <strong>{email}</strong></p>
                <p>You selected the event: <strong>{event_name}</strong></p>
                <p>A confirmation email has been sent to this address with a confirmation link.<br> 
                Please confirm your subscription within 30 minutes. <br>
                If the email ends up in your spam folder, please mark it as "Not Spam" to avoid missing future messages.
                </p>
                <a href="/">Go back to the form</a>
              </div>
            </body>
            </html>
            """

        }

    else:
        return {
            "statusCode": 405,
            "body": "Method Not Allowed"
        }

