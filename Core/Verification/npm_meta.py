import csv
import json
import os
from bs4 import BeautifulSoup
import requests


class NpmMetaInfo:

    def __init__(self):
        self.versoin = None
        self.release_date = None
        self.pkgs_data = []

    def read_pkg_csv(self, csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                self.pkgs_data.append(row)

    def get_meta_info(self):
        for pkg in self.pkgs_data:
            pkg_name = pkg[0]
            source = pkg[1]
            base_dir = 'https://registry.npmjs.org/'
            if source == 'None':
                link = base_dir + pkg_name
                print(link)

    def write_snyk_time(self, data):
        with open("/Users/blue/Desktop/newtest.csv", "a") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(data)

    def npm_release_date(self):
        """Parse npm metadata files and enrich CSV records with release dates."""
        pkg_release_date = {}
        raw_data_files = os.listdir("/Users/blue/Downloads/npm_metainfo")
        for file in raw_data_files:
            file_path = os.path.join("/Users/blue/Downloads/npm_metainfo", file)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    p_tag = soup.find('p')
                    json_str = p_tag.text.strip()
                    data = json.loads(json_str)
                    pkg_name = data['name']
                    release_date = data['time']['created'].split('T')[0]
                    pkg_release_date[pkg_name] = release_date
            except:
                pass
        with open("/Users/blue/Desktop/our_snyk_osv_release_news_source_snyk_osv.csv", "r") as csvfile:
            csvreader = csv.reader(csvfile)
            for index, row in enumerate(csvreader):
                manager = row[1].strip()
                pkgname = row[0].strip()
                if manager == "None":
                    if pkgname in pkg_release_date:
                        release_date = pkg_release_date[pkgname]
                        row[1] = "npm"
                        row[4] = release_date
                        self.write_snyk_time(row)
                    else:
                        self.write_snyk_time(row)
                else:
                    self.write_snyk_time(row)


if __name__ == '__main__':
    npm_meta_info = NpmMetaInfo()
    npm_meta_info.npm_release_date()
