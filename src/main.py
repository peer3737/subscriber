import urllib.parse
import base64

def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    if method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": """
            <html>
            <head><title>Simple Form</title></head>
            <body>
              <h1>Contact Form</h1>
              <form method="POST">
                <label>Name: <input type="text" name="name" /></label><br /><br />
                <label>Email: <input type="email" name="email" /></label><br /><br />
                <input type="submit" value="Submit" />
              </form>
            </body>
            </html>
            """
        }

    elif method == "POST":
        body = event.get("body", "")
        if event.get("isBase64Encoded"):

            body = base64.b64decode(body).decode('utf-8')

        data = urllib.parse.parse_qs(body)
        name = data.get("name", [""])[0]
        email = data.get("email", [""])[0]

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": f"""
            <html>
            <body>
              <h1>Thank you, {name}!</h1>
              <p>We received your email: {email}</p>
              <a href="/">Go back</a>
            </body>
            </html>
            """
        }

    else:
        return {
            "statusCode": 405,
            "body": "Method Not Allowed"
        }
