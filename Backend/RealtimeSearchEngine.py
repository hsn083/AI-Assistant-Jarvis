"""
RealtimeSearchEngine.py  —  Dual-Source Real-Time Search
=========================================================
Uses TWO search APIs for maximum coverage:

  1. NewsData.io  — for ALL news/current events queries
     • Live news from 80,000+ sources worldwide
     • Pakistani/Urdu news sources included
     • Returns headline, description, source, published date, content
     • Free tier: 200 requests/day

  2. SerpAPI (Google Search)  — for factual/general web queries
     • Answer box, knowledge graph, organic results
     • Sports scores, prices, weather, people, places
     • Free tier: 100 searches/month

Smart routing:
  • News/current events keywords → NewsData.io
  • Everything else → SerpAPI Google
  • Both keys missing → graceful error message

Per-minute cache prevents duplicate API calls.
Full conversation history (last 20 messages) included in every AI call.
Urdu digit fix + Devanagari guard applied to every answer.

Setup (.env):
  NewsDataAPIKey=your_newsdata_key   # https://newsdata.io/  (free: 200/day)
  SerpAPIKey=your_serpapi_key        # https://serpapi.com/  (free: 100/month)
"""

import requests
import json
import datetime
import os
import re
from json import load, dump
from groq import Groq
from dotenv import dotenv_values
from Backend.NumberFix import fix_numbers, NUMBER_FORMAT_RULE

# ── Config ─────────────────────────────────────────────────────────────────────
env_vars        = dotenv_values(".env")
Username        = env_vars.get("Username", "User")
Assistantname   = env_vars.get("Assistantname", "Jarvis")
GroqAPIKey      = env_vars.get("GroqAPIKey")
SerpAPIKey      = env_vars.get("SerpAPIKey", "")
NewsDataAPIKey  = env_vars.get("NewsDataAPIKey", "")
InputLanguage   = env_vars.get("InputLanguage", "en")
HISTORY_WINDOW  = int(env_vars.get("HistoryWindow", "20"))

os.makedirs("Data", exist_ok=True)
CHATLOG = os.path.join("Data", "ChatLog.json")

client = Groq(api_key=GroqAPIKey)

# ── Language instruction ───────────────────────────────────────────────────────
def _language_instruction() -> str:
    lang = (InputLanguage or "en").lower()
    if lang.startswith("ur"):
        return (
            "*** CRITICAL LANGUAGE RULE: Reply ONLY in pure Urdu, written ONLY in "
            "Urdu (Perso-Arabic, Nastaliq) script. Example: آپ کیسے ہیں\n"
            "*** DO NOT use Hindi or Devanagari script (हिन्दी is FORBIDDEN). ***\n"
            "*** DO NOT use Roman/Latin letters or Roman Urdu. ***\n"
            "*** For brand names write Urdu transliteration: فیس بک، یوٹیوب، گوگل ***\n"
            "*** Translate ALL English search data below into proper Urdu before answering. ***"
        )
    if lang.startswith("en"):
        return "*** Reply in English only. ***"
    return f"*** Reply in the user's language ({InputLanguage}), translating the search data if needed. ***"

# ── Devanagari guard ───────────────────────────────────────────────────────────
DEVANAGARI_RANGE = (0x0900, 0x097F)

def _contains_devanagari(text: str) -> bool:
    return any(DEVANAGARI_RANGE[0] <= ord(ch) <= DEVANAGARI_RANGE[1] for ch in text)

# ── System prompt ──────────────────────────────────────────────────────────────
System = (
    f"Hello, I am {Username}. You are a very accurate and advanced AI assistant named "
    f"{Assistantname} with real-time internet access.\n"
    "*** Provide professional, concise answers. Use proper punctuation and grammar. ***\n"
    "*** Answer ONLY from the provided search/news data. Do not invent facts. ***\n"
    "*** You are in Conversation Mode — maintain context across all turns. ***\n"
    f"{_language_instruction()}"
    f"{NUMBER_FORMAT_RULE}"
)

_BASE_SYSTEM = [
    {"role": "system",    "content": System},
    {"role": "user",      "content": "Hi"},
    {"role": "assistant", "content": f"Hello {Username}, how can I help you?"},
]

# ── ChatLog helpers ────────────────────────────────────────────────────────────
def _load_history() -> list:
    try:
        with open(CHATLOG, "r", encoding="utf-8") as f:
            data = load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _save_history(history: list) -> None:
    try:
        with open(CHATLOG, "w", encoding="utf-8") as f:
            dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[RealtimeSearch] ChatLog save error: {e}")

if not os.path.exists(CHATLOG):
    _save_history([])

