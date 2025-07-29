import tkinter as tk
from tkinter import scrolledtext
import requests
import threading
import time

SERVER_URL = ""

last_query = None

def send_query_to_server(query, display_area, retry_button=None):
    global last_query
    last_query = query

    if retry_button:
        retry_button.config(state=tk.DISABLED)

    display_area.insert(tk.END, f"\nYou: {query}\n", "user")
    display_area.see(tk.END)

    display_area.insert(tk.END, "🤖 AI: AI is processing your request", "processing")
    processing_line_index = display_area.index("end-1l")

    stop_animation = [False]
    patience_message_added = [False]

    def animate_dots():
        dot_count = 0
        elapsed = 0
        while not stop_animation[0]:
            dots = "." * (dot_count % 4)
            dot_count += 1
            display_area.delete(processing_line_index, f"{processing_line_index} lineend")
            display_area.insert(processing_line_index, f"🤖 AI: AI is processing your request{dots}", "processing")
            display_area.see(tk.END)

            elapsed += 0.5
            if elapsed >= 15 and not patience_message_added[0]:
                display_area.insert(tk.END, "\n🤖 AI: This may take a little longer, please be patient...\n", "info")
                display_area.see(tk.END)
                patience_message_added[0] = True

            time.sleep(0.5)

    def get_response():
        error_occurred = False
        answer = ""
        try:
            response = requests.post(SERVER_URL, json={"customer_message": query}, timeout=(120, 1800))
            response.raise_for_status()
            data = response.json()
            answer = data.get("answer", "❌ The assistant could not process your request.")
        except requests.exceptions.Timeout:
            answer = "❌ Request timed out. Please try again shortly."
            error_occurred = True
        except requests.exceptions.ConnectionError:
            answer = "❌ Unable to connect to the assistant. Please check your internet connection or try again later."
            error_occurred = True
        except requests.exceptions.HTTPError:
            answer = "❌ Something went wrong on the server. Please try again later."
            error_occurred = True
        except Exception:
            answer = "❌ An unexpected error occurred. Please try again later."
            error_occurred = True

        stop_animation[0] = True
        display_area.delete(processing_line_index, f"{processing_line_index} lineend")

        # 🧹 Remove "please be patient" line if present
        if patience_message_added[0]:
            lines = display_area.get("1.0", tk.END).splitlines()
            for i in range(len(lines) - 1, -1, -1):
                if "This may take a little longer" in lines[i]:
                    display_area.delete(f"{i+1}.0", f"{i+2}.0")
                    break

        display_area.insert(processing_line_index, f"🤖 AI: {answer}\n", "ai")
        display_area.see(tk.END)

        if retry_button:
            retry_button.config(state=tk.NORMAL if error_occurred else tk.DISABLED)

    threading.Thread(target=animate_dots, daemon=True).start()
    threading.Thread(target=get_response, daemon=True).start()

def on_submit(entry_field, display_area, retry_button):
    query = entry_field.get().strip()
    if query.lower() in ['exit', 'quit']:
        root.destroy()
        return
    if query == "":
        display_area.insert(tk.END, "⚠️ Please enter a non-empty query.\n", "error")
        return
    entry_field.delete(0, tk.END)
    send_query_to_server(query, display_area, retry_button)

# GUI Setup
root = tk.Tk()
root.title("Ajazz Product Assistant")
root.resizable(False, False)

frame = tk.Frame(root, bg="#f4f4f4")
frame.pack(padx=10, pady=10)

display_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=25, width=80, font=("Consolas", 10), bg="white")
display_area.pack(pady=(0, 10))

# Styling
display_area.tag_config("user", foreground="blue", font=("Consolas", 10, "bold"))
display_area.tag_config("ai", foreground="green", font=("Consolas", 10))
display_area.tag_config("error", foreground="red", font=("Consolas", 10, "italic"))
display_area.tag_config("processing", foreground="gray", font=("Consolas", 10, "italic"))
display_area.tag_config("info", foreground="#cc8800", font=("Consolas", 10, "italic"))

entry_field = tk.Entry(frame, width=65, font=("Consolas", 10))
entry_field.pack(side=tk.LEFT, padx=(0, 10))

submit_button = tk.Button(frame, text="Send", width=10, bg="#007acc", fg="white")
submit_button.pack(side=tk.LEFT)

# 🔁 Retry button - styled boldly
retry_button = tk.Button(
    frame,
    text="Retry Request",
    width=14,
    bg="#ffffff",
    fg="white",
    font=("Consolas", 10, "bold"),
    state=tk.DISABLED
)
retry_button.pack(side=tk.LEFT, padx=(10, 0))

entry_field.bind("<Return>", lambda event: on_submit(entry_field, display_area, retry_button))
submit_button.config(command=lambda: on_submit(entry_field, display_area, retry_button))

def on_retry():
    if last_query:
        send_query_to_server(last_query, display_area, retry_button)

retry_button.config(command=on_retry)

# Initial message
display_area.insert(tk.END, "🔍 Ask any Ajazz product-related question. Type 'exit' or 'quit' to close.\n", "ai")

root.mainloop()
