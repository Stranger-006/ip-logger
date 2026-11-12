from flask import Flask, request, render_template_string
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timezone
import logging
import secrets
from firewall import check_request


app=Flask(__name__)
@app.before_request
def firewall_guard():
    if request.path == "/favicon.ico":
        return "",204
    if request.method in("HEAD","OPTIONS"):
        return None
    ip=request.remote_addr or "unknown"

    allowed,reason=check_request(ip)

    if not allowed:
        return reason,429

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
    return prefix + "." + str(last_octet)

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP Logger | Network Security</title>

    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: Arial, sans-serif;
            background: #0b1120;
            color: #e5e7eb;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 25px;
        }

        .container {
            width: 100%;
            max-width: 720px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #60a5fa;
            font-size: 32px;
            margin-bottom: 10px;
        }

        .header p {
            color: #94a3b8;
            font-size: 14px;
        }

        .card {
            background: #151f32;
            border: 1px solid #26364f;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        }

        .status {
            display: inline-block;
            color: #4ade80;
            background: #123326;
            padding: 7px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-bottom: 18px;
        }

        h2 {
            font-size: 21px;
            margin-bottom: 12px;
            color: #f8fafc;
        }

        .description {
            color: #a8b4c7;
            line-height: 1.7;
            font-size: 14px;
            margin-bottom: 22px;
        }

        .button {
            display: inline-block;
            background: #2563eb;
            color: white;
            text-decoration: none;
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
        }

        .button:hover {
            background: #3b82f6;
            transform: translateY(-2px);
        }

        .result {
            background: #0b1729;
            border: 1px solid #2563eb;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }

        .ip {
            color: #60a5fa;
            font-size: 25px;
            font-weight: bold;
            margin-top: 10px;
            overflow-wrap: anywhere;
        }

        .note {
            color: #fbbf24;
            font-size: 12px;
            margin-top: 12px;
        }

        .footer {
            text-align: center;
            color: #64748b;
            font-size: 12px;
            margin-top: 25px;
        }

        @media (max-width: 500px) {
            .header h1 {
                font-size: 26px;
            }

            .card {
                padding: 22px;
            }
        }
    </style>
</head>

<body>
    <main class="container">

        <header class="header">
            <h1>IP Logger</h1>
            <p>Visitor Monitoring & Network Protection System</p>
        </header>

        {% if demo_ip %}
        <section class="card">
            <span class="status">DEMO GENERATED</span>
            <h2>Your simulated IP address</h2>
            <p class="description">
                A demonstration IP address has been generated
                successfully for testing purposes.
            </p>

            <div class="result">
                <p>Simulated IP Address</p>
                <div class="ip">{{ demo_ip }}</div>
            </div>

            <p class="note">
                This is a simulated address, not your actual public IP.
            </p>

            <a href="{{ url_for('home') }}" class="button">
                Back to Home
            </a>
        </section>

        {% else %}
        <section class="card">
            <span class="status">SYSTEM ONLINE</span>

            <h2>Welcome to IP Logger</h2>

            <p class="description">
                This project demonstrates website visitor IP logging,
                request monitoring, database storage and automated
                firewall protection.
            </p>

            <form action="{{ url_for('demo') }}" method="post">
                <button type="submit" class="button">
                    Generate Demo IP
                </button>
            </form>
        </section>

        <section class="card">
            <h2>About the System</h2>
            <p class="description">
                The system records visitor requests and uses a
                MongoDB-backed firewall to monitor request frequency
                and temporarily block addresses that exceed
                the configured request limit.
            </p>
        </section>
        {% endif %}

        <footer class="footer">
            IP Logger & Firewall System | Educational Project
        </footer>

    </main>
</body>
</html>
"""

@app.route("/")
def home():
    ip=request.remote_addr or "unknown"

    timestamp=datetime.now(timezone.utc).isoformat()

    visitor_logger.info(f"LIVE VISITOR | IP:{ip}|Time:{timestamp}|" f"XFF:{request.headers.get('X-Forwarded-For','Not supplied')}")

    print(f"Logged visitor IP: {ip} at {timestamp}",flush=True)

    return render_template_string(PAGE_TEMPLATE)

@app.route("/demo", methods=["POST"])
def demo():
    try:
        demo_ip=generate_demo_ip()
        timestamp=datetime.now(timezone.utc).isoformat()
        visitor_logger.info(f"DEMO VISITOR | IP:{demo_ip}|Time:{timestamp}|" f"XFF:{request.headers.get('X-Forwarded-For','Not supplied')}")
        print(f"Logged demo visitor IP: {demo_ip} at {timestamp}",flush=True)
        return render_template_string(PAGE_TEMPLATE, demo_ip=demo_ip)
    except Exception:
        app.logger.exception("Demo generation failed")
        return "Unable to generate demo IP.",500
if __name__=="__main__":
    app.run(debug=False)    
