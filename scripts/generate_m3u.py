#!/usr/bin/env python3
"""
Dizipal M3U Generator
Fetches video URLs from Dizipal website and generates an M3U playlist.
"""

import cloudscraper
from parsel import Selector
import re
from urllib.parse import urljoin, urlparse
import requests
import time
import sys
import datetime

def fetch_page(url, scraper):
    """Fetch page content using CloudScraper."""
    try:
        resp = scraper.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_current_domain():
    """Get current domain from raw GitHub URL."""
    try:
        url = "https://raw.githubusercontent.com/koprulu555/domain-kontrol2/refs/heads/main/dizipaldomain.txt"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            line = resp.text.strip()
            if line.startswith("guncel_domain="):
                domain = line.split("=", 1)[1].strip()
                if not domain.endswith('/'):
                    domain += '/'
                return domain
    except Exception as e:
        print(f"Error fetching current domain: {e}")
    # fallback
    return "https://dizipal1222.com/"

def get_sitemap_urls(domain, limit_months=3):
    """Extract URLs from sitemap files."""
    sitemap_index_url = urljoin(domain, "sitemap.xml")
    scraper = cloudscraper.create_scraper()
    text = fetch_page(sitemap_index_url, scraper)
    if not text:
        return []
    # each line is a sitemap URL
    lines = text.strip().split('\n')
    sitemap_urls = []
    for line in lines:
        line = line.strip()
        if line.startswith('http'):
            sitemap_urls.append(line)
    # filter recent months
    today = datetime.datetime.now()
    recent_sitemaps = []
    for sitemap_url in sitemap_urls:
        match = re.search(r'sitemap-(\d{4})-(\d{2})\.xml', sitemap_url)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            sitemap_date = datetime.datetime(year, month, 1)
            if (today - sitemap_date).days < limit_months * 30:
                recent_sitemaps.append(sitemap_url)
        else:
            recent_sitemaps.append(sitemap_url)
    all_urls = []
    for sitemap_url in recent_sitemaps:
        parsed = urlparse(sitemap_url)
        path = parsed.path
        new_url = urljoin(domain, path)
        text2 = fetch_page(new_url, scraper)
        if not text2:
            continue
        lines2 = text2.strip().split('\n')
        for line2 in lines2:
            line2 = line2.strip()
            if line2.startswith('http'):
                url = line2.split()[0]
                parsed2 = urlparse(url)
                path2 = parsed2.path
                new_url2 = urljoin(domain, path2)
                all_urls.append(new_url2)
    return all_urls

def classify_urls(urls):
    """Classify URLs into series main pages and film pages."""
    series_main = []
    film_main = []
    for url in urls:
        if '/dizi/' in url and '/sezon-' not in url and '/bolum-' not in url:
            series_main.append(url)
        elif '/film/' in url:
            film_main.append(url)
    return series_main, film_main

def get_episodes_from_series(url, scraper):
    """Extract episode list from series main page."""
    html = fetch_page(url, scraper)
    if not html:
        return []
    selector = Selector(html)
    episodes = []
    for ep in selector.css("div.episode-item"):
        name = ep.css("div.name::text").get()
        href = ep.css("a::attr(href)").get()
        if not href:
            continue
        full_url = urljoin(url, href)
        episode_text = ep.css("div.episode::text").get()
        season = None
        episode = None
        if episode_text:
            match = re.search(r'(\d+)\. Sezon\s*(\d+)\. Bölüm', episode_text)
            if match:
                season = int(match.group(1))
                episode = int(match.group(2))
        episodes.append({
            'name': name,
            'url': full_url,
            'season': season,
            'episode': episode
        })
    return episodes

def get_m3u8_from_page(url, scraper, referer):
    """Extract M3U8 URL from video page."""
    html = fetch_page(url, scraper)
    if not html:
        return None
    selector = Selector(html)
    iframe_src = selector.css(".series-player-container iframe::attr(src)").get()
    if not iframe_src:
        iframe_src = selector.css("div#vast_new iframe::attr(src)").get()
    if not iframe_src:
        return None
    iframe_url = urljoin(referer, iframe_src)
    iframe_html = fetch_page(iframe_url, scraper)
    if not iframe_html:
        return None
    match = re.search(r'file:"([^"]+)"', iframe_html)
    if match:
        return match.group(1)
    match = re.search(r'file: "([^"]+)"', iframe_html)
    if match:
        return match.group(1)
    match = re.search(r'src="([^"]+\.m3u8)"', iframe_html)
    if match:
        return match.group(1)
    return None

def main():
    domain = get_current_domain()
    print(f"Using domain: {domain}")
    scraper = cloudscraper.create_scraper()
    print("Fetching sitemap URLs...")
    urls = get_sitemap_urls(domain, limit_months=3)
    print(f"Total URLs found: {len(urls)}")
    series_main, film_main = classify_urls(urls)
    print(f"Series main pages: {len(series_main)}")
    print(f"Film pages: {len(film_main)}")
    m3u_lines = ["#EXTM3U"]
    # process series
    for series_url in series_main:
        print(f"Processing series: {series_url}")
        episodes = get_episodes_from_series(series_url, scraper)
        for ep in episodes:
            m3u8 = get_m3u8_from_page(ep['url'], scraper, domain)
            if m3u8:
                season = ep['season'] or 1
                episode = ep['episode'] or 1
                title = f"{ep['name']} S{season:02d}E{episode:02d}"
                m3u_lines.append(f"#EXTINF:-1, {title}")
                m3u_lines.append(m3u8)
        time.sleep(0.5)
    # process films
    for film_url in film_main:
        print(f"Processing film: {film_url}")
        m3u8 = get_m3u8_from_page(film_url, scraper, domain)
        if m3u8:
            title = film_url.split('/')[-1].replace('-', ' ').title()
            m3u_lines.append(f"#EXTINF:-1, {title}")
            m3u_lines.append(m3u8)
        time.sleep(0.5)
    # write file
    with open('dizipal.m3u', 'w', encoding='utf-8') as f:
        f.write('\n'.join(m3u_lines))
    print(f"Total entries: {len(m3u_lines)//2}")

if __name__ == '__main__':
    main()
