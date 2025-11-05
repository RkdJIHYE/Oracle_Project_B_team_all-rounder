import pandas as pd
import matplotlib.pyplot as plt
import platform

# 한글 폰트
if platform.system() == "Windows":
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == "Darwin":
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

file_path = "/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/출력/시간대별_월평균_평일휴일_역별_승하차_통합(반올림_행합계포함).csv"
try:
    df = pd.read_csv(file_path, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="cp949")

weekday = df[df["평일휴일"] == "평일"]
time_cols = [c for c in weekday.columns if "시간대" in c]

# ✅ 컬럼 순서 조정: "06-07시간대"를 두 번째로 옮김
if "06-07시간대" in time_cols:
    time_cols.remove("06-07시간대")
    time_cols.insert(1, "06-07시간대")

# 1) 월별로 역/승하차를 모두 합쳐 '그 달의 하루' 만들기
monthly_city_day = weekday.groupby("월")[time_cols].sum()

# 2) 여러 달을 평균해 '대표 하루' 만들기
city_daily_avg = monthly_city_day.mean()

# 시각화
plt.figure(figsize=(12,6))
city_daily_avg.plot(kind="bar", edgecolor="black")
plt.title("평일 시간대별 서울시 노인 지하철 이용 수 (2021.7~2023.12)(월평균)")
plt.xlabel("시간대")
plt.ylabel("이용 인원(명)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
