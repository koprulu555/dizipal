#!/usr/bin/env python3
"""
DİZİPAL M3U OLUŞTURUCU
Sadece sayfa URL'lerini toplar: https://dizipal1222.com/dizi/enfes-bir-aksam/sezon-1/bolum-1
"""

import cloudscraper
import requests
import re
import time
from urllib.parse import urljoin

class DizipalScraper:
    def __init__(self):
        self.base_url = self.get_current_domain()
        print(f"🔗 Domain: {self.base_url}")
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.all_links = []
        self.platforms = {
            'netflix': 'NETFLİX',
            'exxen': 'GAIN', 
            'blutv': 'BluTV',
            'disney': 'Disney+',
            'amazon-prime': 'Amazon Prime',
            'tod-bein': 'TOD',
            'gain': 'GAIN',
            'mubi': 'Mubi'
        }

    def get_current_domain(self):
        """GitHub'dan güncel domain'i al"""
        try:
            url = "https://raw.githubusercontent.com/koprulu555/domain-kontrol2/refs/heads/main/dizipaldomain.txt"
            r = requests.get(url, timeout=10)
            for line in r.text.split('\n'):
                if line.startswith('guncel_domain='):
                    domain = line.split('=', 1)[1].strip()
                    if domain:
                        return domain.rstrip('/')
        except:
            pass
        return "https://dizipal1222.com"

    def get_sitemap(self):
        """Sitemap'ten tüm linkleri çek"""
        sitemap_url = f"{self.base_url}/sitemap.xml"
        print(f"📄 Sitemap: {sitemap_url}")
        
        try:
            r = self.scraper.get(sitemap_url, timeout=30)
            links = re.findall(r'<loc>(.*?)</loc>', r.text)
            return [link for link in links if self.base_url in link]
        except Exception as e:
            print(f"❌ Sitemap hatası: {e}")
            return []

    def crawl_category(self, url, category_name):
        """Kategori sayfasındaki tüm içerikleri bul"""
        print(f"🔍 {category_name} taranıyor: {url}")
        
        try:
            r = self.scraper.get(url, timeout=30)
            
            # Dizi linklerini bul (senin yapına göre)
            dizi_links = re.findall(r'href="(/dizi/[^"]+)"', r.text)
            for link in dizi_links:
                if '/sezon-' in link and '/bolum-' in link:
                    full_url = urljoin(self.base_url, link)
                    if full_url not in self.all_links:
                        self.all_links.append(full_url)
            
            # Film linklerini bul
            film_links = re.findall(r'href="(/film/[^"]+)"', r.text)
            for link in film_links:
                full_url = urljoin(self.base_url, link)
                if full_url not in self.all_links:
                    self.all_links.append(full_url)
                    
        except Exception as e:
            print(f"⚠️  {category_name} hatası: {e}")

    def organize_links(self):
        """Linkleri kategorilere ayır"""
        categories = {
            'DİZİLER': [],
            'FİLMLER': [],
            'PLATFORMLAR': {}
        }
        
        for link in self.all_links:
            # Platform kontrolü
            platform_found = False
            for key, name in self.platforms.items():
                if key in link:
                    if name not in categories['PLATFORMLAR']:
                        categories['PLATFORMLAR'][name] = []
                    categories['PLATFORMLAR'][name].append(link)
                    platform_found = True
                    break
            
            if not platform_found:
                if '/dizi/' in link:
                    categories['DİZİLER'].append(link)
                elif '/film/' in link:
                    categories['FİLMLER'].append(link)
        
        return categories

    def generate_m3u(self, categories):
        """M3U dosyasını oluştur"""
        m3u_content = ["#EXTM3U"]
        
        # DİZİLER
        m3u_content.append("\n# KATEGORİ: DİZİLER")
        for url in sorted(categories['DİZİLER'])[:1000]:  # İlk 1000
            name = self.extract_name(url)
            m3u_content.append(f"#EXTINF:-1, {name}")
            m3u_content.append(url)
        
        # FİLMLER
        m3u_content.append("\n# KATEGORİ: FİLMLER")
        for url in sorted(categories['FİLMLER'])[:500]:
            name = self.extract_name(url)
            m3u_content.append(f"#EXTINF:-1, {name}")
            m3u_content.append(url)
        
        # PLATFORMLAR
        for platform, urls in categories['PLATFORMLAR'].items():
            m3u_content.append(f"\n# KATEGORİ: {platform}")
            for url in urls[:200]:
                name = self.extract_name(url)
                m3u_content.append(f"#EXTINF:-1, {name}")
                m3u_content.append(url)
        
        return "\n".join(m3u_content)

    def extract_name(self, url):
        """URL'den isim çıkar"""
        # Örnek: /dizi/enfes-bir-aksam/sezon-1/bolum-1
        match = re.search(r'/(dizi|film)/([^/]+)', url)
        if match:
            name = match.group(2).replace('-', ' ').title()
            
            # Sezon/bölüm bilgisi
            season_match = re.search(r'/sezon-(\d+)', url)
            episode_match = re.search(r'/bolum-(\d+)', url)
            
            if season_match and episode_match:
                return f"{name} S{season_match.group(1).zfill(2)}E{episode_match.group(1).zfill(2)}"
            return name
        return "İsimsiz"

    def run(self):
        """Ana fonksiyon"""
        print("🚀 Dizipal M3U Oluşturucu Başlıyor...\n")
        
        # 1. Sitemap'ten link al
        sitemap_links = self.get_sitemap()
        
        # 2. Kategorileri tara
        categories_to_crawl = [
            (f"{self.base_url}/diziler", "Diziler"),
            (f"{self.base_url}/filmler", "Filmler"),
            (f"{self.base_url}/diziler/son-bolumler", "Son Bölümler"),
        ]
        
        # Platformları ekle
        for platform in self.platforms.keys():
            categories_to_crawl.append((f"{self.base_url}/koleksiyon/{platform}", platform))
        
        for url, name in categories_to_crawl:
            self.crawl_category(url, name)
            time.sleep(1)  # Sunucuyu yormamak için
        
        # 3. Linkleri düzenle
        categories = self.organize_links()
        
        print(f"\n📊 BULUNANLAR:")
        print(f"   Diziler: {len(categories['DİZİLER'])}")
        print(f"   Filmler: {len(categories['FİLMLER'])}")
        for platform, urls in categories['PLATFORMLAR'].items():
            print(f"   {platform}: {len(urls)}")
        
        # 4. M3U oluştur
        m3u_content = self.generate_m3u(categories)
        
        # 5. Dosyaya yaz
        with open('dizipal.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"\n✅ BAŞARILI! {len(m3u_content.splitlines())} satır yazıldı.")
        print(f"📁 Dosya: dizipal.m3u")

if __name__ == "__main__":
    scraper = DizipalScraper()
    scraper.run()
