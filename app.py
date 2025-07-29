import subprocess
import time
import requests
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

# MySQL config
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "password123",
    "database": "ajazz_products"
}

# Local AI API config
AI_API_URL = "http://localhost:1234/v1/chat/completions"
AI_MODEL = "falcon-h1-7b-instruct"

def start_localtunnel():
    print("\n🚀 Starting LocalTunnel...")
    subprocess.Popen(
        ["lt", "--port", "5000", "--subdomain", "insta947x-donkey-haxx-flipflop-b4nanalord-neverguess567"],
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )
    time.sleep(4)
    print("✅ Public URL: https://insta947x-donkey-haxx-flipflop-b4nanalord-neverguess567.loca.lt\n")

def ask_ai(messages):
    response = requests.post(AI_API_URL, json={
        "model": AI_MODEL,
        "messages": messages,
        "temperature": 0.5
    })
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def classify_user_message(user_message):
    system_prompt = (
        "Classify the user message strictly into one of the following:\n"
        "- 'PRODUCT' if it's about Ajazz hardware products (keyboards, mice, headphones, peripherals, accessories)\n"
        "- 'GREETING' if it's a friendly greeting\n"
        "- 'OTHER' for everything else"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    classification = ask_ai(messages).strip().upper()
    return classification

def describe_and_select_all(cursor, table_names):
    all_results = []
    for table in table_names:
        try:
            cursor.execute(f"DESCRIBE {table};")
            cursor.fetchall()  # discard structure
            cursor.execute(f"SELECT * FROM {table};")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            for row in rows:
                all_results.append(dict(zip(columns, row)))
        except Exception as e:
            print(f"⚠️ Skipping table {table} due to error: {e}")
    return all_results

def generate_answer_from_db(db_results_text, user_message):
    if db_results_text.strip().lower() == "no results found.":
        return "Sorry, no matching product was found in the database."

    system_prompt = (
        "You are a helpful product assistant.\n"
        "Use ONLY the provided database results to respond to the user's question.\n"
        "Do not invent or assume details not present.\n"
        f"User question: {user_message}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": db_results_text}
    ]
    return ask_ai(messages)

def generate_greeting():
    return "Hello! I'm your Ajazz assistant. You can ask me about Ajazz products like keyboards, mice, and other accessories."

def generate_direct_answer():
    return "I am only designed to answer Ajazz's product-related queries only."

@app.route('/query', methods=['POST'])
def handle_query():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)
    if not data or "customer_message" not in data:
        return jsonify({"error": "Missing 'customer_message' field"}), 400

    customer_message = data["customer_message"]
    print(f"\n💬 Customer Message: {customer_message}")

    try:
        classification = classify_user_message(customer_message)
        print(f"🔎 Message Type: {classification}")

        if classification == "GREETING":
            answer = generate_greeting()
            print(f"🤖 AI Greeting Answer:\n{answer}")
            return jsonify({"answer": answer})

        if classification != "PRODUCT":
            answer = generate_direct_answer()
            print(f"🤖 AI direct answer:\n{answer}")
            return jsonify({"answer": answer})

        # Connect and fetch from all product tables
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES;")
        table_rows = cursor.fetchall()
        table_names = [row[0] for row in table_rows]

        results = describe_and_select_all(cursor, table_names)

        cursor.close()
        conn.close()

        if not results:
            db_results_text = "No results found."
        else:
            db_results_text = "\n".join(str(r) for r in results)

        print("\n📊 Database Returned Results:")
        for row in results:
            print(row)

        final_answer = generate_answer_from_db(db_results_text, customer_message)
        print(f"\n🤖 AI final answer:\n{final_answer}")

        return jsonify({"answer": final_answer})

    except mysql.connector.Error as e:
        print(f"❌ MySQL Error: {str(e)}")
        return jsonify({"answer": "An internal error occurred. Please try again later."}), 500
    except Exception as e:
        print(f"❌ Server Exception: {str(e)}")
        return jsonify({"answer": "An internal error occurred. Please try again later."}), 500

if __name__ == "__main__":
    start_localtunnel()
    app.run(host="0.0.0.0", port=5000)
