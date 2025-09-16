// 原来的仪表盘相关 JavaScript 代码 

document.addEventListener('DOMContentLoaded', function() {
    loadData();
});

async function loadData() {
    try {
        const response = await fetch('../aggregated_packages.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const rawData = await response.json();
        
        if (!Array.isArray(rawData)) {
            throw new Error('Data is not an array');
        }

        // 过滤数据
        const data = filterValidData(rawData);
        
        // 使用过滤后的数据进行统计和图表初始化
        updateStatistics(data);
        initializeCharts(data);
    } catch (error) {
        console.error('Error loading data:', error);
        
        const errorMessage = `数据加载失败: ${error.message}`;
        
        document.querySelectorAll('.chart').forEach(chart => {
            chart.innerHTML = `<div class="error-message">${errorMessage}</div>`;
        });

        // 更新错误元素列表，移除已删除的元素
        const errorElements = [
            'totalCount',
            'monthlyCount',
            'sourceCount',
            'mostActiveManager',
            'avgMonthlyGrowth',
            'latestUpdate',
            'monthlyTrend',
            'managerCount',
            'updateTime',
            'mostDangerousManager',
            'dangerCount',
            'topDiscoverer',
            'discovererCount'
            // 移除 'mainAttackType' 和 'attackTypeCount'
        ];

        errorElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = 'Error';
            }
        });
    }
}

// 添加数据过滤函数
function filterValidData(data) {
    return data.filter(item => {
        // 过滤掉包名为 Unknown 的
        if (!item['Package Name'] || item['Package Name'].toLowerCase() === 'unknown') {
            return false;
        }
        // 过滤掉 CVE 格式的包名
        if (/^cve-\d{4}-\d+$/i.test(item['Package Name'])) {
            return false;
        }
        return true;
    });
}

