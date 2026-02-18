import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class OSVDatabase:

    def __init__(self):
        current_dir = os.path.dirname(__file__)
        codes_dir = os.path.dirname(current_dir)
        project_dir = os.path.dirname(codes_dir)
        self.chromedriver = os.path.join(project_dir, "utils/chromedriver/macarm/chromedriver")
        self.osv_baseurl = "https://osv.dev/list?ecosystem={}"
        service = Service(executable_path=self.chromedriver)
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=service, options=options)
        self.malicious_pkg_info = []

    def parse_osv_database(self, pkg_manager, page_index):
        self.driver.get(self.osv_baseurl.format(pkg_manager))
        self.driver.implicitly_wait(3)
        for i in range(page_index):
            try:
                wait = WebDriverWait(self.driver, 10)
                more_button_selector = ".next-page-button.link-button"
                more_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, more_button_selector)))
                self.driver.execute_script("arguments[0].scrollIntoView();", more_button)
                self.driver.execute_script("arguments[0].click();", more_button)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            except Exception as e:
                print(f"Error clicking next page: {e}")
                break
        vuln_table_contents = self.driver.find_element(By.CSS_SELECTOR, ".vuln-table-rows.mdc-data-table__content")
        vuln_table_rows = vuln_table_contents.find_elements(By.CSS_SELECTOR, ".vuln-table-row.mdc-data-table__row")
        for vuln_table_row in vuln_table_rows:
            vuln_id_link = vuln_table_row.find_element(By.CSS_SELECTOR, ".vuln-table-cell.mdc-data-table__cell").find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            vuln_package_manager = vuln_table_row.find_element(By.CSS_SELECTOR, ".vuln-table-cell.vuln-packages").text
            vuln_version_row = vuln_table_row.find_element(By.CSS_SELECTOR, ".vuln-table-cell.vuln-versions")
            vuln_versions = vuln_version_row.find_elements(By.CLASS_NAME, "version")
            malicious_versions = list()
            for vuln_version in vuln_versions:
                malicious_versions.append(vuln_version.text)
            vuln_data = vuln_table_row.find_element(By.TAG_NAME, "relative-time").text
            malicious_info = vuln_table_row.find_element(By.CSS_SELECTOR, ".vuln-table-cell.vuln-summary").text.strip()
            if "Malicious code in" in malicious_info:
                malicious_package_name = malicious_info.replace("Malicious code in", "").replace("(PyPI)", "").strip()
                malicious_manager = "PyPI"
                print(malicious_package_name, malicious_versions)
                self.malicious_pkg_info.append([vuln_id_link, malicious_package_name, malicious_manager, malicious_versions, vuln_data])


if __name__ == '__main__':
    osvdatabase = OSVDatabase()
    osvdatabase.parse_osv_database("PyPI", 10)
