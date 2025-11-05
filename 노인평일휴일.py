import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import platform
import re





# ==============================
# 0) 한글 폰트 설정
# ==============================
if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

# ==============================
# 1) 데이터 로드
# ==============================
file_path = "/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/출력/시간대별_월평균_평일휴일_역별_승하차_통합(반올림_행합계포함).csv"
try:
    df = pd.read_csv(file_path, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="cp949")

# (선택) 분석 기간 제한
# df = df[(df["월"] >= "2021-07") & (df["월"] <= "2023-12")].copy()

# ==============================
# 2) 시간대 컬럼 자동 인식
# ==============================
time_cols = [c for c in df.columns if "시간대" in c]

# "HH-HH시간대"만 인정 (예: "10-11시간대")
rgx = re.compile(r"^(\d{2})-(\d{2})시간대$")

def parse_bin(col: str):
    m = rgx.match(col)
    if not m:
        return None
    s, e = int(m.group(1)), int(m.group(2))
    return s, e

# ==============================
# 3) 원하는 시간창(10:00~17:00)만 포함
#    포함 규칙: 시작시각 >= 10, 종료시각 <= 17  -> 10-11, 11-12, ..., 16-17
# ==============================
WIN_START = 10
WIN_END   = 17

time_cols_10_17 = []
for c in time_cols:
    pr = parse_bin(c)
    if pr is None:
        continue
    s, e = pr
    if s >= WIN_START and e <= WIN_END:
        time_cols_10_17.append(c)

# 폴백: 표준 이름 세트
fallback_10_17 = [f"{h:02d}-{h+1:02d}시간대" for h in range(10, 17)]
if not time_cols_10_17:
    time_cols_10_17 = [c for c in fallback_10_17 if c in df.columns]

if not time_cols_10_17:
    raise ValueError("10~17시 구간에 해당하는 시간대 컬럼을 찾지 못했습니다. 컬럼명을 확인해 주세요.")

# ==============================
# 4) 10~17시 합계 계산 (월평균 하루치 기준)
# ==============================
df["합계_10to17"] = df[time_cols_10_17].sum(axis=1)

# ==============================
# 5) 연도 컬럼 생성 후, 연도별 평일/휴일 합계 및 100% 정규화
# ==============================
df["연도"] = pd.to_datetime(df["월"], errors="coerce").dt.year
if df["연도"].isna().any():
    # 파싱 실패분은 문자열 앞 4자리로 보정(가능한 경우)
    y4 = df.loc[df["연도"].isna(), "월"].astype(str).str.extract(r"^(\d{4})")[0]
    df.loc[df["연도"].isna(), "연도"] = pd.to_numeric(y4, errors="coerce")

df = df.dropna(subset=["연도"]).copy()
df["연도"] = df["연도"].astype(int)

yearly_sum_10_17 = df.groupby(["연도", "평일휴일"])["합계_10to17"].sum().unstack(fill_value=0)
yearly_ratio_10_17 = yearly_sum_10_17.div(yearly_sum_10_17.sum(axis=1), axis=0) * 100

# 정렬된 연도 인덱스 확보
years = sorted(yearly_ratio_10_17.index.tolist())
years_str = [str(y) for y in years]

# 값 안전 추출 (일부 연도에 '평일' 또는 '휴일'이 없을 수 있음)
weekday_vals = yearly_ratio_10_17["평일"].reindex(years, fill_value=0) if "평일" in yearly_ratio_10_17.columns else pd.Series(0, index=years)
holiday_vals = yearly_ratio_10_17["휴일"].reindex(years, fill_value=0) if "휴일" in yearly_ratio_10_17.columns else pd.Series(0, index=years)

# ==============================
# 6) 시각화: 연도별 '좌우 나란히' 막대(그룹드 바)
# ==============================
x = np.arange(len(years))
width = 0.38


from matplotlib import cm
colors = cm.Pastel1.colors  

plt.figure(figsize=(12, 6))
plt.bar(x - width/2, weekday_vals.values, width, label="평일", color=colors[0] )
plt.bar(x + width/2, holiday_vals.values, width, label="휴일", color=colors[1])

plt.xticks(x, years_str, rotation=0)
plt.ylim(0, 100)
plt.ylabel("비율 (%)")
plt.title("연도별 평일/휴일 무임승차인원 이용 비율 (10~17시, 100% 정규화, 그룹드 바)")
plt.legend()

# 값 라벨(퍼센트) 표기
for xi, v in zip(x - width/2, weekday_vals.values):
    plt.text(xi, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
for xi, v in zip(x + width/2, holiday_vals.values):
    plt.text(xi, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)

plt.tight_layout()
plt.show()

# ==============================
# (선택) 연도별 '전 시간대 전체' 비율도 보고 싶다면
# ==============================
# time_cols_all = [c for c in df.columns if rgx.match(c)]  # 00-01 ~ 23-24 형태만
# df["합계_ALL"] = df[time_cols_all].sum(axis=1)
# yearly_sum_all = df.groupby(["연도","평일휴일"])["합계_ALL"].sum().unstack(fill_value=0)
# yearly_ratio_all = yearly_sum_all.div(yearly_sum_all.sum(axis=1), axis=0) * 100
# yearly_ratio_all.to_csv("연도별_평일휴일_비율_ALL(100퍼센트정규화).csv", encoding="utf-8-sig")
