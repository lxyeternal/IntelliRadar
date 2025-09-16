let allData = [];
let currentPage = 1;
const itemsPerPage = 10;
let filteredData = [];
let selectedPackageManagers = new Set();

// 添加排序状态变量
let currentSort = {
    column: 'post_date', // 默认按日期排序
    direction: 'desc'    // 默认降序
};

// 获取数据
async function fetchData() {
    try {
        const response = await fetch('aggregated_packages.json');
        const rawData = await response.json();
        
        // 不再过滤数据，保留所有数据
        allData = rawData;
        filteredData = [...allData];
        
        // 初始化包管理器筛选器
        initializePackageManagerFilters();
        // 显示第一页数据
        sortAndRenderData(); // 使用新的排序函数
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('resultsContainer').innerHTML = 
            '<div class="error-message">数据加载失败，请稍后重试</div>';
    }
}

// 修改数据过滤函数
function filterValidData(data) {
    return data.filter(item => {
        // 基础检查：包名不能是 Unknown 或 CVE 格式
        if (!item['Package Name'] || 
            item['Package Name'].toLowerCase() === 'unknown' ||
            /^cve-\d{4}-\d+$/i.test(item['Package Name'])) {
            return false;
        }

        // 检查必需字段是否存在且有效
        const requiredFields = [
            'Package Manager',
            'Attack Vector',
            'Method of Attack',
            'post_date',
            'Source',
            'Discoverer',
            'Repository URL',
            'Indicators of Compromise'
        ];

        for (const field of requiredFields) {
            if (!item[field] || 
                item[field] === 'Unknown' || 
                item[field] === 'N/A' ||
                (Array.isArray(item[field]) && item[field].length === 0)) {
                return false;
            }
        }

        // 特殊处理数组类型的字段
        if (Array.isArray(item.Source)) {
            if (item.Source.some(source => !source || source === 'Unknown')) {
                return false;
            }
        }

        if (Array.isArray(item['Indicators of Compromise'])) {
            if (item['Indicators of Compromise'].length === 0 || 
                item['Indicators of Compromise'].some(ioc => !ioc || ioc === 'Unknown')) {
                return false;
            }
        }

        // 检查日期格式是否有效
        const date = new Date(item.post_date);
        if (isNaN(date.getTime())) {
            return false;
        }

        // 检查 URL 格式是否有效
        try {
            new URL(item['Repository URL']);
        } catch {
            return false;
        }

        // 所有检查都通过
        return true;
    });
}

// 初始化包管理器筛选器
function initializePackageManagerFilters() {
    // 获取所有包管理器并统计数量
    const packageManagerStats = allData.reduce((acc, item) => {
        const manager = item['Package Manager'];
        acc[manager] = (acc[manager] || 0) + 1;
        return acc;
    }, {});

    const packageManagers = Object.keys(packageManagerStats).sort();
    const filterContainer = document.getElementById('packageManagerFilters');
    
    // 更新侧边栏标题
    document.querySelector('.sidebar h3').innerHTML = `
        <span class="mdi mdi-filter-variant"></span>
        Package Manager
    `;
    
    packageManagers.forEach(manager => {
        const filterItem = document.createElement('div');
        filterItem.className = 'filter-item';
        filterItem.innerHTML = `
            <input type="checkbox" id="${manager}" value="${manager}">
            <label for="${manager}">
                <span class="checkbox-custom"></span>
                <span class="manager-name">${manager}</span>
            </label>
        `;
        filterContainer.appendChild(filterItem);

        filterItem.querySelector('input').addEventListener('change', (e) => {
            filterItem.classList.toggle('active', e.target.checked);
            if (e.target.checked) {
                selectedPackageManagers.add(manager);
            } else {
                selectedPackageManagers.delete(manager);
            }
            filterAndRenderResults();
        });
    });
}

// 搜索和筛选
function filterAndRenderResults() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    filteredData = allData.filter(item => {
        const matchesSearch = Object.values(item).some(value => 
            String(value).toLowerCase().includes(searchTerm)
        );
        
        const matchesPackageManager = selectedPackageManagers.size === 0 || 
            selectedPackageManagers.has(item['Package Manager']);
        
        return matchesSearch && matchesPackageManager;
    });
    
    currentPage = 1;
    renderResults();
}

