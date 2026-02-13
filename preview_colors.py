#!/usr/bin/env python3
"""Preview chat message colors"""

CHAT_USER_COLOR = '\033[96m'            # Bright cyan (label)
CHAT_AGENT_COLOR = '\033[92m'           # Bright green (label)
CHAT_USER_TEXT_COLOR = '\033[97m'       # Bright white (message - future use)
CHAT_AGENT_TEXT_COLOR = '\033[90m'      # Dim gray (message)
RESET = '\033[0m'

print("\n" + "="*60)
print("Chat Message Color Preview")
print("="*60 + "\n")

# Example conversation
print(f"{CHAT_USER_COLOR}You:{RESET} Hello! How can you help me today?")
print(f"\n{CHAT_AGENT_COLOR}Agent:{RESET} {CHAT_AGENT_TEXT_COLOR}I'm here to assist you with your questions and provide helpful information. What would you like to know?{RESET}")

print(f"\n{CHAT_USER_COLOR}You:{RESET} Tell me about Python programming.")
print(f"\n{CHAT_AGENT_COLOR}Agent:{RESET} {CHAT_AGENT_TEXT_COLOR}Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.{RESET}")

print(f"\n{CHAT_USER_COLOR}You:{RESET} That's great, thanks!")
print(f"\n{CHAT_AGENT_COLOR}Agent:{RESET} {CHAT_AGENT_TEXT_COLOR}You're welcome! Feel free to ask if you have more questions.{RESET}")

print("\n" + "="*60)
print("Color Legend:")
print("="*60)
print(f"{CHAT_USER_COLOR}■{RESET} User label: Bright cyan")
print(f"{CHAT_AGENT_COLOR}■{RESET} Agent label: Bright green")
print(f"{CHAT_AGENT_TEXT_COLOR}■{RESET} Agent message: Dim gray (subtle distinction)")
print(f"User input: Default terminal color (as typed)")
print("="*60 + "\n")
