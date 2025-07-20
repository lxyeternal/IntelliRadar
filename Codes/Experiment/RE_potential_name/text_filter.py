import re
import nltk
import os
from nltk.corpus import stopwords

# 下载停用词（如果需要）
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

def load_common_words(file_path):
    """加载常见词文件"""
    common_words = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                common_words.add(line.strip().lower())
        print(f"已加载 {len(common_words)} 个常见词")
    except Exception as e:
        print(f"加载常见词文件失败: {e}")
    return common_words

def extract_package_names(text, common_words=None):
    """
    从文本中提取潜在的包名称
    
    参数:
    text (str): 要分析的文本内容
    common_words (set): 常见词集合，用于过滤结果
    
    返回:
    list: 过滤后的潜在包名称列表
    """
    if common_words is None:
        common_words = set()
    
    # 使用与原代码相同的正则表达式
    regex = r"(?:@[a-zA-Z0-9\-]+\/)?[a-zA-Z0-9][a-zA-Z0-9\._\-]+"
    stop_words = set(stopwords.words('english'))
    
    unique_words = []
    try:
        # 找出所有匹配项
        matches = re.findall(regex, text)
        unique_matches = set(matches)
        
        # 打印第一步：正则匹配的结果
        print("\n第一步：正则表达式匹配结果")
        print("-" * 40)
        for i, match in enumerate(unique_matches):
            print(f"{i+1}. {match}")
        print(f"共找到 {len(unique_matches)} 个匹配项")
        print("-" * 40)
        
        # 处理每个匹配项
        for word in unique_matches:
            # 处理以点或逗号结尾的单词
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
    
    # 打印第一次过滤后的结果（过滤常见词后）
    print("\n中间步骤：过滤常见词后的结果")
    print("-" * 40)
    for i, word in enumerate(re_pkgnames):
        print(f"{i+1}. {word}")
    print(f"过滤常见词后剩余 {len(re_pkgnames)} 个词")
    print("-" * 40)
    
    # 过滤掉停用词
    filtered_words = [word for word in re_pkgnames if word.lower() not in stop_words]
    
    # 打印第二步：过滤停用词后的结果
    print("\n第二步：过滤停用词后的最终结果")
    print("-" * 40)
    for i, word in enumerate(filtered_words):
        print(f"{i+1}. {word}")
    print(f"最终剩余 {len(filtered_words)} 个潜在包名")
    print("-" * 40)
    
    return filtered_words

# 测试文本
test_text = """Threat analysts have discovered ten malicious Python packages on the PyPI repository, used to infect developer's systems with password-stealing malware. The fake packages used typosquatting to impersonate popular software projects and trick PyPI users into downloading them. Pyg-utils, Pymocks, PyProto2 – All three packages target AWS credentials and appear very similar to another set of packages discovered by Sonatype in June. The first even connects to the same domain ("pygrata.com"), while the other two target "pymocks.com"). Free-net-vpn and Free-net-vpn2 – User credential harvester published to a site mapped by a dynamic DNS mapping service. Although the discovered packages were reported by CheckPoint and removed from PyPI, software developers that downloaded them on their systems could still be at risk."""

# 尝试加载常见词文件
# 请根据您的实际路径修改
common_words_file = "/Users/blue/Documents/Github/SCC_Intelligence/archive/words.txt"  # 根据需要修改路径

# 检查文件是否存在
if os.path.exists(common_words_file):
    common_words = load_common_words(common_words_file)
else:
    print(f"警告: 常见词文件 '{common_words_file}' 不存在，将使用空集合")
    common_words = set()

# 运行提取
extracted_packages = extract_package_names(test_text, common_words)

# 输出结果
print("\n提取的潜在包名:")
for pkg in extracted_packages:
    print(f"- {pkg}")