function updateStatistics(data) {
    try {
        // 总数据量
        document.getElementById('totalCount').textContent = data.length.toLocaleString();

        // 本月新增统计（带同比增长）
        const currentDate = new Date();
        const currentMonth = currentDate.getMonth();
        const currentYear = currentDate.getFullYear();
        
        const thisMonthCount = data.filter(item => {
            try {
                const itemDate = new Date(item.post_date);
                return !isNaN(itemDate) && 
                       itemDate.getMonth() === currentMonth && 
                       itemDate.getFullYear() === currentYear;
            } catch {
                return false;
            }
        }).length;

        const lastMonthCount = data.filter(item => {
            try {
                const itemDate = new Date(item.post_date);
                const lastMonth = currentMonth === 0 ? 11 : currentMonth - 1;
                const lastMonthYear = currentMonth === 0 ? currentYear - 1 : currentYear;
                return !isNaN(itemDate) && 
                       itemDate.getMonth() === lastMonth && 
                       itemDate.getFullYear() === lastMonthYear;
            } catch {
                return false;
            }
        }).length;

        document.getElementById('monthlyCount').textContent = thisMonthCount.toLocaleString();
        
        // 计算环比增长
        const growth = lastMonthCount === 0 ? 100 : ((thisMonthCount - lastMonthCount) / lastMonthCount * 100).toFixed(1);
        const trendElement = document.getElementById('monthlyTrend');
        trendElement.innerHTML = `
            <span class="mdi ${growth >= 0 ? 'mdi-arrow-up-bold' : 'mdi-arrow-down-bold'}"></span>
            <span>${Math.abs(growth)}%</span>
        `;
        trendElement.className = `trend-indicator ${growth >= 0 ? 'up' : 'down'}`;

        // 数据源数量 - 修改为显示数据源名称和各自的数据量
        const sourceStats = {};
        data.forEach(item => {
            if (Array.isArray(item.Source)) {
                item.Source.forEach(source => {
                    if (source) {
                        sourceStats[source] = (sourceStats[source] || 0) + 1;
                    }
                });
            } else if (item.Source) {
                sourceStats[item.Source] = (sourceStats[item.Source] || 0) + 1;
            }
        });

        // 找出数据量最大的数据源
        const topSource = Object.entries(sourceStats)
            .sort((a, b) => b[1] - a[1])[0];

        if (topSource) {
            document.getElementById('sourceCount').textContent = topSource[0];
            // 添加子信息显示数据量
            document.getElementById('sourceInfo').textContent = 
                `贡献 ${topSource[1].toLocaleString()} 个数据`;
        }

        // 最活跃包管理器统计
        const managerStats = {};
        data.forEach(item => {
            const manager = item['Package Manager'];
            if (manager) {
                managerStats[manager] = (managerStats[manager] || 0) + 1;
            }
        });

        const managers = Object.entries(managerStats);
        const mostActive = managers.length > 0 ? 
            managers.sort((a, b) => b[1] - a[1])[0] : 
            ['Unknown', 0];

        document.getElementById('mostActiveManager').textContent = mostActive[0];
        document.getElementById('managerCount').textContent = 
            `${mostActive[1].toLocaleString()} 个恶意包`;

        // 计算月均增长
        const sixMonthsAgo = new Date();
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
        const recentData = data.filter(item => {
            try {
                const itemDate = new Date(item.post_date);
                return !isNaN(itemDate) && itemDate >= sixMonthsAgo;
            } catch {
                return false;
            }
        });
        const avgGrowth = Math.round(recentData.length / 6);
        document.getElementById('avgMonthlyGrowth').textContent = 
            `${avgGrowth.toLocaleString()}`;

        // 最近更新时间
        const validDates = data
            .map(item => {
                try {
                    const date = new Date(item.post_date);
                    return isNaN(date) ? null : date;
                } catch {
                    return null;
                }
            })
            .filter(date => date !== null);

        if (validDates.length > 0) {
            const latestDate = new Date(Math.max(...validDates));
            const latestPackage = data.find(item => {
                try {
                    return new Date(item.post_date).getTime() === latestDate.getTime();
                } catch {
                    return false;
                }
            });

            document.getElementById('latestUpdate').textContent = 
                (latestPackage && latestPackage['Package Name']) || 'Unknown';
            document.getElementById('updateTime').textContent = 
                `${latestDate.toLocaleDateString()} ${latestDate.toLocaleTimeString()}`;
        } else {
            document.getElementById('latestUpdate').textContent = 'Unknown';
            document.getElementById('updateTime').textContent = 'No valid date';
        }

        // 最危险包管理器（根据攻击类型数量）
        const managerDangerStats = {};
        data.forEach(item => {
            const manager = item['Package Manager'];
            if (manager) {
                if (!managerDangerStats[manager]) {
                    managerDangerStats[manager] = new Set();
                }
                if (item['Attack Vector']) {
                    managerDangerStats[manager].add(item['Attack Vector']);
                }
            }
        });

        const mostDangerous = Object.entries(managerDangerStats)
            .map(([name, attacks]) => ({
                name,
                count: attacks.size
            }))
            .sort((a, b) => b.count - a.count)[0];

        if (mostDangerous) {
            document.getElementById('mostDangerousManager').textContent = mostDangerous.name;
            document.getElementById('dangerCount').textContent = 
                `${mostDangerous.count} 种攻击类型`;
        }

        // 最活跃发现者
        const discoverers = {};
        data.forEach(item => {
            if (item['Discoverer']) {
                discoverers[item['Discoverer']] = 
                    (discoverers[item['Discoverer']] || 0) + 1;
            }
        });

        const topDiscoverer = Object.entries(discoverers)
            .sort((a, b) => b[1] - a[1])[0];

        if (topDiscoverer) {
            document.getElementById('topDiscoverer').textContent = topDiscoverer[0];
            document.getElementById('discovererCount').textContent = 
                `发现 ${topDiscoverer[1]} 个包`;
        }

        // 更新 Top 10 表格
        updateTopPackagesTable(data);
    } catch (error) {
        console.error('Error in updateStatistics:', error);
        throw error;
    }
}

function updateTopPackagesTable(data) {
    const tbody = document.querySelector('#topPackagesTable tbody');
    const sortedData = [...data]
        // 过滤掉不符合条件的数据
        .filter(pkg => {
            // 过滤掉 CVE 格式的包名
            if (/^CVE-\d{4}-\d+$/i.test(pkg['Package Name'])) {
                return false;
            }
            // 过滤掉攻击类型为 Unknown 的
            if (!pkg['Attack Vector'] || pkg['Attack Vector'] === 'Unknown') {
                return false;
            }
            // 过滤掉发现者为 Unknown 的
            if (!pkg['Discoverer'] || pkg['Discoverer'] === 'Unknown') {
                return false;
            }
            return true;
        })
        // 按日期排序并取前10
        .sort((a, b) => new Date(b.post_date) - new Date(a.post_date))
        .slice(0, 10);

    tbody.innerHTML = sortedData.map(pkg => `
        <tr>
            <td>${pkg['Package Name']}</td>
            <td>${pkg['Package Manager'] || 'Unknown'}</td>
            <td>${pkg['Attack Vector']}</td>
            <td>${new Date(pkg.post_date).toLocaleDateString()}</td>
            <td>${pkg['Discoverer']}</td>
        </tr>
    `).join('');
}

