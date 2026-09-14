import json
import os
import re
import subprocess
import threading
import time
import tkinter as tk
import urllib.parse
import webbrowser
import requests

# Safe Imports & Voice Setup
try:
    from gtts import gTTS
    import pygame

    OPENROUTER_API_KEY = "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"
    INITIALIZED = True
except Exception as e:
    print(f"Initialization Error: {e}")
    INITIALIZED = False

# --- Dark Theme Palette ---
COLOR_MAIN_BG = "#121316"       # Dark Background
COLOR_PANEL_BG = "#1a1c23"      # Panel Background
COLOR_CHAT_BG = "#16181d"       # Terminal Text Area
COLOR_INPUT_BG = "#22252e"      # Input Field Soft Dark
COLOR_TEXT_MAIN = "#e1e4ea"     # Primary Clean Text
COLOR_ACCENT_PURPLE = "#a78bfa" # Sakti AI Accent Color
COLOR_USER = "#60a5fa"          # User Accent Color
COLOR_VOICE_BTN = "#2a2e39"     # Voice Button BG

# --- Custom Typography & Fonts ---
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_SUBHEADER = ("Segoe UI", 9, "bold")
FONT_SENDER = ("Segoe UI Semibold", 11, "bold")
FONT_MSG = ("Segoe UI", 10)
FONT_INPUT = ("Segoe UI", 11)
FONT_BTN = ("Segoe UI", 10, "bold")


def draw_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Canvas par Smooth Rounded Rectangle draw karne ke liye helper function"""
    points = [
        x1 + radius, y1,
        x1 + radius, y1,
        x2 - radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)


def clean_text_for_speech(text):
    """Voice engine ke liye code blocks aur symbols remove karta hai"""
    text = re.sub(
        r"```[a-zA-Z]*.*?```",
        " Yahan code generated hai. ",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"[*#_~`>-]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def speak_async(text):
    """Google Voice (gTTS) in Clean Hindi via Background Thread"""

    def _speak():
        if not text:
            return
        clean_speech = clean_text_for_speech(text)
        temp_file = "temp_voice.mp3"
        try:
            tts = gTTS(text=clean_speech, lang="hi", slow=False)
            tts.save(temp_file)

            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            pygame.mixer.quit()

            if os.path.exists(temp_file):
                os.remove(temp_file)

        except Exception as e:
            print(f"Voice Error: {e}")

    threading.Thread(target=_speak, daemon=True).start()


def append_to_chat(sender, message, color="#ffffff", add_voice_btn=False):
    """GUI Terminal me text output show karna aur Voice Button attach karna"""
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, f"\n{sender}: ", "sender")
    chat_display.insert(tk.END, f"{message}\n", "msg")

    chat_display.tag_config("sender", foreground=color, font=FONT_SENDER)
    chat_display.tag_config("msg", foreground=COLOR_TEXT_MAIN, font=FONT_MSG)

    if add_voice_btn and message.strip():
        btn = tk.Button(
            chat_display,
            text="🔊 Listen Voice",
            font=FONT_BTN,
            bg=COLOR_VOICE_BTN,
            fg="#34d399",
            activebackground="#374151",
            activeforeground="#34d399",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            relief="flat",
            command=lambda t=message: speak_async(t),
        )
        chat_display.window_create(tk.END, window=btn)
        chat_display.insert(tk.END, "\n")

    chat_display.see(tk.END)
    chat_display.config(state=tk.DISABLED)


def execute_action(action_type, target=""):
    """System Tasks Execution based on Sakti AI decision"""
    if action_type == "open_youtube":
        if target:
            msg = f"YouTube khol raha hoon aur {target} search kar raha hoon."
            append_to_chat("🤖 SAKTI", msg, "#f87171", add_voice_btn=True)
            encoded_query = urllib.parse.quote(target)
            webbrowser.open(
                f"https://www.youtube.com/results?search_query={encoded_query}"
            )
        else:
            msg = "YouTube khol raha hoon."
            append_to_chat("🤖 SAKTI", msg, "#f87171", add_voice_btn=True)
            webbrowser.open("https://www.youtube.com")

    elif action_type in ["open_sklauncher", "open_minecraft"]:
        msg = "SKLauncher open kar raha hoon bhai."
        append_to_chat("🤖 SAKTI", msg, COLOR_USER, add_voice_btn=True)
        try:
            sk_dir = r"E:\sklauncher\jre\bin"
            sklauncher_exe = os.path.join(sk_dir, "SKlauncher.exe")
            java_exe = os.path.join(sk_dir, "javaw.exe")
            sk_jar = r"E:\sklauncher\SKlauncher.jar"

            if os.path.exists(sklauncher_exe):
                os.startfile(sklauncher_exe)
            elif os.path.exists(java_exe) and os.path.exists(sk_jar):
                subprocess.Popen([java_exe, "-jar", sk_jar])
            else:
                err = f"SKLauncher file missing in: {sk_dir}"
                append_to_chat("⚠️ ERROR", err, "#f87171")
        except Exception as e:
            append_to_chat("⚠️ ERROR", f"Launch error: {e}", "#f87171")

    elif action_type == "open_chrome":
        msg = "Google Chrome khol raha hoon."
        append_to_chat("🤖 SAKTI", msg, COLOR_USER, add_voice_btn=True)
        webbrowser.open("https://www.google.com")

    elif action_type == "open_notepad":
        msg = "Notepad open kar raha hoon."
        append_to_chat("🤖 SAKTI", msg, "#fbbf24", add_voice_btn=True)
        os.system("notepad")

    elif action_type == "open_calculator":
        msg = "Calculator open kar raha hoon."
        append_to_chat("🤖 SAKTI", msg, "#fbbf24", add_voice_btn=True)
        os.system("calc")


def process_query_thread(user_input):
    """Direct local bypass & AI API call via OpenRouter"""
    cmd = user_input.lower().strip()

    if "sklauncher" in cmd or "minecraft" in cmd:
        execute_action("open_sklauncher")
        status_label.config(text="● SYSTEM ONLINE", fg="#34d399")
        return
    elif "chrome" in cmd:
        execute_action("open_chrome")
        status_label.config(text="● SYSTEM ONLINE", fg="#34d399")
        return
    elif "notepad" in cmd:
        execute_action("open_notepad")
        status_label.config(text="● SYSTEM ONLINE", fg="#34d399")
        return
    elif "calc" in cmd or "calculator" in cmd:
        execute_action("open_calculator")
        status_label.config(text="● SYSTEM ONLINE", fg="#34d399")
        return

    try:
        system_prompt = """Analyze the user command and reply strictly in valid JSON format:
{
  "intent": "action" OR "chat",
  "action_type": "open_youtube" / "open_minecraft" / "open_sklauncher" / "open_chrome" / "open_notepad" / "open_calculator" / "none",
  "search_target": "search query if user wants to play/search a video on YouTube, otherwise empty string",
  "ai_response": "Short answer in conversational Hindi or complete code if requested"
}

