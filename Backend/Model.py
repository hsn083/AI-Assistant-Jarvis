import cohere
from rich import print
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
CohereAPIKey = env_vars.get("CohereAPIKey")

co = cohere.Client(api_key=CohereAPIKey)

funcs = [
    "exit", "general", "realtime", "open", "open file", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "site search", "create file", "delete file",
    "reminder"
]

messages = []

preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
-> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require any up to date information like if the query is 'who was akbar?' respond with 'general who was akbar?', if the query is 'how can i study more effectively?' respond with 'general how can i study more effectively?', if the query is 'can you help me with this math problem?' respond with 'general can you help me with this math problem?', if the query is 'Thanks, i really liked it.' respond with 'general thanks, i really liked it.' , if the query is 'what is python programming language?' respond with 'general what is python programming language?', etc. Respond with 'general (query)' if a query doesn't have a proper noun or is incomplete like if the query is 'who is he?' respond with 'general who is he?', if the query is 'what's his networth?' respond with 'general what's his networth?', if the query is 'tell me more about him.' respond with 'general tell me more about him.', and so on even if it require up-to-date information to answer. Respond with 'general (query)' if the query is asking about time, day, date, month, year, etc like if the query is 'what's the time?' respond with 'general what's the time?'.
-> Respond with 'realtime ( query )' if a query REQUIRES up-to-date information from the internet that a language model would not know, such as: current news, recent events, live scores, current prices, stock prices, today's weather, latest updates, who currently holds a position, what happened recently, or anything that changes day to day. Examples: 'who is the current prime minister of pakistan' → 'realtime who is the current prime minister of pakistan', 'what is bitcoin price today' → 'realtime what is bitcoin price today', 'latest news about cricket' → 'realtime latest news about cricket', 'what happened in the news today' → 'realtime what happened in the news today', 'tell me about facebook recent update' → 'realtime tell me about facebook recent update', 'what is the weather today' → 'realtime what is the weather today', 'who won the match today' → 'realtime who won the match today'. IMPORTANT: if the query asks about a LIVING person's current status, current role, recent work, or recent news — always use realtime. If the query asks about HISTORICAL facts, definitions, or general knowledge that doesn't change — use general.
-> Respond with 'open (application name or website name)' if a query is asking to open any application like 'open facebook', 'open telegram', etc. but if the query is asking to open multiple applications, respond with 'open 1st application name, open 2nd application name' and so on.
-> Respond with 'close (application name)' if a query is asking to close any application like 'close notepad', 'close facebook', etc. but if the query is asking to close multiple applications or websites, respond with 'close 1st application name, close 2nd application name' and so on.
-> Respond with 'play (song name)' if a query is asking to play any song like 'play afsanay by ys', 'play let her go', etc. but if the query is asking to play multiple songs, respond with 'play 1st song name, play 2nd song name' and so on.
-> Respond with 'generate image (image prompt)' if a query is requesting to generate a image with given prompt like 'generate image of a lion', 'generate image of a cat', etc. but if the query is asking to generate multiple images, respond with 'generate image 1st image prompt, generate image 2nd image prompt' and so on.
-> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder like 'set a reminder at 9:00pm on 25th june for my business meeting.' respond with 'reminder 9:00pm 25th june business meeting'.
-> Respond with 'system (task name)' if a query is asking to mute, unmute, volume up, volume down , etc. but if the query is asking to do multiple tasks, respond with 'system 1st task, system 2nd task', etc.
-> Respond with 'content (topic)' if a query is asking to write any type of content like application, codes, emails or anything else about a specific topic but if the query is asking to write multiple types of content, respond with 'content 1st topic, content 2nd topic' and so on.
-> Respond with 'google search (topic)' if a query is asking to search a specific topic on google but if the query is asking to search multiple topics on google, respond with 'google search 1st topic, google search 2nd topic' and so on.
-> Respond with 'youtube search (topic)' if a query is asking to search a specific topic on youtube but if the query is asking to search multiple topics on youtube, respond with 'youtube search 1st topic, youtube search 2nd topic' and so on.
-> Respond with 'site search (site name: topic)' if a query is asking to find, search, or look up something on a specific named website other than google or youtube, such as facebook, instagram, twitter/x, linkedin, amazon, or wikipedia. Example: if the query is 'find page on facebook called islamic lab' respond with 'site search facebook: islamic lab'. If the query is 'search for wireless mouse on amazon' respond with 'site search amazon: wireless mouse'. If the query is 'look up john smith on linkedin' respond with 'site search linkedin: john smith'.
-> Respond with 'create file (full file path)' if a query is asking to create a new empty file at a specific location, like 'create a file called notes.txt on my desktop' respond with 'create file C:\\Users\\%USERNAME%\\Desktop\\notes.txt'. If no folder is mentioned, assume the Desktop.
-> Respond with 'open file (full file path or just a file/folder name)' if a query is asking to open an existing file or folder, like 'open my documents folder' respond with 'open file Documents', or 'open report.docx from downloads' respond with 'open file C:\\Users\\%USERNAME%\\Downloads\\report.docx'.
-> Respond with 'delete file (full file path or file name)' if a query is asking to delete a file, like 'delete the file called old_notes.txt' respond with 'delete file old_notes.txt'.
*** If the query is asking to perform multiple tasks like 'open facebook, telegram and close whatsapp' respond with 'open facebook, open telegram, close whatsapp' ***
*** If the user is saying goodbye or wants to end the conversation like 'bye jarvis.' respond with 'exit'.***
*** Respond with 'general (query)' if you can't decide the kind of query or if a query is asking to perform a task which is not mentioned above. ***
"""

ChatHistory = [
    {"role": "User", "message": "how are you ?"},
    {"role": "Chatbot", "message": "general how are you ?"},
    {"role": "User", "message": "do you like pizza ?"},
    {"role": "Chatbot", "message": "general do you like pizza ?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and by the way remind me that i have a dancing performance on 5th at 11pm"},
    {"role": "Chatbot", "message": "general what is today's date, reminder 11:00pm 5th aug dancing performance"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."},
    {"role": "User", "message": "find page on facebook thats name islamic lab"},
    {"role": "Chatbot", "message": "site search facebook: islamic lab"},
    {"role": "User", "message": "search wireless headphones on amazon"},
    {"role": "Chatbot", "message": "site search amazon: wireless headphones"},
    {"role": "User", "message": "what is bitcoin price today"},
    {"role": "Chatbot", "message": "realtime what is bitcoin price today"},
    {"role": "User", "message": "latest news about pakistan"},
    {"role": "Chatbot", "message": "realtime latest news about pakistan"},
    {"role": "User", "message": "who won ipl today"},
    {"role": "Chatbot", "message": "realtime who won ipl today"},
    {"role": "User", "message": "what is the weather in lahore"},
    {"role": "Chatbot", "message": "realtime what is the weather in lahore"},
    {"role": "User", "message": "who is elon musk"},
    {"role": "Chatbot", "message": "realtime who is elon musk"},
    {"role": "User", "message": "what is python programming language"},
    {"role": "Chatbot", "message": "general what is python programming language"},
    {"role": "User", "message": "what happened in the news today"},
    {"role": "Chatbot", "message": "realtime what happened in the news today"},
    {"role": "User", "message": "who was akbar"},
    {"role": "Chatbot", "message": "general who was akbar"},
]

def FirstLayerDMM(prompt: str = "test"):
    messages.append({"role": "user", "content": f"{prompt}"})

    # Non-streaming is faster here: this returns a short classification
    # string like "general (what is AI)" -- streaming that word-by-word
    # adds protocol overhead and latency for no benefit on short outputs.
    try:
        result = co.chat(
            model="command-r-plus-08-2024",
            message=prompt,
            temperature=0.7,
            chat_history=ChatHistory,
            prompt_truncation='OFF',
            connectors=[],
            preamble=preamble
        )
        # Cohere SDK v4 uses result.text; v5+ uses result.message.content
        if hasattr(result, 'text') and result.text:
            response = result.text
        elif hasattr(result, 'message') and hasattr(result.message, 'content'):
            content = result.message.content
            if isinstance(content, list) and content:
                response = content[0].text if hasattr(content[0], 'text') else str(content[0])
            else:
                response = str(content)
        else:
            response = str(result)
    except Exception as e:
        print(f"FirstLayerDMM error: {e}")
        response = f"general {prompt}"

    response = response.replace("\n", "")
    response = response.split(",")

    response = [i.strip() for i in response]

    temp = []

    for task in response:
        for func in funcs:
            if task.startswith(func):
                temp.append(task)

    response = temp

    if "(query)" in response:
        newresponse = FirstLayerDMM(prompt=prompt)
        return newresponse
    else:
        return response

    
if __name__ == "__main__":
    while True:
        print(FirstLayerDMM(input(">>>")))