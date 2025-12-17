#!/usr/bin/env python3
"""
Dizipal M3U Oluşturucu
Amacı: Dizipal sitesindeki tüm film/dizi sayfa URL'lerini toplar.
Çıktı: dizipal.m3u (İçinde M3U8 değil, site içi sayfa bağlantıları bulunur)
"""

import cloudscraper
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse

class DizipalScraper:
    def __init__(self):
        # 1. ADIM: Güncel domain'i al
        self.base_url = self.get_current_domain()
        print(f"📍 Çalışılan Site: {self.base_url}")
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.all_urls = set()  # Tekrar eden URL'leri engellemek için

    def get_current_domain(self):
        """GitHub'dan güncel domain'i çeker."""
        try:
            domain_url = "https://raw.githubusercontent.com/koprulu555/domain-kontrol2/refs/heads/main/dizipaldomain.txt"
            response = requests.get(domain_url, timeout=10)
            for line in response.text.splitlines():
                if line.startswith("guncel_domain="):
                    domain = line.split('=', 1)[1].strip()
                    if domain:
                        return domain.rstrip('/')
        except Exception as e:
            print(f"⚠️  Domain alınırken hata: {e}")
        
        # Yedek domain (proje açıklamasında verilen)
        return "https://dizipal1222.com"

    def get_sitemap_urls(self):
        """Ana sitemap.xml'den tüm içerik URL'lerini toplar."""
        sitemap_url = urljoin(self.base_url, "/sitemap.xml")
        print(f"🗺️  Site haritası taranıyor: {sitemap_url}")
        
        try:
            resp = self.scraper.get(sitemap_url, timeout=30)
            soup = BeautifulSoup(resp.content, 'lxml-xml')
            urls = []
            
            # Sitemap içindeki <loc> etiketlerini bul
            for loc in soup.find_all('loc'):
                url = loc.text.strip()
                if self.base_url in url:
                    urls.append(url)
            
            print(f"✅ Site haritasından {len(urls)} URL bulundu.")
            return urls
        except Exception as e:
            print(f"❌ Site haritası alınamadı: {e}")
            return []

    def classify_and_filter_urls(self, urls):
        """URL'leri kategorilere ayırır ve filtreler."""
        categories = {
            'diziler': [],
            'filmler': [],
            'platforms': {}
        }
        
        # Platform listesi (senin belirttiğin gibi)
        platform_keywords = {
            'netflix': 'NETFLİX',
            'exxen': 'GAIN',
            'blutv': 'BluTV',
            'disney': 'Disney+',
            'amazon-prime': 'Amazon Prime',
            'tod-bein': 'TOD',
            'gain': 'GAIN',
            'mubi': 'Mubi'
        }
        
        for url in urls:
            # 1. Dizi bölümlerini bul (sezon/bolum pattern'i)
            if '/dizi/' in url and '/sezon-' in url and '/bolum-' in url:
                categories['diziler'].append(url)
            
            # 2. Film sayfalarını bul (film/ ile başlayan veya film- içeren)
            elif '/film/' in url or '/film-' in url:
                categories['filmler'].append(url)
            
            # 3. Platform koleksiyonlarını bul
            for keyword, platform_name in platform_keywords.items():
                if keyword in url:
                    if platform_name not in categories['platforms']:
                        categories['platforms'][platform_name] = []
                    categories['platforms'][platform_name].append(url)
                    break
        
        print(f"📊 Sınıflandırma: {len(categories['diziler'])} dizi, {len(categories['filmler'])} film")
        for platform, links in categories['platforms'].items():
            print(f"   - {platform}: {len(links)} içerik")
        
        return categories

    def generate_m3u_content(self, categories):
        """Kategorilerden M3U içeriği oluşturur."""
        m3u_lines = ['#EXTM3U']
        
        # DİZİLER
        m3u_lines.append('\n# KATEGORI: DİZİLER')
        for url in sorted(categories['diziler'])[:500]:  # İlk 500'ü al (sınırlama)
            # Dizi adını URL'den çıkar
            name = self.extract_name_from_url(url)
            m3u_lines.append(f'#EXTINF:-1, {name}')
            m3u_lines.append(url)
        
        # FİLMLER
        m3u_lines.append('\n# KATEGORI: FİLMLER')
        for url in sorted(categories['filmler'])[:300]:
            name = self.extract_name_from_url(url)
            m3u_lines.append(f'#EXTINF:-1, {name}')
            m3u_lines.append(url)
        
        # PLATFORMLAR
        for platform_name, urls in sorted(categories['platforms'].items()):
            m3u_lines.append(f'\n# KATEGORI: {platform_name.upper()}')
            for url in urls[:100]:
                name = self.extract_name_from_url(url)
                m3u_lines.append(f'#EXTINF:-1, {name}')
                m3u_lines.append(url)
        
        return '\n'.join(m3u_lines)

    def extract_name_from_url(self, url):
        """URL'den insanların okuyabileceği bir isim çıkarır."""
        # Örnek: https://dizipal1222.com/dizi/enfes-bir-aksam/sezon-1/bolum-1
        # Çıktı: Enfes Bir Aksam S01E01
        
        parsed = urlparse(url)
        path = parsed.path
        
        # Dizi bölümü için
        if '/sezon-' in path and '/bolum-' in path:
            match = re.search(r'/dizi/([^/]+)/sezon-(\d+)/bolum-(\d+)', path)
            if match:
                name = match.group(1).replace('-', ' ').title()
                season = match.group(2).zfill(2)
                episode = match.group(3).zfill(2)
                return f"{name} S{season}E{episode}"
        
        # Film veya dizi ana sayfası için
        match = re.search(r'/(?:dizi|film)/([^/]+)', path)
        if match:
            name = match.group(1).replace('-', ' ').title()
            return name
        
        return "İsimsiz İçerik"

    def run(self):
        """Ana çalıştırma fonksiyonu."""
        print("🚀 Dizipal M3U Oluşturucu Başlıyor...")
        
        # 1. Sitemap'ten URL'leri al
        all_urls = self.get_sitemap_urls()
        if not all_urls:
            print("❌ Site haritası boş, alternatif yöntem deneniyor...")
            # Alternatif yöntem eklenebilir
            return
        
        # 2. URL'leri sınıflandır
        categories = self.classify_and_filter_urls(all_urls)
        
        # 3. M3U içeriğini oluştur
        m3u_content = self.generate_m3u_content(categories)
        
        # 4. Dosyaya yaz
        with open('dizipal.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"✅ İşlem tamam! Toplam {len(m3u_content.splitlines())} satır yazıldı.")
        print(f"📁 Çıktı: dizipal.m3u")

if __name__ == "__main__":
    scraper = DizipalScraper()
    scraper.run()
