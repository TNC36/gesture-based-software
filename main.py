import pyttsx3 #!pip install pyttsx3
import speech_recognition as sr
import pyautogui
import webbrowser
import os
import new1

def in_engine():
    engine = pyttsx3.init("sapi5")
    voices = engine.getProperty( 'voices')
    engine.setProperty('voice', voices[1].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-50)
    volume = engine.getProperty('volume')
    engine.setProperty('volume', volume+0.25)
    return engine

def speak(text):
    engine = in_engine()
    engine.say(text)
    engine.runAndWait()

def get_voice_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening.......")
        r.pause_threshold=1.0
        r.phrase_threshold=0.3
        r.sample_rate = 48000
        r.dynamic_energy_threshold=True
        r.operation_timeout=5
        r.non_speaking_duration=0.5
        r.dynamic_energy_adjustment=2
        r.energy_threshold=4000
        r.phrase_time_limit = 10
        # print(sr.Microphone.list_microphone_names())
        audio = r.listen(source)
        try:
            query = r.recognize_google(audio, language='en-in')
        except sr.UnknownValueError:
            print("Could not understand audio. Please repeat.")
            return "None"
        except sr.RequestError:
            print("Speech recognition service unavailable.")
            return "None"
    return query

def open_browser(query):
    if 'google' in query:
        speak("Boss, what should i search on google..")
        search =get_voice_command().lower()
        webbrowser.open(f"{search}")
    elif 'edge' in query:
        speak("opening your microsoft edge")
        os.startfile()

def intro(query):
    if 'introduce yourself' in query:
        speak("Allow me to introduce myself I am Mantiso, the virtual artificial intelligence and Im here to assist you with a variety of tasks as best I can.")
def register_user():
    speak("by which name i should register you")
    nameing =get_voice_command().lower()
    names=nameing
    speak(f'your name is {names}')
    # print(names)
    return names

def register_User_file():
    speak("by which name i should register your face id")
    nameing =get_voice_command().lower()
    names=nameing
    speak(f'your face id name is {names}')
    # print(names)
    return names

if __name__ == "__main__":
    while True:
        query =get_voice_command().lower()

        if "stop" in query:
            speak('Stoping the execution')
            break

        elif ("raise volume" in query) or ("increase volume" in query):
            pyautogui.press("volumeup")
            speak("Volume increased")

        elif ("volume down" in query) or ("decrease volume" in query):
            pyautogui.press("volumedown")
            speak("Volume decrease")

        elif ("volume mute" in query) or ("mute sound" in query):
            pyautogui.press("volumemute")
            speak("Volume muted")

        elif ("open google" in query) or ("open edge" in query):
            open_browser(query)

        elif ("introduce yourself" in query):
            intro(query)

        elif ('register me'  in query):
            register_user()

        elif ("face" in query) or ("recogntion" in query):
            speak("Starting face recognition.")
            if os.path.exists("reg1.py"):
                os.system("python reg1.py")
            else:
                print("Error: reg1.py not found.")

        elif ('gesture' in query) or ('start gesture' in query):
            speak("Starting gesture and eye recognition.")
            if os.path.exists("new1.py"):
                os.system("python new1.py")
            else:
                print("Error: new1.py not found.")
                
        elif ('pause camera' in query):
            speak('stoping the camera')
            
# speak ("Hello, I'm JARVIS")