# ── Realtime clock info ────────────────────────────────────────────────────────
def _realtime_info() -> str:
    dt = datetime.datetime.now()
    return (
        f"Real-time info — Day: {dt.strftime('%A')}, "
        f"Date: {dt.strftime('%d %B %Y')}, "
        f"Time: {dt.strftime('%H:%M:%S')}"
    )

# ── Per-minute result cache ────────────────────────────────────────────────────
_cache: dict[str, str] = {}

def _cache_key(source: str, query: str) -> str:
    minute = datetime.datetime.now().strftime("%Y%m%d%H%M")
    return f"{source}:{query.strip().lower()}:{minute}"

def _cache_get(key: str) -> str | None:
    return _cache.get(key)

def _cache_set(key: str, value: str) -> None:
    _cache[key] = value
    if len(_cache) > 100:
        del _cache[next(iter(_cache))]

# ── News query detector ────────────────────────────────────────────────────────
_NEWS_RE = re.compile(
    r'\b(news|latest|breaking|today|update|recent|happened|current events|'
    r'headlines|خبر|خبریں|آج کی خبر|تازہ|حالیہ|ابھی)\b',
    re.IGNORECASE
)

def _is_news_query(query: str) -> bool:
    return bool(_NEWS_RE.search(query))

# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 1 — NewsData.io
# ══════════════════════════════════════════════════════════════════════════════
def _newsdata_search(query: str) -> str:
    """
    Fetch live news from NewsData.io.
    Tries Urdu-language results first when InputLanguage is Urdu,
    then falls back to English results.
    Free plan: 200 requests/day, 10 results per call.
    Docs: https://newsdata.io/documentation
    """
    if not NewsDataAPIKey:
        return ""   # caller will fall back to SerpAPI

    lang = (InputLanguage or "en").lower()

    # Build params — request Urdu news when user is Urdu, else English
    params: dict = {
        "apikey":   NewsDataAPIKey,
        "q":        query,
        "size":     5,
        "language": "ur" if lang.startswith("ur") else "en",
    }

    def _fetch(p: dict) -> list:
        try:
            r = requests.get("https://newsdata.io/api/1/latest", params=p, timeout=10)
            r.raise_for_status()
            return r.json().get("results", [])
        except requests.exceptions.Timeout:
            print(f"[NewsData] Timeout for: {query}")
            return []
        except Exception as e:
            print(f"[NewsData] Error: {e}")
            return []

    articles = _fetch(params)

    # If Urdu search returned nothing, retry in English
    if not articles and lang.startswith("ur"):
        params["language"] = "en"
        articles = _fetch(params)

    if not articles:
        return ""   # signal: no results, try SerpAPI

    result = f"NewsData.io live news results for '{query}':\n[start]\n"
    for art in articles[:5]:
        title       = art.get("title") or ""
        description = (art.get("description") or "")[:300]
        source_name = art.get("source_id") or art.get("source_name") or ""
        pub_date    = art.get("pubDate") or ""
        content     = (art.get("content") or "")[:200]
        country     = ", ".join(art.get("country") or [])
        category    = ", ".join(art.get("category") or [])

        result += f"Headline: {title}\n"
        if source_name:
            result += f"Source: {source_name}"
            if pub_date:
                result += f"  ({pub_date[:16]})"   # trim seconds
            result += "\n"
        if country:
            result += f"Country: {country}\n"
        if category:
            result += f"Category: {category}\n"
        if description:
            result += f"Summary: {description}\n"
        if content and content != description:
            result += f"Detail: {content}\n"
        result += "\n"

    result += "[end]"
    print(f"[NewsData] {len(articles)} articles returned for: {query[:60]}")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 2 — SerpAPI (Google Search)
