print("Python application started")
from flask import Flask, request
from datetime import datetime, timezone
import logging

app=Flask(__name__)

visitor_logger=logging.getLogger("visitor_logger")
visitor_logger.setLevel(logging.INFO)

handler=logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
visitor_logger.addHandler(handler)
visitor_logger.propagate= False

@app.route("/")
def home():
    ip=request.remote_addr or "unknown"

    timestamp=datetime.now(timezone.utc).isoformat()

    visitor_logger.info("Visitor IP:%s|Time:%s", ip, timestamp)

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
     </body>
    </html>
    """



if __name__=="__main__":
    app.run(debug=False)    
