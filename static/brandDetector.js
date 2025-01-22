function parseJSON(data) {
    return data; // JSON数据已经是对象数组，不需要解析
}

function renderJSON(data) {
    const tableBody = document.getElementById('csvTable').getElementsByTagName('tbody')[0];
    tableBody.innerHTML = ''; // 清空表格内容
    data.forEach(row => {
        const tr = document.createElement('tr');
        Object.values(row).forEach(value => {
            const td = document.createElement('td');
            td.textContent = value;
            tr.appendChild(td);
        });
        tr.setAttribute('data-rating', row.Rating); // 设置数据属性以便筛选
        tableBody.appendChild(tr);
    });
}

function updateProductInfo(data) {
    const productInfo = data.productinfo;
    const productInfoContainer = document.querySelector('.product-info');

    // 更新产品名称
    document.querySelector('.product-name').textContent = data.productname;

    // 更新评分总分
    const scoreTotal = document.querySelector('.score_total');
    scoreTotal.querySelector('.score').textContent = productInfo.averageOverallRating;

    // 更新总评价数
    scoreTotal.querySelector('.total').textContent = productInfo.TotalResults;

    // 更新各星级评价
    const ratings = document.querySelector('.ratings');
    ratings.innerHTML = ''; // 清空现有内容
    const ratingsImg = document.createElement('img');
    ratingsImg.src = 'static/rating_distribution.png'; // 设置图片的源路径
    ratingsImg.alt = 'Rating Distribution'; // 设置图片的替代文本
    ratingsImg.style.height = '100%'; // 设置图片的高度，可以根据需要调整
    ratings.appendChild(ratingsImg); // 将图片元素添加到ratings容器中

    // 更新购买者类型占比
    const buyer = document.querySelector('.buyer');
    buyer.innerHTML = ''; // 清空现有内容
    const buyerImg = document.createElement('img');
    buyerImg.src = 'static/buyer_distribution.png'; // 设置图片的源路径
    buyerImg.alt = 'Buyer Type Distribution'; // 设置图片的替代文本
    buyerImg.style.height = '100%'; // 设置图片的高度，可以根据需要调整
    buyer.appendChild(buyerImg); // 将图片元素添加到buyer容器中

    // 更新推荐占比
    const recommend = document.querySelector('.recommend');
    recommend.innerHTML = ''; // 清空现有内容
    const recommendImg = document.createElement('img');
    recommendImg.src = 'static/recommend_distribution.png'; // 设置图片的源路径
    recommendImg.alt = 'Recommendation Distribution'; // 设置图片的替代文本
    recommendImg.style.height = '100%'; // 设置图片的高度，可以根据需要调整
    recommend.appendChild(recommendImg); // 将图片元素添加到recommend容器中

    // 更新年龄分布占比
    const age = document.querySelector('.age');
    age.innerHTML = ''; // 清空现有内容
    const ageImg = document.createElement('img');
    ageImg.src = 'static/age_distribution.png'; // 设置图片的源路径
    ageImg.alt = 'Age Distribution'; // 设置图片的替代文本
    ageImg.style.height = '100%'; // 设置图片的高度，可以根据需要调整
    age.appendChild(ageImg); // 将图片元素添加到age容器中

    // 更新性别分布占比（如果有数据）
    const gender = document.querySelector('.gender');
    gender.innerHTML = ''; // 清空现有内容
    // 如果有性别分布数据，可以在此处添加相应的饼图图片
}

function startScraping() {
    const productLink = document.querySelector('.link-input').value;
    const loadingImage = document.getElementById('loadingImage');
    const tableBody = document.getElementById('csvTable').getElementsByTagName('tbody')[0];

    // 显示加载图片
    loadingImage.style.display = 'block';

    fetch('/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `linkInput=${encodeURIComponent(productLink)}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        const brandValue = data.brand;
        document.querySelector('.brand').textContent = brandValue; // 更新 HTML 中的 brand 值

        // 处理 JSON 数据
        if (data.csvData) {
            const parsedData = parseJSON(data.csvData);
            renderJSON(parsedData);
        } else {
            alert("出现错误");
        }

        // 更新产品信息
        updateProductInfo(data);

        // 隐藏加载图片
        loadingImage.style.display = 'none';
    })
    .catch(error => {
        console.error('Error:', error);
        // 隐藏加载图片
        loadingImage.style.display = 'none';
    });
}


