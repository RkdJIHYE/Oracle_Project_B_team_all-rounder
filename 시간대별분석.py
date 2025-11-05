import pandas as pd
import matplotlib.pyplot as plt
import platform
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch
import numpy as np

# 한글 폰트 설정
if platform.system() == "Windows":
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == "Darwin":
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# 파일 경로 (본인의 파일 경로로 수정하세요)
file_path = "/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/출력/시간대별_월평균_평일휴일_역별_승하차_통합(반올림_행합계포함).csv"

# CSV 파일 읽기 (인코딩 처리)
try:
    df = pd.read_csv(file_path, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="cp949")

print("데이터 정보:")
print(f"총 행 수: {len(df)}")
print(f"컬럼 수: {len(df.columns)}")
print("\n컬럼명:", df.columns.tolist())

if "평일휴일" not in df.columns:
    raise ValueError("데이터에 '평일휴일' 컬럼이 없습니다.")
if "월" not in df.columns:
    raise ValueError("데이터에 '월' 컬럼이 없습니다.")

print("\n평일휴일 구분:", df['평일휴일'].unique())
print("월 구분:", sorted(df['월'].unique()))

# 평일 데이터만 필터링
weekday = df[df["평일휴일"] == "평일"].copy()
print(f"\n평일 데이터 행 수: {len(weekday)}")

# 시간대 컬럼(이 순서로 표시)
time_cols = [
    '06시간대이전', '06-07시간대', '07-08시간대', '08-09시간대', '09-10시간대',
    '10-11시간대', '11-12시간대', '12-13시간대', '13-14시간대', '14-15시간대',
    '15-16시간대', '16-17시간대', '17-18시간대', '18-19시간대', '19-20시간대',
    '20-21시간대', '21-22시간대', '22-23시간대', '23-24시간대', '24시간대이후'
]
existing_time_cols = [c for c in time_cols if c in weekday.columns]
if not existing_time_cols:
    raise ValueError("시간대 컬럼이 존재하지 않습니다. 입력 데이터를 확인하세요.")

print(f"\n사용할 시간대 컬럼 수: {len(existing_time_cols)}")
print("시간대 컬럼들:", existing_time_cols)

# 1) 월별로 역/승하차를 모두 합쳐 '그 달의 하루' 만들기
monthly_city_day = weekday.groupby("월")[existing_time_cols].sum()
print(f"\n월별 집계 완료. 월 수: {len(monthly_city_day)}")

# 2) 여러 달을 평균해 '대표 하루' 만들기
city_daily_avg = monthly_city_day.mean()

print(f"\n일평균 계산 완료. 시간대 수: {len(city_daily_avg)}")

# --- 구간 정의 ---
work_slots = ['10-11시간대','11-12시간대','12-13시간대',
              '13-14시간대','14-15시간대','15-16시간대','16-17시간대']  # 근무시간
commute_slots = ['06-07시간대','07-08시간대','08-09시간대','09-10시간대','17-18시간대','18-19시간대','19-20시간대','20-21시간대']  # 출퇴근
# 나머지는 기타(심야/이른 새벽 등)

# --- 색상 (주석과 실제 색 일치) ---
commute_color = '#BAE1FF'   # 연한 블루: 출퇴근시간
work_color = '#FFBADF'      # 연한 핑크: 근무시간(9-18)
other_color = '#E0E0E0'     # 연한 회색: 기타시간

# 색상 매핑
colors = []
for slot in city_daily_avg.index:
    if slot in work_slots:
        colors.append(work_color)
    elif slot in commute_slots:
        colors.append(commute_color)
    else:
        colors.append(other_color)

print(f"\n색상 할당 완료.")
print(f"근무시간(10-17) 막대 개수: {colors.count(work_color)}")
print(f"출퇴근시간 막대 개수: {colors.count(commute_color)}")
print(f"기타시간 막대 개수: {colors.count(other_color)}")

# 시각화
plt.figure(figsize=(16, 8))
xpos = np.arange(len(city_daily_avg))
bars = plt.bar(xpos, city_daily_avg.values, color=colors, edgecolor="white", linewidth=1.5, alpha=0.9)

plt.title("평일 시간대별 서울시 노인 지하철 이용 수 (월평균)", fontsize=18, fontweight='bold', pad=25)
plt.xlabel("시간대", fontsize=14)
plt.ylabel("이용 인원(명)", fontsize=14)
plt.xticks(xpos, city_daily_avg.index, rotation=45, ha='right', fontsize=11)

ax = plt.gca()
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: format(int(x), ',')))
plt.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
ax.set_axisbelow(True)
ax.set_facecolor('#FAFAFA')

# 최댓값 주석
max_label = city_daily_avg.idxmax()
max_pos = list(city_daily_avg.index).index(max_label)
max_val = city_daily_avg.loc[max_label]
plt.annotate(f'최고: {int(max_val):,}명',
             xy=(max_pos, max_val),
             xytext=(max_pos, max_val * 1.05),
             ha='center', fontsize=10, fontweight='bold',
             arrowprops=dict(arrowstyle='->', color='red', alpha=0.7))

# 범례
legend_elements = [
    Patch(facecolor=commute_color, edgecolor='white', alpha=0.9, label='출퇴근시간(06–10, 17–21)'),
    Patch(facecolor=work_color, edgecolor='white', alpha=0.9, label='근무시간(10–17)'),
    Patch(facecolor=other_color, edgecolor='white', alpha=0.9, label='기타시간(심야/이른 새벽 등)')
]
plt.legend(handles=legend_elements, loc='upper right', fontsize=12)

plt.tight_layout()
plt.show()

# --- 기본 통계 ---
print(f"\n=== 기본 통계 ===")
print(f"총 이용자 수 (일평균): {city_daily_avg.sum():,.0f}명")
print(f"최고 이용 시간대: {city_daily_avg.idxmax()} ({city_daily_avg.max():,.0f}명)")
print(f"최저 이용 시간대: {city_daily_avg.idxmin()} ({city_daily_avg.min():,.0f}명)")

# --- 구간별 합계/비율 ---
def safe_sum(slots):
    return float(sum(city_daily_avg[s] for s in slots if s in city_daily_avg.index))

work_total = safe_sum(work_slots)
commute_total = safe_sum(commute_slots)
total = float(city_daily_avg.sum())
other_total = total - work_total - commute_total

print(f"\n=== 시간대별 비교 ===")
print(f"출퇴근시간(06–10, 17–21): {commute_total:,.0f}명 ({commute_total/total*100:.1f}%)")
print(f"근무시간(10–17): {work_total:,.0f}명 ({work_total/total*100:.1f}%)")
print(f"기타시간: {other_total:,.0f}명 ({other_total/total*100:.1f}%)")
