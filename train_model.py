import pandas as pd
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_login_with_chatgpt(csv_path, target_user, current_login):
    if not os.path.exists(csv_path):
        return "No login data found.", "N/A"

    df = pd.read_csv(csv_path)

    if df.empty:
        return "No login entries in CSV file.", "N/A"

    # ✅ STEP 1: Filter only logins from the specified user
    user_df = df[df['username'] == target_user]

    # ✅ STEP 2: If no login history, return first-time message
    if user_df.empty:
        return (
            f"🧠 AI Summary\n"
            f"**Severity Rating:** High\n"
            f"**Summary:** This is {target_user}'s first login attempt. No history to compare against.",
            "High"
        )

    # ✅ STEP 3: Sort by timestamp if available
    if 'timestamp' in user_df.columns:
        user_df = user_df.sort_values(by='timestamp')

    # ✅ STEP 4: Build login summaries (historical logins only)
    login_summaries = ""
    for i, row in user_df.iterrows():
        login_summaries += (
            f"Login #{i + 1}:\n"
            f"  - Hour: {row['hour']}\n"
            f"  - Weekday: {row['weekday']}\n"
            f"  - IP Address: {row['ip']}\n"
            f"  - User Agent: {row['user_agent']}\n"
            f"  - Device ID: {row['device_id']}\n\n"
        )

    # ✅ STEP 5: Add the current login attempt separately
    new_login_block = (
        "Most Recent Login Attempt:\n"
        f"  - Hour: {current_login['hour']}\n"
        f"  - Weekday: {current_login['weekday']}\n"
        f"  - IP Address: {current_login['ip']}\n"
        f"  - User Agent: {current_login['user_agent']}\n"
        f"  - Device ID: {current_login['device_id']}\n"
    )

    # ✅ STEP 6: Build prompt for GPT
    full_prompt = (
        f"You are an AI security assistant reviewing login behavior logs for user: {target_user}.\n\n"
        "Below is this user's historical login data followed by the most recent login attempt.\n"
        "Each login includes the hour, weekday, IP address, user agent, and device ID.\n"
        "Analyze the latest login compared to the history and answer:\n"
        "1. Is it similar or different?\n"
        "2. Severity rating (Low / Medium / High)?\n"
        "3. Do you have enough data to be confident?\n\n"
        f"{login_summaries}"
        f"{new_login_block}\n\n"
        "Now give your summary and rating for the latest login:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a cybersecurity AI helping detect login anomalies."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3
        )

        reply = response.choices[0].message.content.strip()

        # Extract severity and summary
        severity_line = ""
        summary_block = ""

        for line in reply.splitlines():
            if "severity" in line.lower():
                severity_line = line.strip().replace("**", "").replace("Severity Rating:", "").strip()
            else:
                summary_block += line.strip() + " "

        formatted_summary = (
            f"🧠 AI Summary\n"
            f"**Severity Rating:** {severity_line or 'N/A'}\n"
            f"**Summary:** {summary_block.strip()}"
        )

        return formatted_summary, severity_line or "N/A"

    except Exception as e:
        return f"Error generating AI response: {str(e)}", "Error"
