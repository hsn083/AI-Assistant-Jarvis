from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from dotenv import dotenv_values
import os
import time as time_module
import mtranslate as mt

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage")

# HTML content with speech recognition
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;
        let shouldRestart = false;

        function startRecognition() {
            output.textContent = "";
            shouldRestart = true;
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                if (shouldRestart) {
                    recognition.start();
                }
            };
            recognition.start();
        }

        function stopRecognition() {
            shouldRestart = false;
            if (recognition) {
                recognition.stop();
            }
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

# Inject Input Language
HtmlCode = HtmlCode.replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# Save HTML to file
os.makedirs("Data", exist_ok=True)
with open("Data/Voice.html", "w", encoding="utf-8") as f:
    f.write(HtmlCode)

# Construct local file URL
current_dir = os.getcwd()
Link = f"{current_dir}/Data/Voice.html"
# Chrome settings
chrome_options = Options()

chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
#chrome_options.add_argument("--headless=new")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
)

# Selenium Manager automatically finds/downloads ChromeDriver
driver = webdriver.Chrome(options=chrome_options)

# Setup temp status path
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
os.makedirs(TempDirPath, exist_ok=True)

def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, "Status.data"), "w", encoding='utf-8') as file:
        file.write(Status)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation

_recognition_page_loaded = False

def SpeechRecognition():
    global _recognition_page_loaded
    import time as _t

    # Load the page only once — reloading added 200-500ms per query.
    if not _recognition_page_loaded:
        driver.get("file:///" + Link)
        _recognition_page_loaded = True

    # Click start via JS (faster than find_element + .click())
    driver.execute_script("document.getElementById('start').click();")

    # Poll using execute_script to read innerText directly — avoids the
    # Selenium element-lookup overhead of find_element on every iteration.
    # 20ms polling (was 50ms) means at most 20ms lag after speech ends.
    while True:
        try:
            Text = driver.execute_script(
                "return document.getElementById('output').innerText || '';"
            )
            if Text and Text.strip():
                driver.execute_script("document.getElementById('end').click();")
                if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                    return QueryModifier(Text.strip())
                else:
                    SetAssistantStatus("Translating...")
                    return QueryModifier(UniversalTranslator(Text.strip()))
        except Exception:
            pass
        _t.sleep(0.02)   # 20ms — imperceptible but halves polling lag vs 50ms

# Run the assistant
if __name__ == "__main__":
    while True:
        Text = SpeechRecognition()
        print(Text)
