import csv
from google.cloud import bigquery


class MalPkgMetaInfo:

    def __init__(self):
        self.client = bigquery.Client()
        self.metainfo_csv = "database/metainfo.csv"
        self.download_csv = "database/download.csv"
        self.metainfo_query = "SELECT metadata_version, name, version, author, platform, upload_time FROM `bigquery-public-data.pypi.distribution_metadata` WHERE name = {}"
        self.download_query = "SELECT timestamp, country_code, project, file.filename, file.project, file.version, file.type, details.installer.name FROM `bigquery-public-data.pypi.file_downloads` WHERE file.project = {} AND DATE(timestamp) BETWEEN DATE('2023-12-10') AND DATE('2023-12-12');"

    def write_to_csv(self, row_data, csv_file):
        with open(csv_file, "a", encoding="utf-8", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(row_data)

    def get_metainfo(self, package_name):
        pkg_metainfo_query = self.metainfo_query.format("\'" + package_name + "\'")
        query_job = self.client.query(pkg_metainfo_query)
        query_result = query_job.result()
        header = [field.name for field in query_result.schema]
        self.write_to_csv(header, self.metainfo_csv)
        for row in query_result:
            row_values = [str(value) if value is not None else "" for value in row]
            self.write_to_csv(row_values, self.metainfo_csv)

    def get_download_info(self, package_name):
        pkg_download_query = self.download_query.format("\'" + package_name + "\'")
        query_job = self.client.query(pkg_download_query)
        query_result = query_job.result()
        header = [field.name for field in query_result.schema]
        self.write_to_csv(header, self.download_csv)
        for row in query_result:
            row_values = [str(value) if value is not None else "" for value in row]
            self.write_to_csv(row_values, self.download_csv)


if __name__ == '__main__':
    malpkg = MalPkgMetaInfo()
    metainfo = malpkg.get_metainfo("requests")
    downloadinfo = malpkg.get_download_info("request")
