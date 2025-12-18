#!/usr/bin/env python3
"""
TAM DİZİPAL SCRAPER - Tüm içerikleri kategorilere göre çeker
"""

import cloudscraper
import requests
import re
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

class DizipalScraper:
    def __init__(self):
        self.base_url = self.get_current_domain()
        print(f"🔗 Domain: {self.base_url}")
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url
        })
        self.all_links = []
        self.categories = {
            'DİZİLER': {},
            'FİLMLER': {},
            'PLATFORMLAR': {}
        }
        
        # CloudStream kodundaki kategori yapısı
        self.film_turleri = {
            'aksiyon': 2,
            'macera': 13,
            'animasyon': 3,
            'komedi': 11,
            'korku': 12,
            'gerilim': 9,
            'dram': 7,
            'fantastik': 8,
            'bilimkurgu': 5,
            'aile': 1,
            'belgesel': 4,
            'biyografi': 6,
            'muzik': 14,
            'romantik': 16,
            'savas': 17,
            'spor': 18,
            'suç': 19,
            'tarih': 20,
            'western': 21,
            'yerli': 24,
            'erotik': 25
        }
        
        self.dizi_turleri = {
            'aksiyon': 2,
            'macera': 13,
            'animasyon': 3,
            'komedi': 11,
            'korku': 12,
            'gerilim': 9,
            'dram': 7,
            'fantastik': 8,
            'bilimkurgu': 5,
            'aile': 1,
            'belgesel': 4,
            'suç': 19,
            'tarih': 20,
            'polisiye': 10,
            'yerli': 24,
            'erotik': 25,
            'anime': 26
        }
        
        self.platformlar = {
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

    def crawl_with_pagination(self, base_url, category_name, is_dizi=False):
        """Sayfalandırma ile tüm içerikleri çek"""
        print(f"\n📂 {category_name} taranıyor...")
        page = 1
        all_items = []
        
        while True:
            if is_dizi:
                url = f"{base_url}&sayfa={page}"
            else:
                url = f"{base_url}&sayfa={page}"
            
            try:
                print(f"   Sayfa {page}: {url}")
                r = self.scraper.get(url, timeout=30)
                soup = BeautifulSoup(r.content, 'html.parser')
                
                # Film/Dizi linklerini bul
                items = soup.select('article.type2 ul li a')
                if not items:
                    items = soup.select('div.episode-item a')
                
                if not items:
                    print(f"   ⏹️  Sayfa {page}: içerik bulunamadı, durduruluyor...")
                    break
                
                found_count = 0
                for item in items:
                    href = item.get('href', '')
                    if href and (href.startswith('/dizi/') or href.startswith('/film/')):
                        full_url = urljoin(self.base_url, href)
                        if full_url not in all_items:
                            all_items.append(full_url)
                            found_count += 1
                
                print(f"   ✅ Sayfa {page}: {found_count} içerik bulundu")
                
                # Sonraki sayfa var mı kontrol et
                next_page = soup.select_one('a[rel="next"]')
                if not next_page:
                    break
                    
                page += 1
                time.sleep(1)  # Sunucu yükünü azalt
                
            except Exception as e:
                print(f"   ❌ Sayfa {page} hatası: {e}")
                break
        
        print(f"   📊 Toplam: {len(all_items)} içerik")
        return all_items

    def get_all_episodes(self, dizi_url):
        """Bir dizinin tüm sezon ve bölümlerini çek"""
        episodes = []
        try:
            print(f"    🔍 Bölümler taranıyor: {dizi_url}")
            r = self.scraper.get(dizi_url, timeout=30)
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Sezon listesini bul
            sezon_select = soup.select_one('select[name="sezon"]')
            if sezon_select:
                sezon_options = sezon_select.select('option')
                sezon_nolar = [opt['value'] for opt in sezon_options if opt['value'].isdigit()]
                
                for sezon_no in sezon_nolar:
                    sezon_url = f"{dizi_url}/sezon-{sezon_no}"
                    try:
                        r2 = self.scraper.get(sezon_url, timeout=30)
                        soup2 = BeautifulSoup(r2.content, 'html.parser')
                        
                        # Bölüm linklerini bul
                        bolum_links = soup2.select('div.episode-item a')
                        for link in bolum_links:
                            href = link.get('href', '')
                            if href and '/bolum-' in href:
                                full_url = urljoin(self.base_url, href)
                                if full_url not in episodes:
                                    episodes.append(full_url)
                        
                        time.sleep(0.5)
                    except:
                        continue
            else:
                # Direkt bölüm listesi
                bolum_links = soup.select('div.episode-item a')
                for link in bolum_links:
                    href = link.get('href', '')
                    if href and '/bolum-' in href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in episodes:
                            episodes.append(full_url)
            
        except Exception as e:
            print(f"    ❌ Bölüm çekme hatası: {e}")
        
        return episodes

    def crawl_films_by_year_and_category(self):
        """Filmleri yıl ve türe göre çek"""
        print("\n🎬 FİLMLER taranıyor...")
        
        # Yıllar (2025'ten 1960'a)
        years = list(range(2025, 1959, -1))
        
        for tur_name, tur_id in self.film_turleri.items():
            print(f"\n   🎞️  {tur_name.upper()} filmleri:")
            for year in years:
                url = f"{self.base_url}/filmler?kelime=&yil={year}&tur={tur_id}&siralama="
                films = self.crawl_with_pagination(url, f"{tur_name} {year}", False)
                
                for film_url in films:
                    if film_url not in self.all_links:
                        self.all_links.append(film_url)
                        if tur_name not in self.categories['FİLMLER']:
                            self.categories['FİLMLER'][tur_name] = []
                        self.categories['FİLMLER'][tur_name].append(film_url)
                
                if not films:
                    continue  # Bu yılda film yok, diğer yıla geç
                
                time.sleep(2)

    def crawl_series_by_category(self):
        """Dizileri türe göre çek"""
        print("\n📺 DİZİLER taranıyor...")
        
        for tur_name, tur_id in self.dizi_turleri.items():
            print(f"\n   📺 {tur_name.upper()} dizileri:")
            url = f"{self.base_url}/diziler?kelime=&durum=&tur={tur_id}&type=&siralama="
            series_list = self.crawl_with_pagination(url, tur_name, True)
            
            for series_url in series_list:
                if '/dizi/' in series_url and '/sezon-' not in series_url:
                    # Dizinin tüm bölümlerini çek
                    episodes = self.get_all_episodes(series_url)
                    
                    for episode_url in episodes:
                        if episode_url not in self.all_links:
                            self.all_links.append(episode_url)
                            if tur_name not in self.categories['DİZİLER']:
                                self.categories['DİZİLER'][tur_name] = []
                            self.categories['DİZİLER'][tur_name].append(episode_url)
            
            time.sleep(2)

    def crawl_platforms(self):
        """Platform koleksiyonlarını çek"""
        print("\n🏢 PLATFORMLAR taranıyor...")
        
        for platform_key, platform_name in self.platformlar.items():
            print(f"\n   🏢 {platform_name}:")
            url = f"{self.base_url}/koleksiyon/{platform_key}"
            
            try:
                r = self.scraper.get(url, timeout=30)
                soup = BeautifulSoup(r.content, 'html.parser')
                
                # Platformdaki tüm içerikleri bul
                items = soup.select('article.type2 ul li a')
                for item in items:
                    href = item.get('href', '')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        
                        if '/dizi/' in full_url and '/sezon-' not in full_url:
                            # Dizi ise tüm bölümleri çek
                            episodes = self.get_all_episodes(full_url)
                            for episode_url in episodes:
                                if episode_url not in self.all_links:
                                    self.all_links.append(episode_url)
                                    if platform_name not in self.categories['PLATFORMLAR']:
                                        self.categories['PLATFORMLAR'][platform_name] = []
                                    self.categories['PLATFORMLAR'][platform_name].append(episode_url)
                        elif '/film/' in full_url:
                            # Film ise direkt ekle
                            if full_url not in self.all_links:
                                self.all_links.append(full_url)
                                if platform_name not in self.categories['PLATFORMLAR']:
                                    self.categories['PLATFORMLAR'][platform_name] = []
                                self.categories['PLATFORMLAR'][platform_name].append(full_url)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ {platform_name} hatası: {e}")

    def extract_name_from_url(self, url):
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

    def generate_m3u(self):
        """M3U dosyasını oluştur"""
        print("\n📝 M3U dosyası oluşturuluyor...")
        
        m3u_lines = ['#EXTM3U']
        
        # DİZİLER (türlere göre)
        for tur_name, urls in sorted(self.categories['DİZİLER'].items()):
            if urls:
                m3u_lines.append(f'\n# KATEGORİ: DİZİLER - {tur_name.upper()}')
                # Bölümleri sırala (1,2,3... şeklinde)
                sorted_urls = sorted(urls, key=lambda x: (
                    re.search(r'/sezon-(\d+)', x).group(1) if re.search(r'/sezon-(\d+)', x) else '0',
                    int(re.search(r'/bolum-(\d+)', x).group(1)) if re.search(r'/bolum-(\d+)', x) else 0
                ))
                
                for url in sorted_urls:
                    name = self.extract_name_from_url(url)
                    m3u_lines.append(f'#EXTINF:-1, {name}')
                    m3u_lines.append(url)
        
        # FİLMLER (türlere göre)
        for tur_name, urls in sorted(self.categories['FİLMLER'].items()):
            if urls:
                m3u_lines.append(f'\n# KATEGORİ: FİLMLER - {tur_name.upper()}')
                sorted_urls = sorted(list(set(urls)))  # Tekrarları kaldır ve sırala
                for url in sorted_urls:
                    name = self.extract_name_from_url(url)
                    m3u_lines.append(f'#EXTINF:-1, {name}')
                    m3u_lines.append(url)
        
        # PLATFORMLAR
        for platform_name, urls in sorted(self.categories['PLATFORMLAR'].items()):
            if urls:
                m3u_lines.append(f'\n# KATEGORİ: {platform_name.upper()}')
                sorted_urls = sorted(list(set(urls)))
                for url in sorted_urls:
                    name = self.extract_name_from_url(url)
                    m3u_lines.append(f'#EXTINF:-1, {name}')
                    m3u_lines.append(url)
        
        return '\n'.join(m3u_lines)

    def run(self):
        """Ana fonksiyon"""
        print("=" * 60)
        print("🚀 DİZİPAL TAM SCRAPER BAŞLIYOR")
        print("=" * 60)
        
        # 1. Filmleri çek
        self.crawl_films_by_year_and_category()
        
        # 2. Dizileri çek
        self.crawl_series_by_category()
        
        # 3. Platformları çek
        self.crawl_platforms()
        
        # 4. İstatistik
        print("\n" + "=" * 60)
        print("📊 İSTATİSTİKLER:")
        print("=" * 60)
        
        total_dizi = sum(len(urls) for urls in self.categories['DİZİLER'].values())
        total_film = sum(len(urls) for urls in self.categories['FİLMLER'].values())
        total_platform = sum(len(urls) for urls in self.categories['PLATFORMLAR'].values())
        
        print(f"   Toplam Dizi Bölümü: {total_dizi}")
        print(f"   Toplam Film: {total_film}")
        print(f"   Toplam Platform İçeriği: {total_platform}")
        print(f"   GENEL TOPLAM: {total_dizi + total_film + total_platform}")
        
        # Kategori detayları
        print("\n   Dizi Kategorileri:")
        for tur, urls in sorted(self.categories['DİZİLER'].items()):
            if urls:
                print(f"     - {tur.upper()}: {len(urls)} bölüm")
        
        print("\n   Film Kategorileri:")
        for tur, urls in sorted(self.categories['FİLMLER'].items()):
            if urls:
                print(f"     - {tur.upper()}: {len(urls)} film")
        
        print("\n   Platformlar:")
        for platform, urls in sorted(self.categories['PLATFORMLAR'].items()):
            if urls:
                print(f"     - {platform}: {len(urls)} içerik")
        
        # 5. M3U oluştur
        m3u_content = self.generate_m3u()
        
        # 6. Dosyaya yaz
        with open('dizipal.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print("\n" + "=" * 60)
        print(f"✅ BAŞARIYLA TAMAMLANDI!")
        print(f"📁 Çıktı: dizipal.m3u ({len(m3u_content.splitlines())} satır)")
        print("=" * 60)

if __name__ == "__main__":
    scraper = DizipalScraper()
    scraper.run()