# ══════════════════════════════════════════════════════════════════════════════
def _serp_google(query: str) -> str:
    """
    Google Search via SerpAPI — answer box, knowledge graph, organic results.
    Free plan: 100 searches/month.
    Docs: https://serpapi.com/search-api
    """
    if not SerpAPIKey:
        return _error_result(query, "SerpAPIKey not configured in .env")

    params = {
        "engine":  "google",
        "q":       query,
        "api_key": SerpAPIKey,
        "num":     5,
        "hl":      "en",
        "gl":      "pk",   # Pakistan locale for local relevance
    }

    try:
        r = requests.get("https://serpapi.com/search", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.Timeout:
        return _error_result(query, "Google search timed out.")
    except Exception as e:
        print(f"[SerpAPI] Error: {e}")
        return _error_result(query, str(e))

    result = f"Google search results for '{query}':\n[start]\n"

    # 1. Answer box — direct fact
    ab = data.get("answer_box", {})
    if ab:
        ab_ans = ab.get("answer") or ab.get("result") or ab.get("snippet") or ""
        if ab_ans:
            result += f"[Direct Answer]\n{ab.get('title', '')}: {ab_ans}\n\n"
        if "table" in ab:
            result += "Table:\n"
            for row in ab["table"][:5]:
                result += "  " + "  |  ".join(str(v) for v in row.values()) + "\n"
            result += "\n"

    # 2. Knowledge graph — entity summary
    kg = data.get("knowledge_graph", {})
    if kg and kg.get("title"):
        result += f"[Knowledge Graph]\n{kg['title']}"
        if kg.get("type"):
            result += f" ({kg['type']})"
        result += "\n"
        if kg.get("description"):
            result += f"{kg['description']}\n"
        skip = {"title","description","type","image","website","header_images",
                "merchant_description","profiles","books","tv_shows_and_movies"}
        for k, v in kg.items():
            if k not in skip and isinstance(v, str) and v:
                result += f"{k.replace('_',' ').title()}: {v}\n"
        result += "\n"

    # 3. Sports scores
    sports = data.get("sports_results", {})
    if sports:
        result += f"[Sports Results]\n{json.dumps(sports, indent=2)[:500]}\n\n"

    # 4. Top stories
    for story in data.get("top_stories", [])[:3]:
        result += f"[Story] {story.get('title','')} ({story.get('date','')})\n"
    if data.get("top_stories"):
        result += "\n"

    # 5. Organic results
    organic = data.get("organic_results", [])
    if organic:
        result += "[Web Results]\n"
        for r_item in organic[:4]:
            title   = r_item.get("title", "")
            snippet = (r_item.get("snippet") or "")[:350]
            if title or snippet:
                result += f"Title: {title}\n"
                if snippet:
                    result += f"Snippet: {snippet}\n"
                result += "\n"

    result += "[end]"
    print(f"[SerpAPI] Results returned for: {query[:60]}")
    return result


def _serp_news(query: str) -> str:
    """
    Google News engine via SerpAPI — used as fallback when NewsData returns nothing.
    """
    if not SerpAPIKey:
        return ""

    params = {
        "engine":  "google_news",
        "q":       query,
        "api_key": SerpAPIKey,
        "hl":      "en",
        "gl":      "pk",
    }
    try:
        r = requests.get("https://serpapi.com/search", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[SerpAPI News] Error: {e}")
        return ""

    articles = data.get("news_results", [])
    if not articles:
        return ""

    result = f"Google News results for '{query}':\n[start]\n"
    for art in articles[:5]:
        title   = art.get("title", "")
        source  = art.get("source", {}).get("name", "") if isinstance(art.get("source"), dict) else ""
        date    = art.get("date", "")
        snippet = (art.get("snippet") or "")[:300]
        result += f"Headline: {title}\n"
        if source:
            result += f"Source: {source}"
            if date:
                result += f" ({date})"
            result += "\n"
        if snippet:
            result += f"Summary: {snippet}\n"
        result += "\n"
    result += "[end]"
    return result


# ── Error helper ───────────────────────────────────────────────────────────────
def _error_result(query: str, error: str) -> str:
    return (
        f"Search results for '{query}':\n[start]\n"
        f"Search failed: {error}\n[end]"
    )

# ── No-key fallback ────────────────────────────────────────────────────────────
def _no_keys_message(query: str) -> str:
    return (
        f"Search results for '{query}':\n[start]\n"
        "No search API keys configured.\n"
        "Add NewsDataAPIKey= (https://newsdata.io/) and/or "
        "SerpAPIKey= (https://serpapi.com/) to your .env file.\n"
        "[end]"
    )

# ══════════════════════════════════════════════════════════════════════════════
# SMART DISPATCHER — routes query to the right source(s)
# ══════════════════════════════════════════════════════════════════════════════
def SmartSearch(query: str) -> str:
    """
    Routing logic:
      News query  → NewsData.io first, SerpAPI Google News as fallback
      Other query → SerpAPI Google Search first, NewsData as supplement
                    if no SerpAPI key, try NewsData anyway
    All results are cached per-minute to avoid duplicate API calls.
    """
    if not NewsDataAPIKey and not SerpAPIKey:
        return _no_keys_message(query)

    is_news = _is_news_query(query)

    if is_news:
        # ── NEWS PATH: NewsData.io → SerpAPI News fallback ────────────────
        ckey = _cache_key("newsdata", query)
        cached = _cache_get(ckey)
        if cached:
            print(f"[Cache] NewsData hit: {query[:50]}")
            return cached

        print(f"[Routing] News query → NewsData.io: {query[:60]}")
        result = _newsdata_search(query)

        if not result:
            # NewsData returned nothing — try SerpAPI News
            print(f"[Fallback] NewsData empty → SerpAPI News")
            ckey2 = _cache_key("serp_news", query)
            cached2 = _cache_get(ckey2)
            if cached2:
                return cached2
            result = _serp_news(query)
            if result:
                _cache_set(ckey2, result)
            else:
                # Last resort: regular Google search
                result = _serp_google(query) if SerpAPIKey else _error_result(query, "No news found and no SerpAPI key.")

        if result:
            _cache_set(ckey, result)
        return result or _error_result(query, "No results from any source.")

    else:
        # ── GENERAL PATH: SerpAPI Google → NewsData supplement ────────────
        ckey = _cache_key("serp_google", query)
        cached = _cache_get(ckey)
        if cached:
            print(f"[Cache] SerpAPI hit: {query[:50]}")
            return cached

        if SerpAPIKey:
            print(f"[Routing] General query → SerpAPI Google: {query[:60]}")
            result = _serp_google(query)
        elif NewsDataAPIKey:
            # No SerpAPI — try NewsData anyway (better than nothing)
            print(f"[Routing] No SerpAPI key → NewsData fallback: {query[:60]}")
            result = _newsdata_search(query) or _error_result(query, "SerpAPIKey not configured.")
        else:
            result = _no_keys_message(query)

        if result:
            _cache_set(ckey, result)
        return result

# ── Answer cleanup ─────────────────────────────────────────────────────────────
def AnswerModifier(answer: str) -> str:
    return "\n".join(line for line in answer.split("\n") if line.strip())

# ══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTION — called from Main.py
# ══════════════════════════════════════════════════════════════════════════════
def RealtimeSearchEngine(prompt: str) -> str:
    """
    Search the web (SerpAPI + NewsData.io) and answer with the LLM.
    Full conversation history included. User message saved ONCE after response.
    """
    try:
        from Frontend.GUI import GetStopFlag
    except Exception:
        GetStopFlag = lambda: False

    prompt = prompt.strip()
    if not prompt:
        return ""

    lang      = (InputLanguage or "en").lower()
    want_urdu = lang.startswith("ur")

    history        = _load_history()
    search_context = SmartSearch(prompt)
    print(f"[Search] Context: {len(search_context)} chars")

    def _run_completion(extra_system_msg: str | None = None) -> tuple[str, bool]:
        sys_msgs = list(_BASE_SYSTEM) + [
            {"role": "system", "content": _realtime_info()},
            {"role": "system", "content": search_context},
        ]
        if extra_system_msg:
            sys_msgs.append({"role": "system", "content": extra_system_msg})

        context = history[-HISTORY_WINDOW:] + [{"role": "user", "content": prompt}]

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=sys_msgs + context,
            max_tokens=800,
            temperature=0.3,
            top_p=1,
            stream=True,
            stop=None,
        )

        answer  = ""
        stopped = False
        for chunk in completion:
            if GetStopFlag():
                stopped = True
                try:
                    completion.close()
                except Exception:
                    pass
                break
            delta = chunk.choices[0].delta.content
            if delta:
                answer += delta

        return answer.strip().replace("</s>", ""), stopped

    def _save(answer: str) -> None:
        history.append({"role": "user",      "content": prompt})
        history.append({"role": "assistant",  "content": answer})
        _save_history(history)

    Answer, was_stopped = _run_completion()

    if was_stopped:
        if Answer:
            _save(Answer)
        return ""

    # Urdu drift guard
    if want_urdu and _contains_devanagari(Answer):
        print("[RealtimeSearch] Devanagari detected — retrying in Urdu")
        retry, retry_stopped = _run_completion(
            extra_system_msg=(
                "Your previous reply used Hindi/Devanagari script, which is WRONG. "
                "Rewrite using ONLY Urdu (Perso-Arabic) script. "
                "Do not use any Devanagari characters."
            )
        )
        if not retry_stopped and retry:
            if not _contains_devanagari(retry):
                Answer = retry
            else:
                try:
                    import mtranslate as mt
                    translated = mt.translate(retry, "ur", "hi")
                    if translated and translated.strip():
                        Answer = translated
                except Exception as e:
                    print(f"[RealtimeSearch] mtranslate fallback failed: {e}")

    Answer = AnswerModifier(Answer)
    Answer = fix_numbers(Answer)
    _save(Answer)
    return Answer


# ── Standalone test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Jarvis Dual-Source Realtime Search")
    print(f"  NewsData.io : {'✅ configured' if NewsDataAPIKey else '❌ missing (NewsDataAPIKey= in .env)'}")
    print(f"  SerpAPI     : {'✅ configured' if SerpAPIKey else '❌ missing (SerpAPIKey= in .env)'}")
    print("=" * 60)
    print()
    while True:
        try:
            q = input("You: ").strip()
            if not q:
                continue
            print(f"\nJarvis: {RealtimeSearchEngine(q)}\n")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
