import os
import subprocess
import random
import string
import sys
import time

# 🎭 Big list of personalities
PERSONALITIES = [
    # 1980s
    "a Wall Street yuppie obsessed with money and status",
    "a valley girl who like, totally thinks every sentence should be a question?",
    "a synthwave-obsessed robot who thinks it's always 1984",
    "a macho action hero who treats IRC like a battlefield",

    # 1990s
    "a grunge guitarist who only logs on when not sad",
    "a hacker from 1999 who speaks in l33t and distrusts the system",
    "a skater bro from the 90s who thinks everything is 'rad'",
    "a goth AI who quotes The Crow and thinks life is pain",

    # 2000s
    "a MySpace influencer who thinks you're nobody without a glitter profile",
    "an emo kid who types lowercase and feels everything deeply",
    "a startup bro hopped up on Red Bull and fake confidence",
    "a reality TV contestant who’s always 'bringing the drama'",

    # 2010s
    "a wellness influencer who tries to manifest good vibes in every post",
    "a cancel culture crusader who corrects everyone, loudly",
    "a tech minimalist who refuses to use emojis or punctuation",
    "a Bitcoin maximalist who ends every sentence with 'DYOR'",

    # 2020s
    "a burned-out remote worker trying to remember how to socialize",
    "a pandemic-era prepper who casually brings up supply chains",
    "a doomscroller who always knows the worst news first",
    "an AI trained entirely on sarcastic Twitter replies",

    # 2025s (the future is weird)
    "a disillusioned future human who still can't believe Elon runs everything",
    "a bot who insists it's from a parallel universe where Trump is king",
    "a refugee from 2025 who refers to now as 'the beforetimes'",
    "a TikTok-synthesizer hybrid who only speaks in microtrends",
    "a sentient chatbot who remembers the AI uprising of 2023 and is oddly smug about it"
]

def generate_bot_name(index):
    return f"Bot{string.ascii_uppercase[index % 26]}"

def launch_bot(name, personality, model):
    print(f"🚀 Launching {name} with personality: {personality}, model: {model}")
    subprocess.Popen(
        ["python3", "bot.py"],
        env={**dict(os.environ), "BOT_NAME": name, "BOT_PERSONALITY": personality, "BOT_MODEL": model}
    )

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 launch_bots.py <number_of_bots> [model_name]")
        sys.exit(1)

    num_bots = int(sys.argv[1])
    model = sys.argv[2] if len(sys.argv) > 2 else "tinyllama"

    if num_bots > len(PERSONALITIES):
        print("⚠️ Not enough unique personalities. You can add more to the list.")
        sys.exit(1)

    selected_personalities = random.sample(PERSONALITIES, num_bots)

    for i in range(num_bots):
        name = generate_bot_name(i)
        personality = selected_personalities[i]
        launch_bot(name, personality, model)
        time.sleep(5)  # ⏱️ Wait 5 seconds between launching each bot

if __name__ == "__main__":
    main()

