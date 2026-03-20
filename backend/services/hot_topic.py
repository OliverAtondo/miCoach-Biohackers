#!/usr/bin/env python3
"""
Enhanced Programming Hot Topics Scraper
Includes Tier 1 & Tier 2 developer news sources.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# ------------------------------
# EXISTING SCRAPERS (you already had)
# ------------------------------
# ... keep your existing Hacker News / Reddit / Dev.to / GitHub removed


# ==============================
# NEW SCRAPERS (Tier 1 + Tier 2)
# ==============================

# ---------------------------------------------------------
# 1. INFOQ
# ---------------------------------------------------------
def scrape_infoq() -> List[Dict]:
    try:
        url = "https://www.infoq.com/development/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        stories = []
        for article in soup.select("article")[:10]:
            title_tag = article.find("h2")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link_tag = article.find("a", href=True)
            if link_tag:
                link = "https://www.infoq.com" + link_tag["href"]
                stories.append({
                    "title": title,
                    "url": link,
                    "source": "InfoQ"
                })
        return stories
    except Exception as e:
        print(f"[!] InfoQ Error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# 2. SD Times
# ---------------------------------------------------------
def scrape_sd_times() -> List[Dict]:
    try:
        url = "https://sdtimes.com/category/developer/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        stories = []
        for article in soup.select("article")[:10]:
            title_tag = article.find("h2")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link_tag = article.find("a", href=True)
            if link_tag:
                stories.append({
                    "title": title,
                    "url": link_tag["href"],
                    "source": "SD Times"
                })
        return stories
    except Exception as e:
        print(f"[!] SD Times Error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# 3. DeveloperTech News
# ---------------------------------------------------------
def scrape_developertech() -> List[Dict]:
    try:
        url = "https://www.developer-tech.com/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        stories = []
        for art in soup.select("article")[:10]:
            title_tag = art.find("h3") or art.find("h2")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link_tag = art.find("a", href=True)
            if link_tag:
                stories.append({
                    "title": title,
                    "url": link_tag["href"],
                    "source": "DeveloperTech News"
                })
        return stories
    except Exception as e:
        print(f"[!] DeveloperTech Error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# 4. TechCrunch (Developer / Startup news)
# ---------------------------------------------------------
def scrape_techcrunch() -> List[Dict]:
    try:
        url = "https://techcrunch.com/tag/programming/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        stories = []
        for post in soup.select("div.post-block")[:10]:
            title_tag = post.find("h2")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link_tag = title_tag.find("a", href=True)
            if link_tag:
                stories.append({
                    "title": title,
                    "url": link_tag["href"],
                    "source": "TechCrunch"
                })
        return stories
    except Exception as e:
        print(f"[!] TechCrunch Error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# 5. Martin Fowler Blog
# ---------------------------------------------------------
def scrape_martin_fowler() -> List[Dict]:
    try:
        url = "https://martinfowler.com/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        stories = []
        for li in soup.select("ul#latest-articles li")[:10]:
            a = li.find("a", href=True)
            if a:
                title = a.get_text(strip=True)
                link = "https://martinfowler.com" + a["href"]
                stories.append({
                    "title": title,
                    "url": link,
                    "source": "Martin Fowler Blog"
                })
        return stories
    except Exception as e:
        print(f"[!] Martin Fowler Error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# 6. Stack Overflow Blog
# ---------------------------------------------------------
def scrape_stackoverflow_blog() -> List[Dict]:
    try:
        url = "https://stackoverflow.blog/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        stories = []
        for article in soup.select("article")[:10]:
            title_tag = article.find("h2")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link_tag = article.find("a", href=True)
            if link_tag:
                stories.append({
                    "title": title,
                    "url": link_tag["href"],
                    "source": "Stack Overflow Blog"
                })
        return stories

    except Exception as e:
        print(f"[!] SO Blog Error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# 7. DigitalOcean Community
# ---------------------------------------------------------
def scrape_digitalocean() -> List[Dict]:
    try:
        url = "https://www.digitalocean.com/community/tutorials"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        stories = []
        for card in soup.select("div.card--content")[:10]:
            a = card.find("a", href=True)
            if a:
                title = a.get_text(strip=True)
                link = "https://www.digitalocean.com" + a["href"]
                stories.append({
                    "title": title,
                    "url": link,
                    "source": "DigitalOcean Community"
                })
        return stories
    except Exception as e:
        print(f"[!] DigitalOcean Error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# 8. CSS-Tricks
# ---------------------------------------------------------
def scrape_css_tricks() -> List[Dict]:
    try:
        url = "https://css-tricks.com/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        stories = []
        for article in soup.select("article.article-card")[:10]:
            title_tag = article.find("h2")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link_tag = article.find("a", href=True)
            if link_tag:
                stories.append({
                    "title": title,
                    "url": link_tag["href"],
                    "source": "CSS-Tricks"
                })
        return stories
    except Exception as e:
        print(f"[!] CSS-Tricks Error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# 9. GitLab Trending Repos
# ---------------------------------------------------------
def scrape_gitlab_trending() -> List[Dict]:
    try:
        url = "https://gitlab.com/explore/projects/trending"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        stories = []
        for proj in soup.select("li.project-row")[:10]:
            a = proj.find("a", class_="project-row-title", href=True)
            if a:
                title = a.get_text(strip=True)
                link = "https://gitlab.com" + a["href"]
                stories.append({
                    "title": title,
                    "url": link,
                    "source": "GitLab Trending"
                })
        return stories
    except Exception as e:
        print(f"[!] GitLab Error: {e}", file=sys.stderr)
        return []


# ==============================
# COMBINED SCRAPE
# ==============================

def get_hot_topics(user_role: str = None) -> List[Dict]:
    """
    Get hot topics, optionally filtering or ranking by user_role (e.g., 'Frontend Developer').
    Each topic includes: title, url, source, summary (if available).
    """
    sources = [
        ("InfoQ", scrape_infoq),
        ("SD Times", scrape_sd_times),
        ("DeveloperTech", scrape_developertech),
        ("TechCrunch", scrape_techcrunch),
        ("Martin Fowler", scrape_martin_fowler),
        ("Stack Overflow Blog", scrape_stackoverflow_blog),
        ("DigitalOcean", scrape_digitalocean),
        ("CSS-Tricks", scrape_css_tricks),
        ("GitLab Trending", scrape_gitlab_trending)
    ]

    all_news = []
    for name, func in sources:
        print(f"Fetching {name} ...")
        try:
            for item in func():
                # Try to extract a summary/snippet if possible
                summary = None
                if 'url' in item:
                    try:
                        r = requests.get(item['url'], headers=HEADERS, timeout=6)
                        soup = BeautifulSoup(r.text, "html.parser")
                        # Try to get first paragraph or meta description
                        p = soup.find('p')
                        if p and len(p.get_text(strip=True)) > 40:
                            summary = p.get_text(strip=True)[:220]
                        else:
                            desc = soup.find('meta', attrs={'name': 'description'})
                            if desc and desc.get('content'):
                                summary = desc['content'][:220]
                    except Exception:
                        pass
                all_news.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "source": item.get("source", ""),
                    "summary": summary or ""
                })
        except Exception as e:
            print(f"[ERROR] {name}: {e}")

    # Si se provee user_role, filtrar/ordenar por relevancia usando keywords
    if user_role:
        role_keywords = {
            "frontend": ["css", "react", "vue", "angular", "javascript", "ui", "web", "html", "frontend"],
            "backend": ["api", "database", "server", "python", "node", "backend", "cloud", "docker", "sql"],
            "data": ["data", "ml", "ai", "machine learning", "analytics", "pandas", "numpy", "deep learning"],
            "devops": ["devops", "cloud", "ci", "cd", "docker", "kubernetes", "infrastructure", "aws", "azure"],
            "mobile": ["mobile", "android", "ios", "react native", "flutter", "swift", "kotlin"],
            "security": ["security", "cyber", "vulnerability", "encryption", "auth", "pentest", "hacking"],
        }
        role = user_role.lower()
        keywords = []
        for k, v in role_keywords.items():
            if k in role:
                keywords = v
                break
        if keywords:
            def score(item):
                text = (item["title"] + " " + item["summary"]).lower()
                return sum(kw in text for kw in keywords)
            all_news.sort(key=score, reverse=True)

    return all_news


# ==============================
# MAIN
# ==============================
def main():
    print("🔍 Scraping latest programming news...\n")

    news = get_hot_topics()

    print("\n📰 Latest Programming News:")
    print("=" * 80)
    for i, item in enumerate(news[:80], 1):
        print(f"{i:2d}. [{item['source']}] {item['title']}")
        print(f"    {item['url']}\n")
    print("=" * 80)
    print(f"Total items is: {len(news)}")


if __name__ == "__main__":
    main()