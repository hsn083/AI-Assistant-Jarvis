import json  # Ensure the import is used
from json import load, dump
from dotenv import dotenv_values
import requests
import datetime
from groq import Groq
from Backend.NumberFix import fix_numbers, NUMBER_FORMAT_RULE

env_vars = dotenv_values(".env")

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
InputLanguage = env_vars.get("InputLanguage", "en")

client = Groq(api_key=GroqAPIKey)

messages = []

def _language_instruction():
    """Tells the chatbot which language to reply in, based on the
    InputLanguage configured in .env / Settings. Urdu gets an explicit
    script instruction since 'ur' alone is ambiguous about whether to
    use Urdu script or Roman/Latin transliteration -- and in practice,
    Urdu and Hindi are nearly the same spoken language, so models can
    drift into replying in Devanagari (Hindi script) instead of the
    Perso-Arabic Urdu script unless told very explicitly not to."""
    lang = (InputLanguage or "en").lower()
    if lang.startswith("ur"):
        return (
            "*** IMPORTANT: Reply ONLY in natural, fluent Urdu language. "
            "Use proper conversational Urdu like a native speaker (Pakistani Urdu style). "
            "Write in clean Urdu script, not Roman Urdu and not Hindi. "
            "Keep responses natural and human-like. ***"
        )
    if lang.startswith("en"):
        return "*** Reply in only English, even if the question is in another language, reply in English.***"
    return f"*** Reply in the user's language ({InputLanguage}), not English, unless they switch languages first. ***"

DEVANAGARI_RANGE = (0x0900, 0x097F)

def _contains_devanagari(text):
    return any(DEVANAGARI_RANGE[0] <= ord(ch) <= DEVANAGARI_RANGE[1] for ch in text)

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
{_language_instruction()}
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
{NUMBER_FORMAT_RULE}
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
except json.JSONDecodeError:
    print("ChatLog.json is empty or corrupted. Initializing with an empty list.")
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

def RealtimeInformation():
    now = datetime.datetime.now()
    return (
        f"Please use this real-time information if needed:\n"
        f"Day: {now.strftime('%A')}\nDate: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\nYear: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')} hours, {now.strftime('%M')} minutes.\n"
    )

# Cache the realtime info string for one minute — it's regenerated on every
# ChatBot call, but the date/time only changes at minute resolution, so
# there's no point paying string formatting cost more than once per minute.
_rt_cache: dict = {"ts": 0.0, "val": ""}

def _cached_realtime_info() -> str:
    import time as _t
    now = _t.time()
    if now - _rt_cache["ts"] > 60:
        _rt_cache["val"] = RealtimeInformation()
        _rt_cache["ts"]  = now
    return _rt_cache["val"]

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def ChatBot(Query):
    """ This function sends the user's query to the chatbot and returns the AI's response """

    try:
        from Frontend.GUI import GetStopFlag
    except Exception:
        GetStopFlag = lambda: False

    lang = (InputLanguage or "en").lower()
    want_urdu = lang.startswith("ur")

    # Load full history once -- shared across the try block below
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            all_messages = load(f)
    except Exception:
        all_messages = []

    def _run_completion(extra_system_msg=None):
        # Cap history sent to API to last 20 messages for speed
        messages = all_messages[-20:]
        messages.append({"role": "user", "content": f"{Query}"})

        sys_msgs = SystemChatBot + [{"role": "system", "content": _cached_realtime_info()}]
        if extra_system_msg:
            sys_msgs = sys_msgs + [{"role": "system", "content": extra_system_msg}]

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=sys_msgs + messages,
            max_tokens=512,
            temperature=0.3,
            top_p=1,
            stream=True,
            stop=None
        )

        answer = ""
        stopped = False
        for chunk in completion:
            if GetStopFlag():
                stopped = True
                try:
                    completion.close()
                except Exception:
                    pass
                break
            if chunk.choices[0].delta.content:
                answer += chunk.choices[0].delta.content
        return answer.replace("</s>", ""), stopped

    def _save(answer):
        all_messages.append({"role": "user", "content": Query})
        all_messages.append({"role": "assistant", "content": answer})
        try:
            with open(r"Data\ChatLog.json", "w") as f:
                dump(all_messages, f, indent=4)
        except Exception as e:
            print(f"ChatLog save error: {e}")

    try:
        Answer, was_stopped = _run_completion()

        if was_stopped:
            if Answer.strip():
                _save(Answer)
            return ""

        # Only run Devanagari check/retry when Urdu is configured
        # (running this for every English query wastes API calls)
        if want_urdu and _contains_devanagari(Answer):
            print("Reply came back in Devanagari -- retrying once.")
            retry_answer, retry_stopped = _run_completion(
                extra_system_msg=(
                    "Your previous reply used Hindi/Devanagari script. "
                    "Rewrite ONLY in Urdu (Perso-Arabic) script."
                )
            )
            if not retry_stopped and retry_answer.strip():
                if not _contains_devanagari(retry_answer):
                    Answer = retry_answer
                else:
                    try:
                        import mtranslate as mt
                        translated = mt.translate(retry_answer, "ur", "hi")
                        Answer = translated if translated and translated.strip() else retry_answer
                    except Exception as e:
                        print(f"Hindi→Urdu fallback failed: {e}")
                        Answer = retry_answer

        _save(Answer)
        return fix_numbers(Answer)

    except Exception as e:
        # Log the real error -- do NOT wipe chat history on a transient error
        print(f"ChatBot error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return f"Sorry, I couldn't connect to the AI service. Please check your internet and API key, then try again."


if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        response = ChatBot(user_input)
        print(response)