import matplotlib.pyplot as plt
import os

def generate_chart(productinfo):
    # 检查/static目录是否存在，如果不存在则创建
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # 提取评分数据
    ratings = productinfo['count_rating']
    labels = ['5', '4', '3', '2', '1']
    sizes = [ratings['rating5'], ratings['rating4'], ratings['rating3'], ratings['rating2'], ratings['rating1']]
    
    # 生成条形图
    fig1, ax1 = plt.subplots()
    
    # 设置背景色
    fig1.patch.set_facecolor((30/255, 30/255, 30/255))  # 设置图形背景色为 RGB(30, 30, 30)
    
    # 绘制条形图
    bars = ax1.bar(labels, sizes, color='#ff5722')
    
    # 设置标签和标题
    ax1.set_xlabel('Rating', fontsize=14, fontweight='bold', color='#ff5722')
    
    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, height, str(height),
                 ha='center', va='bottom', fontsize=14, weight='bold', color='black')
    
    # 设置坐标轴刻度字体大小和加粗
    for label in ax1.get_xticklabels() + ax1.get_yticklabels():
        label.set_fontsize(14)
        label.set_weight('bold')
        label.set_color('#ff5722')

    # 保存条形图到/static目录
    plt.savefig('static/rating_distribution.png')
    plt.close()

def generate_charts(productinfo):
    # 检查/static目录是否存在，如果不存在则创建
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # 绘制购买者类型饼图
    fig1, ax1 = plt.subplots()
    fig1.patch.set_facecolor((30/255, 30/255, 30/255))  # 设置图形背景色为 RGB(30, 30, 30)
    buyer_labels = ['DIYer', 'Pro']
    buyer_sizes = [productinfo['count_buyer']['DIYer'], productinfo['count_buyer']['Pro']]
    if sum(buyer_sizes) == 0:
        buyer_sizes = [1, 1]
    wedges, texts, autotexts = ax1.pie(buyer_sizes, labels=buyer_labels, autopct='%1.1f%%', startangle=90, colors=['#ff5722', '#9e9e9e'])
    ax1.axis('equal')  # 等轴比例
    plt.title('Buyer Type Distribution', fontsize=16, fontweight='bold', color='#ff5722')
    for text in texts + autotexts:
        text.set_color('#ffffff')
    plt.savefig('static/buyer_distribution.png')
    plt.close()
    
    # 绘制年龄分布饼图
    fig2, ax2 = plt.subplots()
    fig2.patch.set_facecolor((30/255, 30/255, 30/255))  # 设置图形背景色为 RGB(30, 30, 30)
    age_labels = ['18-34', '35-54', '55+']
    age_sizes = [productinfo['age_distribution_list']['18to34'], productinfo['age_distribution_list']['35to54'], productinfo['age_distribution_list']['55orover']]
    if sum(age_sizes) == 0:
        age_sizes = [1, 1, 1]
    wedges, texts, autotexts = ax2.pie(age_sizes, labels=age_labels, autopct='%1.1f%%', startangle=90, colors=['#ff5722', '#9e9e9e', '#757575'])
    ax2.axis('equal')  # 等轴比例
    plt.title('Age Distribution', fontsize=16, fontweight='bold', color='#ff5722')
    for text in texts + autotexts:
        text.set_color('#ffffff')
    plt.savefig('static/age_distribution.png')
    plt.close()
    
    # 绘制推荐情况饼图
    fig3, ax3 = plt.subplots()
    fig3.patch.set_facecolor((30/255, 30/255, 30/255))  # 设置图形背景色为 RGB(30, 30, 30)
    recommend_labels = ['Recommend', 'Not Recommend']
    recommend_sizes = [productinfo['RecommendCount']['Recom'], productinfo['RecommendCount']['notRecom']]
    if sum(recommend_sizes) == 0:
        recommend_sizes = [1, 1]
    wedges, texts, autotexts = ax3.pie(recommend_sizes, labels=recommend_labels, autopct='%1.1f%%', startangle=90, colors=['#ff5722', '#9e9e9e'])
    ax3.axis('equal')  # 等轴比例
    plt.title('Recommendation Distribution', fontsize=16, fontweight='bold', color='#ff5722')
    for text in texts + autotexts:
        text.set_color('#ffffff')
    plt.savefig('static/recommend_distribution.png')
    plt.close()





productinfo = {
    'TotalResults': 810,
    'averageOverallRating': '4.4',
    'RecommendCount': {'Recom': 50, 'notRecom': 50},
    'count_rating': {'rating5': 68, 'rating4': 16, 'rating3': 5, 'rating2': 3, 'rating1': 7},
    'count_buyer': {'DIYer': 0, 'Pro': 0},
    'count_VerifiedPurchaser': '682',
    'age_distribution_list': {'18to34': 0, '35to54': 0, '55orover': 0},
    'gender_distribution_list': {'Male': 0, 'Female': 0}
}

# 调用函数生成条形图
generate_chart(productinfo)
generate_charts(productinfo)