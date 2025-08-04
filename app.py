from flask import Flask, render_template, request
import datetime
import os
import pandas as pd
import openai
from dotenv import load_dotenv
from train_model import analyze_login_with_chatgpt

# Load environment variables (including API key)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

DATA_FILE = 'login_data.csv'

# Simulated device ID generator (for now)
def get_device_id():
    return 12345

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']  # Not used, just for realism
    now = datetime.datetime.now()

    hour = now.hour
    weekday = now.strftime("%A")
    ip_address = request.remote_addr
    user_agent = request.user_agent.string
    device_id = get_device_id()

    # ✅ Package the current login attempt
    current_login = {
        'username': username,
        'hour': hour,
        'weekday': weekday,
        'ip': ip_address,
        'user_agent': user_agent,
        'device_id': device_id
    }

    # ✅ Analyze this login attempt BEFORE saving it
    summary, severity = analyze_login_with_chatgpt(DATA_FILE, target_user=username, current_login=current_login)

    # ✅ Append to CSV AFTER analysis to avoid polluting the history
    new_entry = pd.DataFrame([current_login])
    file_exists = os.path.exists(DATA_FILE)
    new_entry.to_csv(DATA_FILE, mode='a', header=not file_exists, index=False)

    # ✅ Show the results
    return render_template("success.html",
                           username=username,
                           hour=hour,
                           weekday=weekday,
                           ip=ip_address,
                           summary=summary,
                           severity=severity)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