// 渲染结果
function renderResults() {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';
    
    // 添加表头
    const headerRow = document.createElement('div');
    headerRow.className = 'package-header';
    headerRow.innerHTML = `
        <div class="header-cell" data-sort="Package Name">
            Package Name
            <span class="sort-icon ${currentSort.column === 'Package Name' ? `mdi mdi-arrow-${currentSort.direction === 'asc' ? 'up' : 'down'}` : 'mdi mdi-sort'}"></span>
        </div>
        <div class="header-cell" data-sort="Package Manager">
            Registry
            <span class="sort-icon ${currentSort.column === 'Package Manager' ? `mdi mdi-arrow-${currentSort.direction === 'asc' ? 'up' : 'down'}` : 'mdi mdi-sort'}"></span>
        </div>
        <div class="header-cell" data-sort="Package Version">
            Version
            <span class="sort-icon ${currentSort.column === 'Package Version' ? `mdi mdi-arrow-${currentSort.direction === 'asc' ? 'up' : 'down'}` : 'mdi mdi-sort'}"></span>
        </div>
        <div class="header-cell" data-sort="Source">
            Source
            <span class="sort-icon ${currentSort.column === 'Source' ? `mdi mdi-arrow-${currentSort.direction === 'asc' ? 'up' : 'down'}` : 'mdi mdi-sort'}"></span>
        </div>
        <div class="header-cell" data-sort="post_date">
            Discovery Date
            <span class="sort-icon ${currentSort.column === 'post_date' ? `mdi mdi-arrow-${currentSort.direction === 'asc' ? 'up' : 'down'}` : 'mdi mdi-sort'}"></span>
        </div>
    `;
    container.appendChild(headerRow);

    // 添加排序事件监听
    headerRow.querySelectorAll('.header-cell').forEach(cell => {
        cell.addEventListener('click', () => {
            const column = cell.dataset.sort;
            if (currentSort.column === column) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.column = column;
                currentSort.direction = 'desc';
            }
            sortAndRenderData();
        });
    });

    // 获取当前页数据并显示
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageData = filteredData.slice(startIndex, endIndex);
    
    pageData.forEach(item => {
        const card = document.createElement('div');
        card.className = 'package-card';
        card.onclick = () => showPackageDetail(item['Package Name']);
        
        const version = item['Package Version'] || '*';
        const source = Array.isArray(item['Source']) ? item['Source'].join(', ') : (item['Source'] || 'Unknown');
        const postDate = item['post_date'] || 'N/A';
        
        card.innerHTML = `
            <div class="package-summary">
                <div class="package-name">${item['Package Name']}</div>
                <div>${item['Package Manager']}</div>
                <div class="package-version">${version}</div>
                <div>${source}</div>
                <div>${postDate}</div>
            </div>
        `;
        
        container.appendChild(card);
    });
    
    updatePaginationControls();
}

// 修改数据过滤和排序逻辑
function sortAndRenderData() {
    // 将数据分为两组：完整数据和不完整数据
    const completeData = [];
    const incompleteData = [];

    filteredData.forEach(item => {
        if (isCompleteData(item)) {
            completeData.push(item);
        } else {
            incompleteData.push(item);
        }
    });

    // 分别对两组数据进行排序
    const sortFunction = (a, b) => {
        let valueA = a[currentSort.column];
        let valueB = b[currentSort.column];

        // 特殊处理数组类型的 Source
        if (currentSort.column === 'Source') {
            valueA = Array.isArray(valueA) ? valueA.join(', ') : (valueA || 'Unknown');
            valueB = Array.isArray(valueB) ? valueB.join(', ') : (valueB || 'Unknown');
        }

        // 特殊处理版本号
        if (currentSort.column === 'Package Version') {
            valueA = valueA || '*';
            valueB = valueB || '*';
        }

        // 日期比较
        if (currentSort.column === 'post_date') {
            valueA = new Date(valueA || 0);
            valueB = new Date(valueB || 0);
        }

        if (valueA === valueB) return 0;
        
        const compareResult = valueA > valueB ? 1 : -1;
        return currentSort.direction === 'asc' ? compareResult : -compareResult;
    };

    completeData.sort(sortFunction);
    incompleteData.sort(sortFunction);

    // 合并排序后的数据
    filteredData = [...completeData, ...incompleteData];

    renderResults();
}

// 添加判断数据完整性的函数
function isCompleteData(item) {
    // 基础检查：包名不能是 Unknown 或 CVE 格式
    if (!item['Package Name'] || 
        item['Package Name'].toLowerCase() === 'unknown' ||
        /^cve-\d{4}-\d+$/i.test(item['Package Name'])) {
        return false;
    }

    // 检查必需字段是否存在且有效
    const requiredFields = [
        'Package Manager',
        'Attack Vector',
        'Method of Attack',
        'post_date',
        'Source',
        'Discoverer',
        'Repository URL',
        'Indicators of Compromise'
    ];

    for (const field of requiredFields) {
        if (!item[field] || 
            item[field] === 'Unknown' || 
            item[field] === 'N/A' ||
            (Array.isArray(item[field]) && item[field].length === 0)) {
            return false;
        }
    }

    // 特殊处理数组类型的字段
    if (Array.isArray(item.Source)) {
        if (item.Source.some(source => !source || source === 'Unknown')) {
            return false;
        }
    }

    if (Array.isArray(item['Indicators of Compromise'])) {
        if (item['Indicators of Compromise'].length === 0 || 
            item['Indicators of Compromise'].some(ioc => !ioc || ioc === 'Unknown')) {
            return false;
        }
    }

    // 检查日期格式是否有效
    const date = new Date(item.post_date);
    if (isNaN(date.getTime())) {
        return false;
    }

    // 检查 URL 格式是否有效
    try {
        new URL(item['Repository URL']);
    } catch {
        return false;
    }

    return true;
}