document.addEventListener('DOMContentLoaded', function() {
    const startScrapingButton = document.querySelector('.start-scraping');
    startScrapingButton.addEventListener('click', function(event) {
        event.preventDefault(); // 阻止表单的默认提交行为
        startScraping();
    });
    document.querySelector('.download-reviews').addEventListener('click', function() {
        window.location.href = '/download-csv'; // 触发文件下载
    });
    document.querySelectorAll('.rating-filter').forEach(button => {
        button.addEventListener('click', function() {
            const rating = this.getAttribute('data-rating');
            const rows = document.querySelectorAll('#csvTable tbody tr');
            rows.forEach(row => {
                if (rating === 'all') {
                    row.style.display = ''; // 清除筛选效果
                } else {
                    const rowRating = row.getAttribute('data-rating');
                    if (rowRating === rating) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
        });
    });
    document.getElementById('aiAnalyzeButton').addEventListener('click', function() {
        const aiAnalyzeButton = document.getElementById('aiAnalyzeButton');
        const reviewsButton = document.querySelector('.tab-button.active');
        const reviewsDiv = document.querySelector('.reviews');
        const aiAnalyzeDiv = document.querySelector('.AIanalyze');
    
        // 交换按钮颜色
        aiAnalyzeButton.classList.add('active');
        reviewsButton.classList.remove('active');
    
        // 切换显示和隐藏的元素
        reviewsDiv.classList.add('hidden');
        aiAnalyzeDiv.classList.remove('hidden');
    });
    document.getElementById('reviewsButton').addEventListener('click', function() {
        const aiAnalyzeButton = document.getElementById('aiAnalyzeButton');
        const reviewsButton = document.getElementById('reviewsButton');
        const reviewsDiv = document.querySelector('.reviews');
        const aiAnalyzeDiv = document.querySelector('.AIanalyze');
    
        // 交换按钮颜色
        aiAnalyzeButton.classList.remove('active');
        reviewsButton.classList.add('active');
    
        // 切换显示和隐藏的元素
        reviewsDiv.classList.remove('hidden');
        aiAnalyzeDiv.classList.add('hidden');
    });
});

async function startAnalyze() {
    const keyInput = document.querySelector('.key_input').value; // 获取用户输入的key
    const loadingImage = document.getElementById('loadingImage');

    // 显示加载图片
    loadingImage.style.display = 'block';

    // 发送请求到 /ai 路由
    const response = await fetch('/ai', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `key=${encodeURIComponent(keyInput)}`
    });

    if (!response.ok) {
        throw new Error('Network response was not ok');
    }

    const data = await response.json();

    // 隐藏加载图片
    loadingImage.style.display = 'none';

    if (data.analysis_success) {
        updateAIAnalysisResult(data);
    } else {
        alert("wrong:" + (data.error || "unknown questions"));
    }
}

function updateAIAnalysisResult(data) {
    const customerPersona = document.querySelector('.resultshow:nth-child(1) .resultcontent');
    const suggestionsForImprovement = document.querySelector('.resultshow:nth-child(5) .resultcontent');
    
    customerPersona.textContent = data['Customer Persona'].description;
    suggestionsForImprovement.textContent = data['Suggestions for Improvement'].suggestion;

    // 准备数据
    const scenariosLabels = Object.keys(data['Usage Scenarios']);
    const scenariosData = Object.values(data['Usage Scenarios']);

    const prosLabels = Object.keys(data['Positive Aspects (Pros)']);
    const prosData = Object.values(data['Positive Aspects (Pros)']);

    const consLabels = Object.keys(data['Negative Aspects (Cons)']);
    const consData = Object.values(data['Negative Aspects (Cons)']);

    // 创建图表
    const scenariosCtx = document.getElementById('scenariosChart').getContext('2d');
    const prosCtx = document.getElementById('prosChart').getContext('2d');
    const consCtx = document.getElementById('consChart').getContext('2d');

    new Chart(scenariosCtx, {
        type: 'bar',
        data: {
            labels: scenariosLabels,
            datasets: [{
                label: 'Usage Scenarios',
                data: scenariosData,
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                },
                x: {
                    ticks: {
                        display: false
                    }
                }
            },
            plugins: {
                datalabels: {
                    display: true,
                    color: 'white',
                    font: {
                        weight: 'bold'
                    },
                    formatter: function(value) {
                        return value;
                    }
                }
            }
        }
    });

    new Chart(prosCtx, {
        type: 'bar',
        data: {
            labels: prosLabels,
            datasets: [{
                label: 'Positive Aspects (Pros)',
                data: prosData,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                },
                x: {
                    ticks: {
                        display: false
                    }
                }
            },
            plugins: {
                datalabels: {
                    display: true,
                    color: 'white',
                    font: {
                        weight: 'bold'
                    },
                    formatter: function(value) {
                        return value;
                    }
                }
            }
        }
    });

    new Chart(consCtx, {
        type: 'bar',
        data: {
            labels: consLabels,
            datasets: [{
                label: 'Negative Aspects (Cons)',
                data: consData,
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
                borderColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                },
                x: {
                    ticks: {
                        display: false
                    }
                }
            },
            plugins: {
                datalabels: {
                    display: true,
                    color: 'white',
                    font: {
                        weight: 'bold'
                    },
                    formatter: function(value) {
                        return value;
                    }
                }
            }
        }
    });
    const scenariosDetail = document.getElementById('scenariosDetail');
    let scenariosDetailHtml = '<table><tr><th>Scenario</th><th>Value</th></tr>';
    scenariosLabels.forEach((label, index) => {
        scenariosDetailHtml += `<tr><td>${label}</td><td>${scenariosData[index]}</td></tr>`;
    });
    scenariosDetailHtml += '</table>';
    scenariosDetail.innerHTML = scenariosDetailHtml;

    // 填充Positive Aspects (Pros)的详细信息
    const prosDetail = document.getElementById('prosDetail');
    let prosDetailHtml = '<table><tr><th>Pro</th><th>Value</th></tr>';
    prosLabels.forEach((label, index) => {
        prosDetailHtml += `<tr><td>${label}</td><td>${prosData[index]}</td></tr>`;
    });
    prosDetailHtml += '</table>';
    prosDetail.innerHTML = prosDetailHtml;

    // 填充Negative Aspects (Cons)的详细信息
    const consDetail = document.getElementById('consDetail');
    let consDetailHtml = '<table><tr><th>Con</th><th>Value</th></tr>';
    consLabels.forEach((label, index) => {
        consDetailHtml += `<tr><td>${label}</td><td>${consData[index]}</td></tr>`;
    });
    consDetailHtml += '</table>';
    consDetail.innerHTML = consDetailHtml;
}


document.addEventListener('DOMContentLoaded', function() {
    const startAnalyzeButton = document.querySelector('#submitButton');
    startAnalyzeButton.addEventListener('click', function(event) {
        event.preventDefault(); // 阻止表单的默认提交行为
        startAnalyze();
    });
});