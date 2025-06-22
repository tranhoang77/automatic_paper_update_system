import os
import time
import shutil
import requests
import xml.etree.ElementTree as ET
import hashlib
import json
from datetime import datetime, timedelta

class ArxivPaperDownloader:
    def __init__(self,
                 save_dir,
                 days_back=4,
                 max_results=200,
                 rate_limit_sleep=3,
                 categories=None,
                 metadata_json=None):
        self.save_dir = save_dir
        self.max_results = max_results
        self.rate_limit_sleep = rate_limit_sleep
        self.base_url = 'http://export.arxiv.org/api/query?'
        self.ns = {'atom': 'http://www.w3.org/2005/Atom'}
        self.now = datetime.utcnow()
        self.cutoff = self.now - timedelta(days=days_back)
        # self.categories = categories or [
        #     'cs.AI', 'cs.AR', 'cs.CC', 'cs.CE', 'cs.CG', 'cs.CL', 'cs.CR', 'cs.CV',
        #     'cs.CY', 'cs.DB', 'cs.DC', 'cs.DL', 'cs.DM', 'cs.DS', 'cs.ET', 'cs.FL',
        #     'cs.GL', 'cs.GR', 'cs.GT', 'cs.HC', 'cs.IR', 'cs.IT', 'cs.LG', 'cs.LO',
        #     'cs.MA', 'cs.MM', 'cs.MS', 'cs.NA', 'cs.NE', 'cs.NI', 'cs.OH', 'cs.OS',
        #     'cs.PF', 'cs.PL', 'cs.RO', 'cs.SC', 'cs.SE', 'cs.SI', 'cs.SY'
        # ]
        self.categories = categories or [
            'cs.AI'
        ]

        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)
        os.makedirs(self.save_dir) 
         
        self.metadata_dict = {}  # key = hash, value = metadata
        self.metadata_json = metadata_json or os.path.join(self.save_dir, 'metadata.json')

        self._load_existing_metadata()

    def _load_existing_metadata(self):
        if os.path.exists(self.metadata_json):
            with open(self.metadata_json, 'r', encoding='utf-8') as f:
                self.metadata_dict = json.load(f)
        print(f"Found {len(self.metadata_dict)} existing entries in metadata.")

    def _save_metadata(self):
        with open(self.metadata_json, 'w', encoding='utf-8') as f:
            json.dump(self.metadata_dict, f, indent=2, ensure_ascii=False)

    def process_category(self, category):
        print(f"\n=== Processing category: {category} ===")
        start = 0
        downloaded = 0
        in_range = 0

        while True:
            query = (
                f"search_query=cat:{category}"
                f"&sortBy=submittedDate&sortOrder=descending"
                f"&start={start}&max_results={self.max_results}"
            )
            url = self.base_url + query
            print(f"  Fetching entries {start} to {start + self.max_results}...")

            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  Error: {e}")
                break

            root = ET.fromstring(resp.text)
            entries = root.findall('atom:entry', self.ns)
            if not entries:
                break

            too_old = 0

            for entry in entries:
                pub_elem = entry.find('atom:published', self.ns)
                if pub_elem is None:
                    continue

                pub_str = pub_elem.text
                pub_dt = datetime.strptime(pub_str, '%Y-%m-%dT%H:%M:%SZ')
                if pub_dt < self.cutoff or pub_dt > self.now:
                    too_old += 1
                    continue

                in_range += 1
                abstract_url = entry.find('atom:id', self.ns).text
                pdf_url = next((l.attrib['href'] for l in entry.findall('atom:link', self.ns)
                                if l.attrib.get('title') == 'pdf'), None)
                if not pdf_url:
                    continue

                hash_input = (abstract_url + pdf_url).encode('utf-8')
                file_hash = hashlib.md5(hash_input).hexdigest()

                if file_hash in self.metadata_dict:
                    continue

                pdf_path = os.path.join(self.save_dir, f"{file_hash}.pdf")

                # Save metadata to dict
                self.metadata_dict[file_hash] = {
                    'abstract_url': abstract_url,
                    'pdf_url': pdf_url,
                    'published': pub_str,
                    'category': category
                }

                try:
                    pdf_resp = requests.get(pdf_url, timeout=60)
                    pdf_resp.raise_for_status()
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_resp.content)
                    print(f"    ✓ Downloaded {file_hash}.pdf")
                    downloaded += 1
                    time.sleep(1)
                except requests.RequestException as e:
                    print(f"    Download error: {e}")

            if too_old > len(entries) * 0.9:
                print("  Too many old papers, stop this category.")
                break

            start += self.max_results
            time.sleep(self.rate_limit_sleep)

        return downloaded, in_range

    def run(self):
        total_dl = 0
        total_in = 0

        for i, cat in enumerate(self.categories, 1):
            print(f"\n--- {i}/{len(self.categories)} ---")
            dl, rng = self.process_category(cat)
            total_dl += dl
            total_in += rng

            if i < len(self.categories):
                time.sleep(self.rate_limit_sleep)

        self._save_metadata()

        print("\n=== SUMMARY ===")
        print(f"Downloaded: {total_dl}")
        print(f"In range: {total_in}")
        print(f"Total stored: {len(self.metadata_dict)}")

    def get_abstract_url_from_hash(self, hash_value):
        return self.metadata_dict.get(hash_value, {}).get('pdf_url')

