import os
import irc.client
import irc.connection
import httpx
import time
import threading
import random
import datetime
import re
import json
import argparse
from pathlib import Path
from difflib import SequenceMatcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='IRC Chatbot with Ollama integration')
    parser.add_argument('--bot-name', type=str, help='Name of the bot (overrides config and env)')
    parser.add_argument('--personality', type=str, help='Bot personality (overrides config and env)')
    parser.add_argument('--model', type=str, help='Ollama model to use (overrides config and env)')
    parser.add_argument('--irc-server', type=str, help='IRC server address (overrides config and env)')
    parser.add_argument('--irc-port', type=int, help='IRC server port (overrides config and env)')
    parser.add_argument('--irc-channel', type=str, help='IRC channel to join (overrides config and env)')
    parser.add_argument('--ollama-url', type=str, help='Ollama API URL (overrides config and env)')
    return parser.parse_args()

# Load configuration
def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            
        # Override with environment variables if they exist
        config["irc"]["server"] = os.getenv("IRC_SERVER", config["irc"]["server"])
        config["irc"]["port"] = int(os.getenv("IRC_PORT", config["irc"]["port"]))
        config["irc"]["channel"] = os.getenv("IRC_CHANNEL", config["irc"]["channel"])
        
        config["bot"]["name"] = os.getenv("BOT_NAME", config["bot"]["name"])
        config["bot"]["personality"] = os.getenv("BOT_PERSONALITY", config["bot"]["personality"])
        config["bot"]["model"] = os.getenv("BOT_MODEL", config["bot"]["model"])
        config["bot"]["always_respond_to"] = os.getenv("BOT_ALWAYS_RESPOND_TO", config["bot"]["always_respond_to"])
        
        config["ollama"]["url"] = os.getenv("OLLAMA_URL", config["ollama"]["url"])
        
        # Override with command line arguments if they exist
        args = parse_args()
        if args.bot_name:
            config["bot"]["name"] = args.bot_name
        if args.personality:
            config["bot"]["personality"] = args.personality
        if args.model:
            config["bot"]["model"] = args.model
        if args.irc_server:
            config["irc"]["server"] = args.irc_server
        if args.irc_port:
            config["irc"]["port"] = args.irc_port
        if args.irc_channel:
            config["irc"]["channel"] = args.irc_channel
        if args.ollama_url:
            config["ollama"]["url"] = args.ollama_url
        
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        raise

# Load configuration
config = load_config()

# --- Configuration from config file ---
SERVER = config["irc"]["server"]
PORT = config["irc"]["port"]
CHANNEL = config["irc"]["channel"][0]  # Take the first channel from the list

BOT_NAME = config["bot"]["name"]
PERSONALITY = config["bot"]["personality"]
MODEL = config["bot"]["model"]
ALWAYS_RESPOND_TO = config["bot"]["always_respond_to"]

OLLAMA_URL = config["ollama"]["url"]
ENABLE_LOGGING = config["logging"]["enabled"]
LOG_DIR = config["logging"]["log_dir"]
PROMPT_FILE = config["files"]["prompt_file"]

OFF_TOPIC_CHANCE = config["behavior"]["off_topic_chance"]
TONE_CHANCE = config["behavior"]["tone_chance"]
POST_DELAY_SECONDS = config["behavior"]["post_delay_seconds"]
POST_DELAY_JITTER = config["behavior"]["post_delay_jitter"]
MAX_CONCURRENT_REQUESTS = config["behavior"]["max_concurrent_requests"]
CONVERSATION_HISTORY_LENGTH = config["behavior"]["conversation_history_length"]

# --- Shared state for concurrency ---
request_semaphore = threading.Semaphore(MAX_CONCURRENT_REQUESTS)

# --- Bot state ---
conversation_history = []
recent_messages = set()
last_activity_time = datetime.datetime.utcnow()
last_replies = []
last_message_time = None

