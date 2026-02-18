import re
import nltk
import os
from nltk.corpus import stopwords

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


def load_common_words(file_path):
    """Load common words from file"""
    common_words = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                common_words.add(line.strip().lower())
        print(f"Loaded {len(common_words)} common words")
    except Exception as e:
        print(f"Failed to load common words file: {e}")
    return common_words


def extract_package_names(text, common_words=None):
    """
    Extract potential package names from text.

    Args:
        text (str): Text content to analyze
        common_words (set): Common words set for filtering results

    Returns:
        list: Filtered list of potential package names
    """
    if common_words is None:
        common_words = set()

    regex = r"(?:@[a-zA-Z0-9\-]+\/)?[a-zA-Z0-9][a-zA-Z0-9\._\-]+"
    stop_words = set(stopwords.words('english'))

    unique_words = []
    try:
        matches = re.findall(regex, text)
        unique_matches = set(matches)

        print("\nStep 1: Regex match results")
        print("-" * 40)
        for i, match in enumerate(unique_matches):
            print(f"{i+1}. {match}")
        print(f"Found {len(unique_matches)} matches")
        print("-" * 40)

        for word in unique_matches:
            if word.endswith(".") or word.endswith(","):
                word = word[:-1]
                if word.lower() not in common_words:
                    unique_words.append(word)
            else:
                if word.lower() not in common_words:
                    unique_words.append(word)

        re_pkgnames = set(unique_words)
    except Exception as e:
        print(f"Error extracting package names: {e}")
        re_pkgnames = set()

    print("\nIntermediate step: Results after filtering common words")
    print("-" * 40)
    for i, word in enumerate(re_pkgnames):
        print(f"{i+1}. {word}")
    print(f"Remaining after common word filter: {len(re_pkgnames)} words")
    print("-" * 40)

    filtered_words = [word for word in re_pkgnames if word.lower() not in stop_words]

    print("\nStep 2: Final results after stopword filter")
    print("-" * 40)
    for i, word in enumerate(filtered_words):
        print(f"{i+1}. {word}")
    print(f"Final remaining potential package names: {len(filtered_words)}")
    print("-" * 40)

    return filtered_words


test_text = """Threat analysts have discovered ten malicious Python packages on the PyPI repository, used to infect developer's systems with password-stealing malware. The fake packages used typosquatting to impersonate popular software projects and trick PyPI users into downloading them. Pyg-utils, Pymocks, PyProto2 – All three packages target AWS credentials and appear very similar to another set of packages discovered by Sonatype in June. The first even connects to the same domain ("pygrata.com"), while the other two target "pymocks.com"). Free-net-vpn and Free-net-vpn2 – User credential harvester published to a site mapped by a dynamic DNS mapping service. Although the discovered packages were reported by CheckPoint and removed from PyPI, software developers that downloaded them on their systems could still be at risk."""

common_words_file = "/Users/blue/Documents/Github/SCC_Intelligence/archive/words.txt"

if os.path.exists(common_words_file):
    common_words = load_common_words(common_words_file)
else:
    print(f"Warning: common words file '{common_words_file}' does not exist, using empty set")
    common_words = set()

extracted_packages = extract_package_names(test_text, common_words)

print("\nExtracted potential package names:")
for pkg in extracted_packages:
    print(f"- {pkg}")
