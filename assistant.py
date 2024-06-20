import pyttsx3
import datetime
import speech_recognition as sr
import webbrowser
import wikipedia
import pyautogui
import os
import shlex
import subprocess
import threading
import sched, time

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('volume', 1)

scheduler = sched.scheduler(time.time, time.sleep)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def check_microphone():
    print("Checking microphone...")
    mics = sr.Microphone.list_microphone_names()
    if len(mics) == 0:
        print("No microphone detected. Please ensure a microphone is connected.")
        speak("No microphone detected. Please ensure a microphone is connected.")
        return False
    else:
        print("Available microphones:")
        for i, mic in enumerate(mics):
            print(f"Microphone {i+1}: {mic}")
        return True

def capture_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print("Listening...")
        try:
            audio = r.listen(source, timeout=5)  
            print("Audio captured.")
            return audio, r
        except sr.WaitTimeoutError:
            speak("Sorry, I didn't hear anything. Please try again.")
            return None, r
        except Exception as e:
            speak(f"Sorry, there was an error capturing audio: {str(e)}")
            return None, r

def recognize_speech(audio, recognizer):
    try:
        recognized_text = recognizer.recognize_google(audio, language="en-in")
        return recognized_text.lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return None
    except sr.RequestError:
        speak("Sorry, my speech service is down.")
        return None

def wish_me():
    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    elif 18 <= hour < 24:
        speak("Good Evening!")
    else:
        speak("Good Night!")
    
    speak("Hello, I am your assistant. How can I help you today?")

def perform_calculation(query):
    try:
        result = eval(query)
        speak(f"The result of {query} is {result}")
    except Exception as e:
        speak(f"Sorry, I encountered an error: {str(e)}. Please try again.")

def set_reminder(query):
    try:
        speak("When do you want me to remind you?")
        audio, recognizer = capture_audio()
        reminder_time = recognize_speech(audio, recognizer)
        
        if reminder_time:
            speak(f"Setting reminder for {reminder_time}.")
            reminder_thread = threading.Thread(target=remind_user, args=(reminder_time,))
            reminder_thread.start()
    except Exception as e:
        speak(f"Sorry, there was an error while setting the reminder: {str(e)}")

def remind_user(reminder_time):
    try:
        reminder_time_obj = datetime.datetime.strptime(reminder_time, "%H:%M")
        now = datetime.datetime.now()
        delta = (reminder_time_obj - now).total_seconds()
        
        if delta > 0:
            scheduler.enter(delta, 1, remind_callback, (reminder_time,))
            scheduler.run()
        else:
            speak("Sorry, the reminder time must be in the future.")
    
    except ValueError:
        speak("Sorry, I couldn't understand the time format.")

def remind_callback(reminder_time):
    speak(f"Reminder: It's {reminder_time}. Time to {get_random_reminder_message()}")

def open_website(query):
    speak("Which website do you want to open?")
    audio, recognizer = capture_audio()
    website = recognize_speech(audio, recognizer)
    if website:
        url = f"https://www.{website}.com"
        webbrowser.open(url)

def search_wikipedia(query):
    try:
        speak("Searching Wikipedia...")
        query = query.replace("wikipedia", "")
        result = wikipedia.summary(query, sentences=2)
        speak(f"According to Wikipedia: {result}")
    except wikipedia.exceptions.WikipediaException:
        speak("Sorry, I couldn't find any relevant information on Wikipedia.")

def take_screenshot():
    try:
        speak("Taking screenshot...")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot_path = f"screenshot_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        speak("Screenshot saved.")
        os.startfile(screenshot_path)  
    except Exception as e:
        speak(f"Sorry, an error occurred while taking the screenshot: {str(e)}")

def record_screen():
    try:
        speak("Recording screen... Say 'Stop Recording' to stop.")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_path = f"screen_record_{timestamp}.mp4"
        cmd = f"ffmpeg -y -f gdigrab -framerate 15 -i desktop -vcodec libx264 {video_path}"
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        while True:
            audio, recognizer = capture_audio()
            query = recognize_speech(audio, recognizer)
            if query and any(keyword in query for keyword in ["stop recording", "stop"]):
                process.terminate()
                speak("Screen recording stopped.")
                break
    except Exception as e:
        speak(f"Sorry, an error occurred while recording the screen: {str(e)}")

def google_search(query):
    try:
        speak("Opening Google search...")
        query = query.replace("google search", "")
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
    except Exception as e:
        speak(f"Sorry, an error occurred while performing Google search: {str(e)}")

def get_date():
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {current_date}")

def handle_query(query):
    query = query.lower()  
    
    if 'time' in query:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {current_time}")

    elif any(word in query for word in ['calculate', 'what is']):
        query = query.replace("calculate", "").replace("what is", "").strip()
        perform_calculation(query)

    elif 'reminder' in query:
        set_reminder(query)

    elif 'open website' in query:
        open_website(query)

    elif 'wikipedia' in query:
        search_wikipedia(query)

    elif 'screenshot' in query:
        take_screenshot()

    elif 'record screen' in query:
        record_screen()

    elif 'google search' in query:
        google_search(query)

    elif 'date' in query:
        get_date()

    elif 'exit' in query or 'bye' in query:
        speak("Goodbye!")
        return False

    else:
        speak("Sorry, I didn't understand that. Can you please repeat?")

    return True

if __name__ == "__main__":
    if not check_microphone():
        exit(1)
    
    wish_me()
    
    while True:
        audio, recognizer = capture_audio()

        try:
            query = recognize_speech(audio, recognizer)
            print("\nRecognized:", query)
            
            if query:
                if not handle_query(query):
                    break

        except Exception as e:
            print(e)
            speak("Sorry, there was an error. Please try again.")
