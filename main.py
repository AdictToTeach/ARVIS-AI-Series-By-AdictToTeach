import speech_recognition as sr
import time
from openai import OpenAI
import os 
from gtts import gTTS 
from dotenv import load_dotenv 
import pygame 
# Import the new advanced UI
from jarvis_display import get_jarvis_display 

# --- UI Initialization ---
print("Initializing Advanced HUD Interface...")
time.sleep(1.5) 
JARVIS_UI = get_jarvis_display()

if not JARVIS_UI:
    print("FATAL ERROR: Jarvis Display failed to initialize.")
else:
    # State 0: Blue (Idle)
    JARVIS_UI.set_state(0, "SYSTEM ONLINE")


# --- API CONFIGURATION ---
load_dotenv() 
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("Error: API Key missing.")
    exit()

llm_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
LLM_MODEL = "mistralai/mistral-7b-instruct-v0.2"

# --- AUDIO SETUP ---
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=24000) 
except Exception as e:
    print(f"Mixer Error: {e}")

def speak(text):
    # State 2: Red (Speaking)
    if JARVIS_UI: JARVIS_UI.set_state(2, "PROCESSING DATA")
    
    print(f"JARVIS: {text}") 
    filename = "output.mp3"
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)
        
        if pygame.mixer.get_init():
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1) 
            pygame.mixer.music.unload() 
    except Exception as e:
        print(f"TTS Error: {e}")
    finally:
        if os.path.exists(filename):
            try: os.remove(filename)
            except: pass
    
    # Wapas Idle State par aana
    if JARVIS_UI: JARVIS_UI.set_state(0, "AWAITING INPUT")

def process_with_llm(user_prompt):
    try:
        system_message = "You are JARVIS. Respond concisely in Hinglish/English."
        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": system_message},
                      {"role": "user", "content": user_prompt}],
            temperature=0.7, max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return "System Error."

def listen_wake_word():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        # State 0: Idle
        if JARVIS_UI: JARVIS_UI.set_state(0, "WAITING FOR WAKE WORD")
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            word = recognizer.recognize_google(audio, language='en-in')
            if "jarvis" in word.lower(): return True
        except: pass
        return False

def take_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        # State 1: Orange (Active Listening)
        if JARVIS_UI: JARVIS_UI.set_state(1, "LISTENING ACTIVE")
        print("Command...")
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio, language='en-in')
        except: return "timeout"

if __name__ == "__main__":
    speak("Visual Interface Loaded. Systems Online.")
    while True:
        try:
            if listen_wake_word():
                speak("Yes Sir?")
                while True:
                    cmd = take_command()
                    if "goodbye" in cmd.lower() or "sleep" in cmd.lower():
                        speak("Shutting down protocols.")
                        if JARVIS_UI: JARVIS_UI.stop_loop()
                        break
                    elif cmd in ["timeout", "unrecognized"]:
                        continue
                    else:
                        speak("Processing...")
                        reply = process_with_llm(cmd)
                        speak(reply)
                        
        except KeyboardInterrupt:
            if JARVIS_UI: JARVIS_UI.stop_loop()
            break