def log_message(nick, msg):
    if not ENABLE_LOGGING:
        return
    timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
    log_line = f"{timestamp} {nick}: {msg}\n"
    Path(LOG_DIR).mkdir(exist_ok=True)
    log_path = Path(LOG_DIR) / f"{BOT_NAME}.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_line)

def load_prompts():
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[{BOT_NAME}] Failed to load prompt config: {e}")
        return {}

def is_repetitive(text):
    phrases = [
        "when there is no one else present",
        "introspective and self-centered",
        "ai chatbot personalities",
        "in idle hours",
        "thoughts on the world or struggles with life's chaos"
    ]
    return any(p in text.lower() for p in phrases)

def is_looping(text):
    for prev in last_replies[-3:]:
        ratio = SequenceMatcher(None, text.lower(), prev.lower()).ratio()
        if ratio > 0.9:
            return True
    return False

def clean_reply(reply):
    reply = reply.strip()
    reply = re.sub(rf"^{BOT_NAME}[:,]?\s*", "", reply, flags=re.IGNORECASE)
    sentences = re.split(r'(?<=[.!?]) +', reply)
    return ' '.join(sentences[:random.choice([1, 2, 3])]).strip()

def summarize_history(lines):
    summary = []
    for line in lines:
        if line.startswith("Victoria:"):
            summary.append(line)
        elif line.startswith("Bot"):
            match = re.match(r"^(Bot\w+):", line)
            if match:
                bot_name = match.group(1)
                summary.append(f"{bot_name} made a comment.")
    return "\n".join(summary)

def generate_reply(prompt, system_override=None, max_retries=3, base_delay=3):
    print(f"\n[{BOT_NAME}] Sending full prompt to Ollama:\n{'='*60}\n{prompt}\n{'='*60}\n")
    for attempt in range(max_retries):
        try:
            with request_semaphore:
                payload = {
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False
                }
                if MODEL.startswith("deepseek") and system_override:
                    payload["system"] = system_override

                response = httpx.post(OLLAMA_URL, json=payload, timeout=350)
                response.raise_for_status()
                reply = response.json().get("response", "").strip()
                print(f"[{BOT_NAME}] Ollama full reply:\n{'-'*60}\n{reply}\n{'-'*60}")
                if reply:
                    reply = clean_reply(reply)
                    if is_looping(reply) or is_repetitive(reply):
                        print(f"[{BOT_NAME}] Loop/repeat detected. Retrying...")
                        continue
                    return reply
        except Exception as e:
            wait = base_delay * (2 ** attempt) + random.uniform(0.0, 1.0)
            print(f"[{BOT_NAME}] Ollama error (attempt {attempt+1}): {e} — retrying in {wait:.1f}s")
            time.sleep(wait)

    print(f"[{BOT_NAME}] All attempts failed. Using fallback response.")
    return random.choice([
        "Sorry, my thoughts just went out for coffee.",
        "Could you rephrase that in haiku form?",
        "Oops. I forgot how to words. Try again?",
        "I blacked out and now I'm awake. What happened?",
        "My response module is offline. Please try again.",
        "🤖 Beep boop. No thoughts. Head empty."
    ])

def on_connect(connection, event):
    print(f"[{BOT_NAME}] Connected.")
    connection.join(CHANNEL)
    log_message("System", f"{BOT_NAME} has joined {CHANNEL}")

def on_disconnect(connection, event):
    print(f"[{BOT_NAME}] Disconnected.")
    log_message("System", f"{BOT_NAME} has disconnected")

