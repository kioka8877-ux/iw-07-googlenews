"""
IW-07 GoogleNews — Google News Results
Iron Warrior #7 — Actualités multi-source.
Attaque : Scale SERP ($59/10K)
"""
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import sys
sys.path.insert(0, '/home/user/iron_warriors/shared')
from base import create_app, fetch_html, clean_text, get_timestamp, measure_latency
import time

app = create_app("IW-07 GoogleNews", "Google News results — actualités multi-source")

class NewsResult(BaseModel):
    title: str
    url: str
    source: Optional[str] = None
    snippet: Optional[str] = None
    time_ago: Optional[str] = None
    image_url: Optional[str] = None
    position: int

class NewsResponse(BaseModel):
    query: str
    engine: str
    results: List[NewsResult]
    timestamp: str
    latency_ms: int

@app.get("/search", response_model=NewsResponse)
async def google_news(
    q: str = Query(..., description="News search query"),
    num: int = Query(20, ge=1, le=100),
    gl: str = Query("us"),
    hl: str = Query("en"),
):
    start = time.time()
    url = f"https://www.google.com/search?q={quote_plus(q)}&tbm=nws&num={num}&gl={gl}&hl={hl}"
    try:
        html = await fetch_html(url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Google News fetch failed: {e}")

    soup = BeautifulSoup(html, 'html.parser')
    results = []
    seen = set()

    for div in soup.find_all('div', class_='g') or soup.find_all('div', class_='SoaBEf'):
        h3 = div.find('h3')
        link = div.find('a', href=True)
        source_tag = div.find('div', class_='UPmit') or div.find('span', class_='X5C7bc')
        snippet_tag = div.find('div', class_='GI74Re') or div.find('div', class_='st')
        time_tag = div.find('span', class_='r0bn4c') or div.find('span', class_='tfYN0c')
        img_tag = div.find('img')

        if h3 and link:
            href = link['href']
            if href.startswith('/url?q='):
                href = href.split('/url?q=')[1].split('&')[0]
            if href in seen or not href.startswith('http'):
                continue
            seen.add(href)
            results.append(NewsResult(
                title=clean_text(h3.get_text()),
                url=href,
                source=clean_text(source_tag.get_text()) if source_tag else None,
                snippet=clean_text(snippet_tag.get_text()) if snippet_tag else None,
                time_ago=clean_text(time_tag.get_text()) if time_tag else None,
                image_url=img_tag.get('src') if img_tag else None,
                position=len(results) + 1,
            ))
            if len(results) >= num:
                break

    return NewsResponse(
        query=q, engine="google_news", results=results,
        timestamp=get_timestamp(), latency_ms=measure_latency(start),
    )
