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
    // 创建一个img元素来显示图片
    const img = document.createElement('img');
    img.src = '../rating_distribution.png'; // 设置图片的源路径
    img.alt = 'Rating Distribution'; // 设置图片的替代文本
    img.style.width = '100%'; // 设置图片的宽度，可以根据需要调整
    ratings.appendChild(img); // 将图片元素添加到ratings容器中

    // 更新购买者类型占比（如果有数据）
    const buyer = document.querySelector('.buyer');
    buyer.innerHTML = ''; // 清空现有内容
    Object.keys(productInfo.count_buyer).forEach(buyerType => {
        const buyerSpan = document.createElement('span');
        buyerSpan.textContent = `${buyerType}: ${(productInfo.count_buyer[buyerType] / productInfo.TotalResults * 100).toFixed(2)}% `;
        buyer.appendChild(buyerSpan);
    });

    // 更新推荐占比
    const recommend = document.querySelector('.recommend');
    recommend.innerHTML = ''; // 清空现有内容
    const recomCount = productInfo.RecommendCount.Recom;
    const notRecomCount = productInfo.RecommendCount.notRecom;
    const totalRecommendations = recomCount + notRecomCount;
    const recomPercentage = (recomCount / totalRecommendations * 100).toFixed(2);
    const notRecomPercentage = (notRecomCount / totalRecommendations * 100).toFixed(2);
    recommend.textContent = `推荐: ${recomPercentage}% 不推荐: ${notRecomPercentage}%`;

    // 更新年龄分布占比（如果有数据）
    const age = document.querySelector('.age');
    age.innerHTML = ''; // 清空现有内容
    Object.keys(productInfo.age_distribution_list).forEach(ageGroup => {
        const ageSpan = document.createElement('span');
        ageSpan.textContent = `${ageGroup}: ${(productInfo.age_distribution_list[ageGroup] / productInfo.TotalResults * 100).toFixed(2)}% `;
        age.appendChild(ageSpan);
    });

    // 更新性别分布占比（如果有数据）
    const gender = document.querySelector('.gender');
    gender.innerHTML = ''; // 清空现有内容
    Object.keys(productInfo.gender_distribution_list).forEach(genderType => {
        const genderSpan = document.createElement('span');
        genderSpan.textContent = `${genderType}: ${(productInfo.gender_distribution_list[genderType] / productInfo.TotalResults * 100).toFixed(2)}% `;
        gender.appendChild(genderSpan);
    });
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
});