// 更新分页控制
function updatePaginationControls() {
    const totalPages = Math.ceil(filteredData.length / itemsPerPage);
    document.getElementById('currentPage').textContent = `Page ${currentPage} of ${totalPages}`;
    
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage === totalPages;
}

// 事件监听器
document.addEventListener('DOMContentLoaded', () => {
    fetchData();
    
    document.getElementById('searchInput').addEventListener('input', filterAndRenderResults);
    document.getElementById('searchButton').addEventListener('click', filterAndRenderResults);
    
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderResults();
        }
    });
    
    document.getElementById('nextPage').addEventListener('click', () => {
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderResults();
        }
    });
});

// 显示详情弹窗
function showPackageDetail(packageName) {
    const modal = document.getElementById('detailModal');
    const packageData = allData.find(item => item['Package Name'] === packageName);
    renderDetail(packageData);
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// 关闭弹窗
function closeModal() {
    const modal = document.getElementById('detailModal');
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

// 修改渲染详情的函数，优化默认值处理
function renderDetail(packageData) {
    if (!packageData) {
        document.getElementById('detailContent').innerHTML = '<h2>Package not found</h2>';
        return;
    }

    // 统一处理特殊字段
    packageData = { ...packageData };
    packageData['Model'] = 'GPT-4o';
    packageData['Prompt'] = 'CoT-Fewshot';
    packageData['Impacted Systems'] = packageData['Impacted Systems'] || 'Windows, Linux and MacOS';
    packageData['Package Version'] = packageData['Package Version'] || '*';

    // 不再需要为 Method of Attack 设置默认值，因为已经在过滤时确保它存在

    const detailFields = [
        ['Package Name', 'Package Name', 'mdi-package-variant'],
        ['Registry', 'Package Manager', 'mdi-source-repository'],
        ['Version', 'Package Version', 'mdi-numeric'],
        ['Intelligence Source', 'Source', 'mdi-database'],
        ['Discovery Date', 'post_date', 'mdi-calendar'],
        ['Attack Method', 'Method of Attack', 'mdi-shield-alert'],
        ['Attack Vector', 'Attack Vector', 'mdi-target'],
        ['Discoverer', 'Discoverer', 'mdi-account'],
        ['Repository URL', 'Repository URL', 'mdi-link'],
        ['Impacted Systems', 'Impacted Systems', 'mdi-laptop'],
        ['Intelligence Model', 'Model', 'mdi-brain'],
        ['Analysis Method', 'Prompt', 'mdi-text']
    ];

    let detailHTML = '<div class="detail-grid">';
    
    detailFields.forEach(([label, key, icon]) => {
        let content = packageData[key] || '';
        // 如果是Source且是数组，处理换行
        if (key === 'Source' && Array.isArray(content)) {
            content = content.map(s => s.trim()).join(', ');
        }
        detailHTML += `
            <div class="detail-section">
                <div class="detail-section-title">
                    <span class="mdi ${icon}"></span>
                    ${label}
                </div>
                <div class="detail-section-content">${content}</div>
            </div>
        `;
    });

    // 处理 References (source_link)
    let sourceLinks = Array.isArray(packageData['source_link']) ? 
        packageData['source_link'] : 
        [packageData['source_link']].filter(Boolean);
    
    // 移除每个链接中的换行符
    sourceLinks = sourceLinks.map(link => link.trim());
    
    detailHTML += `
        <div class="detail-section">
            <div class="detail-section-title">
                <span class="mdi mdi-link-variant"></span>
                Intelligence Sources
            </div>
            <div class="detail-section-content source-links">
                ${sourceLinks.map(link => `
                    <a href="${link}" target="_blank" class="source-link">
                        ${link}
                        <span class="mdi mdi-open-in-new"></span>
                    </a>
                `).join('')}
            </div>
        </div>
    `;

    // IoC 单独处理
    if (packageData['Indicators of Compromise']) {
        detailHTML += `
            <div class="detail-section full-width">
                <div class="detail-section-title">
                    <span class="mdi mdi-alert"></span>
                    Indicators of Compromise (IoC)
                </div>
                <div class="detail-section-content">
                    ${Array.isArray(packageData['Indicators of Compromise']) ? 
                        packageData['Indicators of Compromise'].join('<br>') : 
                        packageData['Indicators of Compromise']}
                </div>
            </div>
        `;
    }

    detailHTML += '</div>';
    document.getElementById('detailContent').innerHTML = detailHTML;
}

// 点击模态框外部关闭
document.addEventListener('click', (e) => {
    const modal = document.getElementById('detailModal');
    if (e.target === modal) {
        closeModal();
    }
}); 