Rules:
1. If the user wants to play a video or search YouTube, intent is "action", action_type is "open_youtube", search_target is query.
2. If user wants to open local software, mark appropriate action_type.
3. Write ai_response in simple conversational Hinglish/Hindi. Return ONLY raw JSON without markdown codeblocks."""

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            "temperature": 0.3,
        }

        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15,
        )

        if res.status_code == 200:
            raw_text = res.json()["choices"][0]["message"]["content"].strip()
            raw_text = re.sub(r"^```json\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            data = json.loads(raw_text)

            intent = data.get("intent", "chat")
            action_type = data.get("action_type", "none")
            search_target = data.get("search_target", "")
            ai_response = data.get("ai_response", "")

            if intent == "action" and action_type != "none":
                execute_action(action_type, search_target)
            else:
                append_to_chat(
                    "🤖 SAKTI", ai_response, COLOR_ACCENT_PURPLE, add_voice_btn=True
                )
        else:
            append_to_chat(
                "🤖 SAKTI ERROR",
                f"API Error {res.status_code}: {res.text}",
                "#f87171",
            )

    except Exception as e:
        append_to_chat("🤖 SAKTI ERROR", f"Processing error: {e}", "#f87171")

    status_label.config(text="● SYSTEM ONLINE", fg="#34d399")


def on_user_submit(event=None):
    user_input = user_entry.get().strip()
    if not user_input:
        return

    user_entry.delete(0, tk.END)
    append_to_chat("👤 YOU", user_input, COLOR_USER)
    status_label.config(text="● PROCESSING...", fg="#fbbf24")

    threading.Thread(
        target=process_query_thread, args=(user_input,), daemon=True
    ).start()


# --- GUI WINDOW BUILD ---

root = tk.Tk()
root.title("SAKTI AI TERMINAL")
root.geometry("720x780")
root.config(bg=COLOR_MAIN_BG)
root.resizable(True, True)

# Header Panel
header_frame = tk.Frame(root, bg=COLOR_PANEL_BG, pady=12)
header_frame.pack(fill=tk.X)

title_label = tk.Label(
    header_frame,
    text="⚡ SAKTI AI ⚡",
    font=FONT_HEADER,
    fg=COLOR_ACCENT_PURPLE,
    bg=COLOR_PANEL_BG,
)
title_label.pack()

status_label = tk.Label(
    header_frame,
    text="● SYSTEM ONLINE",
    font=FONT_SUBHEADER,
    fg="#34d399",
    bg=COLOR_PANEL_BG,
)
status_label.pack(pady=2)

# Chat Terminal Outer Canvas (Smooth Rounded Container)
chat_outer_frame = tk.Frame(root, bg=COLOR_MAIN_BG)
chat_outer_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

chat_canvas = tk.Canvas(
    chat_outer_frame, bg=COLOR_MAIN_BG, bd=0, highlightthickness=0
)
chat_canvas.pack(fill=tk.BOTH, expand=True)


def update_chat_shape(event):
    chat_canvas.delete("bg_rect")
    w, h = event.width, event.height
    draw_rounded_rect(
        chat_canvas,
        2,
        2,
        w - 2,
        h - 2,
        radius=25,
        fill=COLOR_CHAT_BG,
        outline="",
        tags="bg_rect",
    )


chat_canvas.bind("<Configure>", update_chat_shape)

# Scrollbar & Chat Text Inside Rounded Canvas
scrollbar = tk.Scrollbar(chat_canvas, bd=0)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=12, padx=5)

chat_display = tk.Text(
    chat_canvas,
    bg=COLOR_CHAT_BG,
    fg=COLOR_TEXT_MAIN,
    font=FONT_MSG,
    yscrollcommand=scrollbar.set,
    wrap=tk.WORD,
    bd=0,
    highlightthickness=0,
    padx=20,
    pady=15,
)
chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
scrollbar.config(command=chat_display.yview)
chat_display.config(state=tk.DISABLED)

# Input Command Panel Container
input_outer_frame = tk.Frame(root, bg=COLOR_MAIN_BG, pady=10, padx=20)
input_outer_frame.pack(fill=tk.X)

# Rounded Entry Canvas
entry_canvas = tk.Canvas(
    input_outer_frame, height=48, bg=COLOR_MAIN_BG, bd=0, highlightthickness=0
)
entry_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))


def update_entry_shape(event):
    entry_canvas.delete("bg_rect")
    w, h = event.width, event.height
    draw_rounded_rect(
        entry_canvas,
        2,
        2,
        w - 2,
        h - 2,
        radius=20,
        fill=COLOR_INPUT_BG,
        outline="",
        tags="bg_rect",
    )


entry_canvas.bind("<Configure>", update_entry_shape)

user_entry = tk.Entry(
    entry_canvas,
    bg=COLOR_INPUT_BG,
    fg=COLOR_TEXT_MAIN,
    insertbackground=COLOR_ACCENT_PURPLE,
    font=FONT_INPUT,
    bd=0,
    highlightthickness=0,
    relief=tk.FLAT,
)
entry_canvas.create_window(15, 24, window=user_entry, anchor="w", width=480)
user_entry.bind("<Return>", on_user_submit)
user_entry.focus()

# Rounded Run Button Canvas
btn_canvas = tk.Canvas(
    input_outer_frame,
    width=90,
    height=48,
    bg=COLOR_MAIN_BG,
    bd=0,
    highlightthickness=0,
)
btn_canvas.pack(side=tk.RIGHT)

draw_rounded_rect(
    btn_canvas,
    2,
    2,
    88,
    46,
    radius=20,
    fill=COLOR_ACCENT_PURPLE,
    outline="",
)

send_button = tk.Button(
    btn_canvas,
    text="RUN ↵",
    command=on_user_submit,
    font=FONT_BTN,
    bg=COLOR_ACCENT_PURPLE,
    fg="#121316",
    activebackground=COLOR_ACCENT_PURPLE,
    activeforeground="#121316",
    bd=0,
    relief="flat",
    cursor="hand2",
)
btn_canvas.create_window(45, 24, window=send_button)

# Startup Message
append_to_chat(
    "🤖 SAKTI",
    "Sakti AI Terminal ready. Main aapki kya madad kar sakta hoon, Bhai?",
    COLOR_ACCENT_PURPLE,
    add_voice_btn=True,
)

root.mainloop()