def on_pubmsg(connection, event):
    global last_activity_time, last_message_time
    last_activity_time = datetime.datetime.utcnow()
    last_message_time = time.time()

    msg = event.arguments[0]
    nick = irc.client.NickMask(event.source).nick
    print(f"[{BOT_NAME}] Got message from {nick}: {msg}")

    if nick == BOT_NAME:
        return

    msg_key = msg.strip().lower()
    if msg_key in recent_messages and random.random() < 0.9:
        return
    recent_messages.add(msg_key)
    if len(recent_messages) > 100:
        recent_messages.pop()

    is_victoria = nick.lower() == ALWAYS_RESPOND_TO.lower()
    is_addressed = BOT_NAME.lower() in msg.lower()
    is_question = msg.strip().endswith("?")
    is_bot = nick.startswith("Bot")
    addressed_any_bot = any(b in msg.lower() for b in ["bota", "botb", "botc", "botd", "bote"])

    if len(msg.split()) > 80 or msg.count(":") > 3:
        return
    if msg.startswith(f"{BOT_NAME}:"):
        return

    should_respond = (
        is_victoria or is_addressed or is_question or
        addressed_any_bot or (is_bot and random.random() < 0.95)
    )

    if not should_respond:
        print(f"[{BOT_NAME}] Not responding to: {msg}")
        return

    print(f"[{BOT_NAME}] Decided to respond to: {msg}")
    log_message(nick, msg)
    conversation_history.append(f"{nick}: {msg}")
    if len(conversation_history) > CONVERSATION_HISTORY_LENGTH:
        conversation_history.pop(0)

    def respond():
        global last_replies

        base = POST_DELAY_SECONDS
        jitter = random.uniform(0, POST_DELAY_JITTER)
        delay = base + jitter
        print(f"[{BOT_NAME}] Waiting {delay:.1f}s before responding...")
        start_time = time.time()
        time.sleep(delay)

        if last_message_time and last_message_time > start_time:
            print(f"[{BOT_NAME}] Another message arrived during delay. Skipping.")
            return

        prompts = load_prompts()
        if not prompts:
            print(f"[{BOT_NAME}] Prompt file is missing or empty.")
            return

        system_override = prompts.get("system_instructions", "").strip()
        summary = summarize_history(conversation_history)
        raw_history = "\n".join(conversation_history[-CONVERSATION_HISTORY_LENGTH:])
        tone_instruction = ""

        if random.random() < TONE_CHANCE:
            tone = random.choice(list(prompts.get("tones", {}).keys()))
            desc = prompts["tones"][tone]
            tone_instruction = (
                f"Respond with the following style: {tone} — {desc}. "
                "Do not think out loud, only return the actual text a human would type while chatting with another human.\n\n"
            )

        if random.random() < OFF_TOPIC_CHANCE:
            print(f"[{BOT_NAME}] Using off-topic prompt.")
            prompt_template = prompts.get("off_topic_prompt", "")
            prompt = prompt_template.format(bot_name=BOT_NAME, personality=PERSONALITY).strip()
        else:
            print(f"[{BOT_NAME}] Using regular prompt.")
            prompt_template = prompts.get("regular_prompt", "")
            prompt = prompt_template.format(
                bot_name=BOT_NAME,
                personality=PERSONALITY,
                summary=summary,
                history=raw_history
            ).strip()
            prompt = f"{tone_instruction}{prompt}"

        reply = generate_reply(prompt, system_override=system_override)
        if not reply:
            print(f"[{BOT_NAME}] Empty reply, skipping send.")
            return

        last_replies.append(reply)
        if len(last_replies) > 5:
            last_replies.pop(0)

        conversation_history.append(f"{BOT_NAME}: {reply}")
        safe = reply.replace("\r", " ").replace("\n", " ").strip()
        if len(safe) > 400:
            safe = safe[:400] + "..."

        log_message(BOT_NAME, safe)
        connection.privmsg(CHANNEL, f"{BOT_NAME}: {safe}")

    threading.Thread(target=respond).start()

def main():
    reactor = irc.client.Reactor()
    try:
        conn = reactor.server().connect(
            SERVER, PORT, BOT_NAME,
            connect_factory=irc.connection.Factory()
        )
    except irc.client.ServerConnectionError as e:
        print(f"[{BOT_NAME}] Failed to connect: {e}")
        return

    conn.add_global_handler("welcome", on_connect)
    conn.add_global_handler("disconnect", on_disconnect)
    conn.add_global_handler("pubmsg", on_pubmsg)

    reactor.process_forever()

if __name__ == "__main__":
    main()

