#!/usr/bin/env python3
"""
Hot Topics Scraper for Programming News
Scrapes latest news from reliable sources: Hacker News, Reddit r/programming, Dev.to, GitHub Trending
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict
import sys

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_hacker_news() -> List[Dict]:
    """Scrape top stories from Hacker News"""
    try:
        url = 'https://news.ycombinator.com/'
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        stories = []
        # HN uses <tr class="athing"> for stories
        for item in soup.find_all('tr', class_='athing')[:10]:  # Top 10
            title_tag = item.find('a', class_='titlelink')
            if title_tag:
                title = title_tag.get_text(strip=True)
                url = title_tag.get('href')
                # Include if it's an external link or programming related
                if url and not url.startswith('item?id='):
                    stories.append({
                        'title': title,
                        'url': url if url.startswith('http') else f'https://news.ycombinator.com/{url}',
                        'source': 'Hacker News'
                    })
        return stories
    except Exception as e:
        print(f"Error scraping Hacker News: {e}", file=sys.stderr)
        return []

def scrape_reddit_programming() -> List[Dict]:
    """Scrape hot posts from r/programming"""
    try:
        url = 'https://www.reddit.com/r/programming/hot.json?limit=10'
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        stories = []
        for post in data['data']['children']:
            post_data = post['data']
            title = post_data['title']
            url = post_data['url']
            # Skip stickied posts or non-programming content
            if not post_data.get('stickied', False) and 'programming' in title.lower() or any(word in title.lower() for word in ['python', 'javascript', 'java', 'c++', 'rust', 'go', 'framework', 'language']):
                stories.append({
                    'title': title,
                    'url': url,
                    'source': 'Reddit r/programming'
                })
        return stories[:10]  # Limit to 10
    except Exception as e:
        print(f"Error scraping Reddit: {e}", file=sys.stderr)
        return []

def scrape_dev_to() -> List[Dict]:
    """Scrape recent articles from Dev.to"""
    try:
        url = 'https://dev.to/'
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        stories = []
        # Dev.to uses <article> or specific classes
        for article in soup.find_all('article')[:10]:
            title_tag = article.find('h2') or article.find('a', class_='crayons-link')
            if title_tag:
                title = title_tag.get_text(strip=True)
                url_tag = article.find('a', href=True)
                if url_tag:
                    url = 'https://dev.to' + url_tag['href'] if url_tag['href'].startswith('/') else url_tag['href']
                    stories.append({
                        'title': title,
                        'url': url,
                        'source': 'Dev.to'
                    })
        return stories
    except Exception as e:
        print(f"Error scraping Dev.to: {e}", file=sys.stderr)
        return []

def scrape_github_trending() -> List[Dict]:
    """Scrape trending repositories from GitHub"""
    try:
        url = 'https://github.com/trending'
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        stories = []
        for repo in soup.find_all('article', class_='Box-row')[:10]:
            title_tag = repo.find('h2', class_='h3')
            if title_tag:
                title = title_tag.get_text(strip=True).replace('\n', '').replace(' ', '')
                url_tag = title_tag.find('a')
                if url_tag:
                    url = 'https://github.com' + url_tag['href']
                    desc_tag = repo.find('p', class_='col-9')
                    description = desc_tag.get_text(strip=True) if desc_tag else 'No description'
                    full_title = f"{title} - {description}"
                    stories.append({
                        'title': full_title,
                        'url': url,
                        'source': 'GitHub Trending'
                    })
        return stories
    except Exception as e:
        print(f"Error scraping GitHub: {e}", file=sys.stderr)
        return []

def get_hot_topics() -> List[Dict]:
    """Main function to get all hot topics from all sources"""
    all_news = []

    # Scrape all sources
    sources = [
        ('Hacker News', scrape_hacker_news),
        ('Reddit r/programming', scrape_reddit_programming),
        ('Dev.to', scrape_dev_to),
        ('GitHub Trending', scrape_github_trending),
    ]

    for source_name, scraper_func in sources:
        news = scraper_func()
        all_news.extend(news)

    return all_news

def main():
    print("🔍 Scraping latest programming news...\n")

    all_news = get_hot_topics()

    print("📰 Latest Programming News:\n")
    print("=" * 80)

    for i, item in enumerate(all_news[:50], 1):  # Limit to 50 total
        print(f"{i:2d}. [{item['source']}] {item['title']}")
        print(f"    {item['url']}")
        print()

    print("=" * 80)
    print(f"Total news items: {len(all_news)}")

if __name__ == '__main__':
    main()