function initializeCharts(data) {
    initMonthlyTrendChart(data);
    initSourceDistributionChart(data);
    initPackageManagerChart(data);
    initAttackTrendChart(data);
}

function initMonthlyTrendChart(data) {
    const monthlyData = {};
    data.forEach(item => {
        const date = new Date(item.post_date);
        const monthYear = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
        monthlyData[monthYear] = (monthlyData[monthYear] || 0) + 1;
    });

    const sortedMonths = Object.keys(monthlyData).sort();
    const monthlyTrendChart = echarts.init(document.getElementById('monthlyTrendChart'));
    
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: sortedMonths,
            axisLabel: {
                rotate: 45
            }
        },
        yAxis: {
            type: 'value'
        },
        series: [{
            data: sortedMonths.map(month => monthlyData[month]),
            type: 'line',
            smooth: true,
            areaStyle: {
                opacity: 0.3
            },
            lineStyle: {
                width: 3
            }
        }]
    };
    
    monthlyTrendChart.setOption(option);
}

function initSourceDistributionChart(data) {
    // 处理数组格式的 Source
    const sourceStats = {};
    data.forEach(item => {
        if (Array.isArray(item.Source)) {
            item.Source.forEach(source => {
                sourceStats[source] = (sourceStats[source] || 0) + 1;
            });
        } else if (item.Source) {
            sourceStats[item.Source] = (sourceStats[item.Source] || 0) + 1;
        }
    });

    const sourceDistributionChart = echarts.init(document.getElementById('sourceDistributionChart'));
    
    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            type: 'scroll'
        },
        series: [{
            name: '数据源分布',
            type: 'pie',
            radius: '70%',
            data: Object.entries(sourceStats)
                .map(([name, value]) => ({
                    name,
                    value
                }))
                .sort((a, b) => b.value - a.value),
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };
    
    sourceDistributionChart.setOption(option);
}

function initPackageManagerChart(data) {
    const managerStats = {};
    data.forEach(item => {
        managerStats[item['Package Manager']] = (managerStats[item['Package Manager']] || 0) + 1;
    });

    const packageManagerChart = echarts.init(document.getElementById('packageManagerChart'));
    
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: [{
            type: 'category',
            data: Object.keys(managerStats),
            axisTick: {
                alignWithLabel: true
            },
            axisLabel: {
                rotate: 45
            }
        }],
        yAxis: [{
            type: 'value'
        }],
        series: [{
            name: '包数量',
            type: 'bar',
            barWidth: '60%',
            data: Object.values(managerStats),
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    {offset: 0, color: '#83bff6'},
                    {offset: 0.5, color: '#188df0'},
                    {offset: 1, color: '#188df0'}
                ])
            }
        }]
    };
    
    packageManagerChart.setOption(option);
}

function initAttackTrendChart(data) {
    // 按月份统计不同攻击类型的数量
    const attackTrends = {};
    data.forEach(item => {
        const date = new Date(item.post_date);
        const monthYear = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
        const attackType = item['Attack Vector'];
        
        // 跳过 Unknown 和空的攻击类型
        if (!attackType || attackType === 'Unknown') {
            return;
        }
        
        if (!attackTrends[monthYear]) {
            attackTrends[monthYear] = {};
        }
        attackTrends[monthYear][attackType] = (attackTrends[monthYear][attackType] || 0) + 1;
    });

    const months = Object.keys(attackTrends).sort();
    // 过滤掉 Unknown 和空的攻击类型
    const attackTypes = [...new Set(data
        .map(item => item['Attack Vector'])
        .filter(type => type && type !== 'Unknown')
    )];
    
    const series = attackTypes.map(type => ({
        name: type,
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
            focus: 'series'
        },
        data: months.map(month => attackTrends[month][type] || 0)
    }));

    const attackTrendChart = echarts.init(document.getElementById('attackTrendChart'));
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                label: {
                    backgroundColor: '#6a7985'
                }
            }
        },
        legend: {
            data: attackTypes,
            type: 'scroll'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: months,
            axisLabel: {
                rotate: 45
            }
        },
        yAxis: {
            type: 'value'
        },
        series: series
    };

    attackTrendChart.setOption(option);
}

// 响应式处理
window.addEventListener('resize', function() {
    const charts = document.querySelectorAll('.chart');
    charts.forEach(chart => {
        echarts.getInstanceByDom(chart)?.resize();
    });
}); 