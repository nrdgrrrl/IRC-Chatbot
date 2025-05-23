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
import hashlib

# Load environment variables
load_dotenv()

# Global state for config and prompt reloading
config_hash = None
prompt_hash = None
config = None
prompts = None
last_config_check = 0
last_prompt_check = 0
CONFIG_CHECK_INTERVAL = 5  # Check for changes every 5 seconds

# Global variables for bot configuration
SERVER = None
PORT = None
CHANNEL = None
BOT_NAME = None
PERSONALITY = None
MODEL = None
ALWAYS_RESPOND_TO = None
OLLAMA_URL = None
ENABLE_LOGGING = None
LOG_DIR = None
PROMPT_FILE = None
OFF_TOPIC_CHANCE = None
TONE_CHANCE = None
POST_DELAY_SECONDS = None
POST_DELAY_JITTER = None
MAX_CONCURRENT_REQUESTS = None
CONVERSATION_HISTORY_LENGTH = None

def get_file_hash(filepath):
    """Get MD5 hash of a file's contents"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None

def reload_config():
    """Reload configuration from config.json"""
    global config, config_hash
    global SERVER, PORT, CHANNEL, BOT_NAME, PERSONALITY, MODEL, ALWAYS_RESPOND_TO
    global OLLAMA_URL, ENABLE_LOGGING, LOG_DIR, PROMPT_FILE
    global OFF_TOPIC_CHANCE, TONE_CHANCE, POST_DELAY_SECONDS, POST_DELAY_JITTER
    global MAX_CONCURRENT_REQUESTS, CONVERSATION_HISTORY_LENGTH
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            new_config = json.load(f)
            
        # Override with environment variables if they exist
        new_config["irc"]["server"] = os.getenv("IRC_SERVER", new_config["irc"]["server"])
        new_config["irc"]["port"] = int(os.getenv("IRC_PORT", new_config["irc"]["port"]))
        new_config["irc"]["channel"] = os.getenv("IRC_CHANNEL", new_config["irc"]["channel"])
        
        new_config["bot"]["name"] = os.getenv("BOT_NAME", new_config["bot"]["name"])
        new_config["bot"]["personality"] = os.getenv("BOT_PERSONALITY", new_config["bot"]["personality"])
        new_config["bot"]["model"] = os.getenv("BOT_MODEL", new_config["bot"]["model"])
        new_config["bot"]["always_respond_to"] = os.getenv("BOT_ALWAYS_RESPOND_TO", new_config["bot"]["always_respond_to"])
        
        new_config["ollama"]["url"] = os.getenv("OLLAMA_URL", new_config["ollama"]["url"])
        
        # Override with command line arguments if they exist
        args = parse_args()
        if args.bot_name:
            new_config["bot"]["name"] = args.bot_name
        if args.personality:
            new_config["bot"]["personality"] = args.personality
        if args.model:
            new_config["bot"]["model"] = args.model
        if args.irc_server:
            new_config["irc"]["server"] = args.irc_server
        if args.irc_port:
            new_config["irc"]["port"] = args.irc_port
        if args.irc_channel:
            new_config["irc"]["channel"] = args.irc_channel
        if args.ollama_url:
            new_config["ollama"]["url"] = args.ollama_url

        config = new_config
        config_hash = get_file_hash("config.json")
        print(f"[{new_config['bot']['name']}] Configuration reloaded successfully")
        
        # Update global variables
        SERVER = config["irc"]["server"]
        PORT = config["irc"]["port"]
        CHANNEL = config["irc"]["channel"][0]
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
        
    except Exception as e:
        print(f"Error reloading config: {e}")

def reload_prompts():
    """Reload prompts from prompts.json"""
    global prompts, prompt_hash
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            prompts = json.load(f)
        prompt_hash = get_file_hash(PROMPT_FILE)
        print(f"[{BOT_NAME}] Prompts reloaded successfully")
    except Exception as e:
        print(f"[{BOT_NAME}] Error reloading prompts: {e}")

def check_for_updates():
    """Check if config or prompts have changed and reload if necessary"""
    global last_config_check, last_prompt_check
    
    current_time = time.time()
    
    # Check config.json
    if current_time - last_config_check >= CONFIG_CHECK_INTERVAL:
        new_hash = get_file_hash("config.json")
        if new_hash and new_hash != config_hash:
            reload_config()
        last_config_check = current_time
    
    # Check prompts.json
    if current_time - last_prompt_check >= CONFIG_CHECK_INTERVAL:
        new_hash = get_file_hash(PROMPT_FILE)
        if new_hash and new_hash != prompt_hash:
            reload_prompts()
        last_prompt_check = current_time

# Initial load of config and prompts
reload_config()
reload_prompts()

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
last_activity_time = datetime.datetime.now(datetime.UTC)
last_replies = []
last_message_time = None
conversation_revival_thread = None
conversation_revival_running = False

def log_message(nick, msg):
    if not ENABLE_LOGGING:
        return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {nick}: {msg}\n"
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
    # Remove any leading/trailing whitespace
    reply = reply.strip()
    
    # Remove bot name prefix if it exists (case insensitive)
    reply = re.sub(rf"^{BOT_NAME}[:,]?\s*", "", reply, flags=re.IGNORECASE)
    
    # Remove any remaining bot name mentions
    reply = re.sub(rf"{BOT_NAME}[:,]?\s*", "", reply, flags=re.IGNORECASE)
    
    # Remove rule-like text
    rule_patterns = [
        r"Rules?:.*?(?=\n\n|\Z)",
        r"Instructions?:.*?(?=\n\n|\Z)",
        r"Guidelines?:.*?(?=\n\n|\Z)",
        r"RULES?:.*?(?=\n\n|\Z)",
        r"INSTRUCTIONS?:.*?(?=\n\n|\Z)",
        r"GUIDELINES?:.*?(?=\n\n|\Z)",
        r"Response:.*?(?=\n\n|\Z)",
        r"RESPONSE:.*?(?=\n\n|\Z)"
    ]
    for pattern in rule_patterns:
        reply = re.sub(pattern, "", reply, flags=re.IGNORECASE | re.DOTALL)
    
    # Split into sentences, but preserve emojis and special characters
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', reply)
    
    # If the reply is already short enough (under 400 chars), keep it intact
    if len(reply) <= 400:
        return reply
    
    # Otherwise, take 1-3 sentences while trying to preserve complete thoughts
    num_sentences = min(len(sentences), random.choice([1, 2, 3]))
    reply = ' '.join(sentences[:num_sentences]).strip()
    
    # If we still have room, try to include more of the response
    if len(reply) < 350 and len(sentences) > num_sentences:
        # Try to add one more sentence if it fits
        next_sentence = sentences[num_sentences]
        if len(reply + ' ' + next_sentence) <= 400:
            reply = reply + ' ' + next_sentence
    
    return reply

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
    print(f"\n[{BOT_NAME}] Sending prompt to Ollama:\n{'='*60}\n{prompt}\n{'='*60}\n")
    
    # First try to generate a response
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
            
            if not reply:
                print(f"[{BOT_NAME}] Empty reply from Ollama")
                return get_fallback_response()
            
            # Clean and validate the reply
            reply = clean_reply(reply)
            
            # If the reply is looping or repetitive, try to fix it without making another API call
            if is_looping(reply) or is_repetitive(reply):
                print(f"[{BOT_NAME}] Loop/repeat detected in response. Attempting to fix...")
                # Try to extract just the first unique sentence
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', reply)
                if sentences:
                    # Take the first sentence that isn't in the last replies
                    for sentence in sentences:
                        if not any(SequenceMatcher(None, sentence.lower(), prev.lower()).ratio() > 0.9 for prev in last_replies[-3:]):
                            reply = sentence.strip()
                            break
                    else:
                        # If all sentences are too similar, use a fallback
                        return get_fallback_response()
            
            print(f"[{BOT_NAME}] Ollama reply:\n{'-'*60}\n{reply}\n{'-'*60}")
            return reply
            
    except Exception as e:
        print(f"[{BOT_NAME}] Ollama error: {e}")
        return get_fallback_response()

def get_fallback_response():
    """Get a fallback response when generation fails"""
    return random.choice([
        "Sorry, my thoughts just went out for coffee.",
        "Could you rephrase that in haiku form?",
        "Oops. I forgot how to words. Try again?",
        "I blacked out and now I'm awake. What happened?",
        "My response module is offline. Please try again.",
        "🤖 Beep boop. No thoughts. Head empty."
    ])

def should_revive_conversation():
    """Check if enough time has passed to revive the conversation"""
    now = datetime.datetime.now(datetime.UTC)
    time_since_last_activity = (now - last_activity_time).total_seconds()
    # Base 3 minutes + random 2 minutes
    revival_threshold = 180 + random.uniform(0, 120)
    return time_since_last_activity > revival_threshold

def find_interesting_message():
    """Find an interesting message from history to respond to"""
    if not conversation_history:
        return None
    
    # Filter out bot messages and very short messages
    human_messages = [
        msg for msg in conversation_history 
        if not msg.startswith("Bot") and len(msg.split()) > 3
    ]
    
    if not human_messages:
        return None
    
    # Pick a random message from the last 10 messages
    recent_messages = human_messages[-10:]
    return random.choice(recent_messages)

def conversation_revival_loop(connection):
    """Background thread that monitors conversation activity and triggers responses"""
    global conversation_revival_running
    conversation_revival_running = True
    
    while conversation_revival_running:
        try:
            # Check for config/prompt updates
            check_for_updates()
            
            if should_revive_conversation():
                print(f"[{BOT_NAME}] Conversation has been quiet, attempting to revive...")
                
                # Find an interesting message to respond to
                message = find_interesting_message()
                if message:
                    # Add the message to conversation history if it's not already there
                    if message not in conversation_history:
                        conversation_history.append(message)
                    
                    # Generate a response
                    prompts = load_prompts()
                    if prompts:
                        system_override = prompts.get("system_instructions", "").strip()
                        summary = summarize_history(conversation_history)
                        raw_history = "\n".join(conversation_history[-CONVERSATION_HISTORY_LENGTH:])
                        
                        # Use a slightly modified prompt for revival
                        prompt_template = prompts.get("regular_prompt", "")
                        prompt = prompt_template.format(
                            bot_name=BOT_NAME,
                            personality=PERSONALITY,
                            summary=summary,
                            history=raw_history
                        ).strip()
                        
                        # Add a hint that we're reviving the conversation
                        prompt += "\n\nNote: The conversation has been quiet. Respond naturally to the last message, helping to revive the discussion."
                        
                        reply = generate_reply(prompt, system_override=system_override)
                        if reply:
                            safe = reply.replace("\r", " ").replace("\n", " ").strip()
                            if len(safe) > 400:
                                safe = safe[:400] + "..."
                            
                            log_message(BOT_NAME, safe)
                            connection.privmsg(CHANNEL, safe)
                            
                            # Update last activity time
                            global last_activity_time
                            last_activity_time = datetime.datetime.now(datetime.UTC)
            
            # Check every 30 seconds
            time.sleep(30)
            
        except Exception as e:
            print(f"[{BOT_NAME}] Error in conversation revival loop: {e}")
            time.sleep(30)  # Wait before retrying

def on_connect(connection, event):
    print(f"[{BOT_NAME}] Connected.")
    # Send USER command explicitly
    connection.send_raw(f"USER {BOT_NAME} 0 * :{PERSONALITY}")
    # Join channel after a short delay to ensure registration is complete
    time.sleep(1)
    connection.join(CHANNEL)
    log_message("System", f"{BOT_NAME} has joined {CHANNEL}")
    
    # Start the conversation revival thread
    global conversation_revival_thread
    if conversation_revival_thread is None or not conversation_revival_thread.is_alive():
        conversation_revival_thread = threading.Thread(
            target=conversation_revival_loop,
            args=(connection,),
            daemon=True
        )
        conversation_revival_thread.start()

def on_disconnect(connection, event):
    print(f"[{BOT_NAME}] Disconnected. Event: {event}")
    log_message("System", f"{BOT_NAME} has disconnected")
    
    # Stop the conversation revival thread
    global conversation_revival_running
    conversation_revival_running = False
    
    # Check if we should stop trying to reconnect
    if "Too many connections" in str(event) or "Connection limit exceeded" in str(event):
        print(f"[{BOT_NAME}] Server connection limit reached. Stopping reconnection attempts.")
        return
            
    # Try to reconnect after a delay
    time.sleep(5)
    try:
        print(f"[{BOT_NAME}] Attempting to reconnect to {SERVER}:{PORT}...")
        connection.connect(
            SERVER, PORT, BOT_NAME,
            connect_factory=irc.connection.Factory(),
            password=None,  # Add password here if needed
            username=BOT_NAME,
            ircname=PERSONALITY
        )
    except Exception as e:
        print(f"[{BOT_NAME}] Reconnection failed: {e}")

def on_pubmsg(connection, event):
    # Check for config/prompt updates before processing message
    check_for_updates()
    
    global last_activity_time, last_message_time
    last_activity_time = datetime.datetime.now(datetime.UTC)
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

    # Get response probabilities from config
    probs = config["behavior"]["response_probabilities"]
    
    # Determine message type and corresponding probability
    is_victoria = nick.lower() == ALWAYS_RESPOND_TO.lower()
    is_addressed = BOT_NAME.lower() in msg.lower()
    is_question = msg.strip().endswith("?")
    is_bot = nick.startswith("Bot")
    addressed_any_bot = any(b in msg.lower() for b in ["bota", "botb", "botc", "botd", "bote"])

    # Calculate response probability based on message type
    if is_victoria:
        response_prob = probs["always_respond_to"]
    elif is_addressed:
        response_prob = probs["addressed_directly"]
    elif is_question:
        response_prob = probs["question"]
    elif addressed_any_bot:
        response_prob = probs["addressed_any_bot"]
    elif is_bot:
        response_prob = probs["other_bot_message"]
    else:
        response_prob = probs["general_message"]

    if len(msg.split()) > 80 or msg.count(":") > 3:
        return
    if msg.startswith(f"{BOT_NAME}:"):
        return

    # Use the calculated probability to decide whether to respond
    if random.random() > response_prob:
        print(f"[{BOT_NAME}] Decided not to respond (probability: {response_prob:.2f})")
        return

    print(f"[{BOT_NAME}] Decided to respond (probability: {response_prob:.2f})")
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
        connection.privmsg(CHANNEL, safe)

    threading.Thread(target=respond).start()

def main():
    reactor = irc.client.Reactor()
    try:
        print(f"[{BOT_NAME}] Attempting to connect to {SERVER}:{PORT}...")
        conn = reactor.server().connect(
            SERVER, PORT, BOT_NAME,
            connect_factory=irc.connection.Factory(),
            password=None,  # Add password here if needed
            username=BOT_NAME,
            ircname=PERSONALITY
        )
        print(f"[{BOT_NAME}] Connection object created successfully")
    except irc.client.ServerConnectionError as e:
        print(f"[{BOT_NAME}] Failed to connect: {e}")
        return
    except Exception as e:
        print(f"[{BOT_NAME}] Unexpected error during connection: {e}")
        return

    def on_welcome(connection, event):
        print(f"[{BOT_NAME}] Received welcome event: {event}")
        on_connect(connection, event)

    def on_disconnect(connection, event):
        print(f"[{BOT_NAME}] Disconnected. Event: {event}")
        log_message("System", f"{BOT_NAME} has disconnected")
        
        # Check if we should stop trying to reconnect
        if "Too many connections" in str(event) or "Connection limit exceeded" in str(event):
            print(f"[{BOT_NAME}] Server connection limit reached. Stopping reconnection attempts.")
            return
            
        # Try to reconnect after a delay
        time.sleep(5)
        try:
            print(f"[{BOT_NAME}] Attempting to reconnect to {SERVER}:{PORT}...")
            connection.connect(
                SERVER, PORT, BOT_NAME,
                connect_factory=irc.connection.Factory(),
                password=None,  # Add password here if needed
                username=BOT_NAME,
                ircname=PERSONALITY
            )
        except Exception as e:
            print(f"[{BOT_NAME}] Reconnection failed: {e}")

    def on_error(connection, event):
        print(f"[{BOT_NAME}] Error event received: {event}")
        if "Too many connections" in str(event) or "Connection limit exceeded" in str(event):
            print(f"[{BOT_NAME}] Server connection limit reached. Please disconnect another bot first.")
            connection.disconnect()

    conn.add_global_handler("welcome", on_welcome)
    conn.add_global_handler("disconnect", on_disconnect)
    conn.add_global_handler("error", on_error)
    conn.add_global_handler("pubmsg", on_pubmsg)

    try:
        print(f"[{BOT_NAME}] Starting reactor...")
        reactor.process_forever()
    except KeyboardInterrupt:
        print(f"\n[{BOT_NAME}] Shutting down...")
        conn.disconnect()
    except Exception as e:
        print(f"[{BOT_NAME}] Error in main loop: {e}")
        conn.disconnect()

if __name__ == "__main__":
    main()

