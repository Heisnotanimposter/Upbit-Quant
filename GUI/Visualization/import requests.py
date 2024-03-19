import requests

# ITU의 API 엔드포인트 설정
ITU_API_ENDPOINT = "https://api.itu.int/public/2.0/network/ITU-R-ICT-ADM"

# ITU API를 통해 데이터 가져오기 (예: 전체 세계 인터넷 이용률 데이터)
response = requests.get(ITU_API_ENDPOINT)
data = response.json()


import pandas as pd

# JSON 데이터를 Pandas 데이터프레임으로 변환
df = pd.DataFrame(data['results'])

# 데이터프레임에서 필요한 열만 선택
df = df[['country_name', 'internet_users']]

# 데이터프레임 정렬 (예: 인터넷 사용자 수 기준으로 내림차순)
df = df.sort_values(by='internet_users', ascending=False)

import matplotlib.pyplot as plt

# 시각화 설정
plt.figure(figsize=(12, 6))
plt.bar(df['country_name'][:10], df['internet_users'][:10])
plt.xlabel('국가')
plt.ylabel('인터넷 사용자 수')
plt.title('세계 상위 10개 국가의 인터넷 사용자 수')

# x축 라벨 회전
plt.xticks(rotation=45)

# 그래프 표시
plt.tight_layout()
plt.show()

