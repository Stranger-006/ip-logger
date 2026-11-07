from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timezone
import logging
import secrets

app=Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

visitor_logger=logging.getLogger("visitor_logger")
visitor_logger.setLevel(logging.INFO)

handler=logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

if not visitor_logger.handlers:
    visitor_logger.addHandler(handler)
visitor_logger.propagate= False

DEMO_RANGES=["192.0.2", "198.51.100", "203.0.113"]

def generate_demo_ip():
    prefix=secrets.choice(DEMO_RANGES)
    last_octet=secrets.randbelow(254) + 1
    return prefix + str(last_octet)

@app.route("/")
def home():
    ip=request.remote_addr or "unknown"

    timestamp=datetime.now(timezone.utc).isoformat()

    visitor_logger.info("LIVE VISITOR | IP:%S|Time:%s|XFF:%s", ip, timestamp, request.headers.get("X-Forwarded-For",
                                                                                                  "Not supplied"))

    print(f"Logged visitor IP: {ip} at {timestamp}",flush=True)

    return """
    <!DOCTYPE html>
    <html>
     <head>
      <title>IP Logger</title>
     </head>
     <body>
      <h1>Welcome!</h1>
      <p>Your visit has been logged.</p> 
      
      <hr>

      <h2>IP demonstration</h2>
      <p>Generate a simulated IP address for testing</p>
      <form action="/demo" method="post">
        <button type="submit">Generate Demo IP</button>
      </form>
     </body>
    </html>
    """

@app.route("/demo", methods=["POST"])
def demo():
    try:
        demo_ip=generate_demo_ip()
        timestamp=datetime.now(timezone.utc).isoformat()
        visitor_logger.info("DEMO VISITOR | IP:%s|Time:%s|XFF:%s", demo_ip, timestamp, request.headers.get("X-Forwarded-For",
                                                                                                     "Not supplied"))
        print(f"Logged demo visitor IP: {demo_ip} at {timestamp}",flush=True)
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <title>IP Logger - Demo</title>
        </head>
        <body>
        <h1>Demo IP Generated!</h1>
        <p>Your simulated IP address is: {demo_ip}</p> 
      
        <hr>
        <a href="/">Back to Home</a>
        </body>
        </html>
        """
    except Exception:
        app.logger.exception("Demo generation failed")
        return "Unable to generate demo IP.",500
if __name__=="__main__":
    app.run(debug=False)    
