import os
import csv
import json


def extract_json_files(directory):
    json_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
    return json_files


def write_csv(data):
    with open("database/osv_database.csv", "a", encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(data)


def osv_dataset():
    dataset_dir = "/Users/blue/Downloads/osv"
    pkg_managers = os.listdir(dataset_dir)
    for pkg_manager in pkg_managers:
        pkg_names = os.listdir(os.path.join(dataset_dir, pkg_manager))
        for pkg_name in pkg_names:
            json_files = extract_json_files(os.path.join(dataset_dir, pkg_manager, pkg_name))
            for pkg_malinfo_file in json_files:
                with open(pkg_malinfo_file, "r") as fr:
                    malinfo = json.load(fr)
                    affected_info = malinfo.get("affected", [])
                    published_info = malinfo.get("published", {}).split("T")[0]
                    for affected in affected_info:
                        package_info = affected.get("package", {})
                        package_name = package_info.get("name", "NA")
                        write_csv([pkg_manager, package_name, published_info])


osv_dataset()
