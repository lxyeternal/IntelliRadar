import os
from collections import defaultdict
from Core.Analysis.llm_batch_analyzer import LTMGPT
from Core.Aggregation.data_integrity import DataIntegrity
from Core.Collection.content_extractor import WebPageContent
from Core.Collection.blog_scraper import WebPageCollection


class IntelligencePipeline:

    def __init__(self):
        self.current_dir = os.path.dirname(__file__)
        self.project_dir = os.path.dirname(self.current_dir)
        self.webpage_content = WebPageContent()
        self.webpage_collection = WebPageCollection()
        self.ltmgpt = LTMGPT()
        self.dataintegrity = DataIntegrity()
        self.waiting_collection_file = os.path.join(self.current_dir, "Collection/pagelinks/waiting_collection.txt")
        self.collected_pagelinks_file = os.path.join(self.current_dir, "Collection/pagelinks/collected_pagelinks.txt")
        self.sources = defaultdict(list)


    def load_waiting_collection(self):
        """Load waiting links into dict format {source: [(timestamp, date, link)]}."""
        if not os.path.exists(self.waiting_collection_file):
            raise FileNotFoundError(f"{self.waiting_collection_file} not found.")
        with open(self.waiting_collection_file, 'r') as file:
            for line in file:
                timestamp, source, date, link = line.strip().split('\t')
                self.sources[source].append((timestamp, date, link))


    def extract_blogs(self):
        """Execute blog extraction tasks."""
        self.webpage_collection.load_old_webpages()
        # self.webpage_collection.snyk_blog()
        # self.webpage_collection.qianxin_blog()
        # self.webpage_collection.datadoghq_blog()
        # self.webpage_collection.jfrog_blog()
        # self.webpage_collection.github_blog()
        # self.webpage_collection.medium_recommand()
        # self.webpage_collection.medium_blog()
        # self.webpage_collection.checkmarx_blog()
        # self.webpage_collection.sonatype_oss_blog()
        # self.webpage_collection.sonatype_blog()
        # self.webpage_collection.bleepingcomputer_blog()
        # self.webpage_collection.securityaffairs_blog()
        # self.webpage_collection.fortinet_blog()
        # self.webpage_collection.phylum_blog()
        # self.webpage_collection.reversinglabs_blog()
        # self.webpage_collection.tuxcare_blog()
        # self.webpage_collection.cybersecuritynews_blog()
        # self.webpage_collection.rhisac_blog()
        # self.webpage_collection.socket_blog()
        # self.webpage_collection.checkpoint_blog()
        # self.webpage_collection.reddit_blog()


    def process_blogs(self):
        """Process blogs in waiting_collection.txt."""
        self.load_waiting_collection()
        for source, entries in self.sources.items():
            for entry in entries:
                timestamp, date, link = entry
                self.process_single_blog(source, timestamp, date, link)
                self.update_files(source, timestamp, date, link)


    def process_single_blog(self, source, timestamp, date, link):
        """Process a single blog link through extraction, LLM analysis, and aggregation."""
        print(f"Processing {source}: {link}")
        self.extract_webpage_content(source, timestamp, link)
        content_file_path = os.path.join(self.project_dir, "Dataset/Content/{source}/{timestamp}.txt".format(source=source, timestamp=timestamp))
        self.process_with_ltmgpt(source, content_file_path, f"{timestamp}.txt")
        json_file_path = os.path.join(self.project_dir, "Dataset/Json/{source}/{timestamp}_verify_gpt4.json".format(source=source, timestamp=timestamp))
        self.aggregate_json(source, json_file_path)


    def extract_webpage_content(self, source, timestamp, link):
        """Extract webpage content using the source-specific extraction method."""
        extract_method = getattr(self.webpage_content, f"{source}_content", None)
        if callable(extract_method):
            extract_method(timestamp, link)
        else:
            raise NotImplementedError(f"No content extraction method for source: {source}")


    def process_with_ltmgpt(self, source, content_file_path, content_file_name):
        """Call LLM for content analysis."""
        self.ltmgpt.process_content(source, content_file_path, content_file_name)


    def aggregate_json(self, source, json_file_path):
        """Aggregate parsed JSON files."""
        self.dataintegrity.process_files(source, json_file_path)


    def update_files(self, source, timestamp, date, link):
        """Remove processed link from waiting list and append to collected list."""
        self.remove_from_waiting_collection(timestamp, source, date, link)
        self.append_to_collected_pagelinks(timestamp, source, date, link)


    def remove_from_waiting_collection(self, timestamp, source, date, link):
        """Remove processed links from waiting_collection.txt."""
        lines_to_keep = []
        with open(self.waiting_collection_file, 'r') as file:
            for line in file:
                if line.strip() != f"{timestamp}\t{source}\t{date}\t{link}":
                    lines_to_keep.append(line)

        with open(self.waiting_collection_file, 'w') as file:
            file.writelines(lines_to_keep)


    def append_to_collected_pagelinks(self, timestamp, source, date, link):
        """Append processed links to collected_pagelinks.txt."""
        with open(self.collected_pagelinks_file, 'a') as file:
            file.write(f"{timestamp}\t{source}\t{date}\t{link}\n")


    def run_pipeline(self):
        """Run the entire pipeline."""
        # self.extract_blogs()
        self.process_blogs()


if __name__ == "__main__":
    pipeline = IntelligencePipeline()
    pipeline.run_pipeline()
