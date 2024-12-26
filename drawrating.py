import matplotlib.pyplot as plt
import os

def generate_pie_chart(productinfo):
    # 检查/static目录是否存在，如果不存在则创建
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # 提取评分数据
    ratings = productinfo['count_rating']
    labels = ['Rating 5', 'Rating 4', 'Rating 3', 'Rating 2', 'Rating 1']
    sizes = [ratings['rating5'], ratings['rating4'], ratings['rating3'], ratings['rating2'], ratings['rating1']]
    total_ratings = sum(sizes)  # 计算总评论数
    
    # 生成饼图
    fig1, ax1 = plt.subplots()
    autopct_func = lambda p: '{:.1f}% ({:d})'.format(p,int(p*total_ratings/100) )
    ax1.pie(sizes, labels=labels, autopct=autopct_func, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    # 保存饼图到/static目录
    plt.savefig('static/rating_distribution.png')
    plt.close()

# 假设这是你的productinfo数据
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

# 调用函数生成饼图
generate_pie_chart(productinfo)