import os
import csv
import requests
from Configs.config import HEADER


class SnykPkgLookup:

    def __init__(self):
        self.snyk_vulndb = "https://security.snyk.io/vuln/{}?search={}"
        self.processed_pkgs = {"npm": set(), "pip": set()}
        self.processed_file = "/Users/blue/Desktop/new_snyk_check.csv"

    def read_csv_files(self, csv_file):
        csv_pkg_names = {"npm": [], "pip": []}
        with open(csv_file, encoding="utf-8-sig") as csvfile:
            csv_reader = csv.reader(csvfile)
            for pkgname, pkgmanager in csv_reader:
                csv_pkg_names[pkgmanager].append(pkgname)
        return csv_pkg_names

    def read_processed_pkgs(self):
        if os.path.exists(self.processed_file):
            with open(self.processed_file, "r") as csvfile:
                csv_reader = csv.reader(csvfile)
                for row in csv_reader:
                    pkg_name = row[1].strip()
                    pkg_manager = row[0].strip()
                    self.processed_pkgs[pkg_manager].add(pkg_name)

    def write_processed_pkgs(self, data):
        with open(self.processed_file, "a") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(data)

    def snyk_check(self, manager, pkgname):
        """Check whether a malicious package exists in the Snyk database."""
        response = requests.get(self.snyk_vulndb.format(manager, pkgname), headers=HEADER)
        if response.status_code == 200:
            if "No results found" in response.text:
                return False
            return True
        return False

    def osv_check(self, url):
        response = requests.get(self.osv_vulndb.format(url), headers=HEADER)
        if response.status_code == 200:
            if "No results" in response.text:
                return False
            return True
        return False

    def osv_check_api(self, package_name):
        url = "https://api.osv.dev/v1/query"
        headers = {'Content-Type': 'application/json'}
        for ecosystem in ["npm", "PyPI"]:
            data = {
                "package": {
                    "name": package_name,
                    "ecosystem": ecosystem
                }
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()
            else:
                return

    def batch_check(self, csv_file):
        csv_pkg_names = self.read_csv_files(csv_file)
        self.read_processed_pkgs()
        for manager, pkgname_list in csv_pkg_names.items():
            for pkgname in pkgname_list:
                if pkgname in self.processed_pkgs[manager]:
                    print(pkgname + " already processed")
                    continue
                snyk_result = self.snyk_check(manager, pkgname.strip())
                self.write_processed_pkgs([manager, pkgname, snyk_result])


class OSVPkgLookup:

    def __init__(self):
        self.osv_database_file = "database/osv_database.csv"
        self.github_database_file = "../Aggregate/github_maldata.csv"
        self.maldata_database_file = "/Users/blue/Desktop/new_phylum_pkgs.csv"
        self.osv_lookup_result = "/Users/blue/Desktop/osv_lookup.csv"
        self.osv_database = []
        self.maldata = []

    def load_osv_database(self):
        with open(self.osv_database_file, encoding="utf-8-sig") as csvfile:
            csv_reader = csv.reader(csvfile)
            for index, row in enumerate(csv_reader):
                if row[0] == "pypi":
                    self.osv_database.append(row[1])

    def load_maldata(self):
        with open(self.maldata_database_file, encoding="utf-8-sig") as csvfile:
            csv_reader = csv.reader(csvfile)
            for index, row in enumerate(csv_reader):
                self.maldata.append(row)

    def load_github_database(self):
        with open(self.github_database_file, encoding="utf-8-sig") as csvfile:
            csv_reader = csv.reader(csvfile)
            for index, row in enumerate(csv_reader):
                self.maldata.append(row[2])

    def write_osv_lookup(self, data):
        with open(self.osv_lookup_result, "a") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(data)

    def compare_lists(self, list1, list2):
        common_elements = set(list1).intersection(set(list2))
        common_elements_count = len(common_elements)
        unique_to_list1_count = len(set(list1) - set(list2))
        unique_to_list2_count = len(set(list2) - set(list1))
        print(common_elements_count, unique_to_list1_count, unique_to_list2_count)
        return common_elements_count, unique_to_list1_count, unique_to_list2_count

    def pkg_check(self):
        self.load_osv_database()
        self.load_maldata()
        self.load_github_database()
        for pkginfo in self.maldata:
            pkgname = pkginfo[0].strip()
            if pkgname in self.osv_database:
                self.write_osv_lookup(pkginfo + ["TRUE"])
            else:
                self.write_osv_lookup(pkginfo + ["FALSE"])


if __name__ == '__main__':
    pkglookup = SnykPkgLookup()
    pkglookup.batch_check("/Users/blue/Desktop/rq1_csv/new_dataset.csv")
