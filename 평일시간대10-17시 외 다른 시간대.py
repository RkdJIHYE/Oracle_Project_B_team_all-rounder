import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import platform
import re
from matplotlib import cm

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
# 2) 평일만 추출
# ==============================
if "평일휴일" not in df.columns:
    raise ValueError("'평일휴일' 컬럼이 없습니다.")
df = df[df["평일휴일"].astype(str).str.strip() == "평일"].copy()

# ==============================
# 3) 시간대 컬럼 자동 인식
# ==============================
time_cols = [c for c in df.columns if "시간대" in c]

# "HH-HH시간대" 형태만 매칭 (예: "10-11시간대")
rgx = re.compile(r"^(\d{2})-(\d{2})시간대$")

def parse_bin(col: str):
    m = rgx.match(col)
    if not m:
        return None
    s, e = int(m.group(1)), int(m.group(2))
    return s, e

# ==============================
# 4) 10~17시 구간 컬럼 선별 (10-11, ..., 16-17)
# ==============================
WIN_START = 10
WIN_END   = 17  # 마지막 bin은 16-17

time_cols_10_17 = []
for c in time_cols:
    pr = parse_bin(c)
    if pr is None:
        continue
    s, e = pr
    if s >= WIN_START and e <= WIN_END:
        time_cols_10_17.append(c)

# 폴백(표준 이름 세트)
fallback_10_17 = [f"{h:02d}-{h+1:02d}시간대" for h in range(10, 17)]
if not time_cols_10_17:
    time_cols_10_17 = [c for c in fallback_10_17 if c in df.columns]

if not time_cols_10_17:
    raise ValueError("10~17시 구간에 해당하는 시간대 컬럼을 찾지 못했습니다. 컬럼명을 확인해 주세요.")

# "그 외" 시간대 = 전체 시간대 - (10~17시)
other_time_cols = [c for c in time_cols if c not in time_cols_10_17]

# ==============================
# 5) 10~17시 합계 & 그 외 합계 (월평균 하루치 기준)
# ==============================
df["합계_10to17"] = df[time_cols_10_17].sum(axis=1)
df["합계_OTHER"]  = df[other_time_cols].sum(axis=1)

# ==============================
# 6) 연도 생성 및 연도별 비율(100% 정규화)
# ==============================
if "월" not in df.columns:
    raise ValueError("'월' 컬럼이 없습니다. 예: 2022-03 형식")

df["연도"] = pd.to_datetime(df["월"], errors="coerce").dt.year
if df["연도"].isna().any():
    y4 = df.loc[df["연도"].isna(), "월"].astype(str).str.extract(r"^(\d{4})")[0]
    df.loc[df["연도"].isna(), "연도"] = pd.to_numeric(y4, errors="coerce")

df = df.dropna(subset=["연도"]).copy()
df["연도"] = df["연도"].astype(int)

yearly_sum = df.groupby("연도")[["합계_10to17", "합계_OTHER"]].sum()
yearly_ratio = yearly_sum.div(yearly_sum.sum(axis=1), axis=0) * 100

years = sorted(yearly_ratio.index.tolist())
years_str = [str(y) for y in years]
vals_10_17 = yearly_ratio["합계_10to17"].reindex(years, fill_value=0.0)
vals_other = yearly_ratio["합계_OTHER"].reindex(years, fill_value=0.0)

# ==============================
# 7) 시각화: 연도별 '좌우 나란히' 막대(그룹드 바)
# ==============================
x = np.arange(len(years))
width = 0.38
palette = cm.Pastel1.colors

plt.figure(figsize=(12, 6))
plt.bar(x - width/2, vals_10_17.values, width, label="10–17시 (평일만)", color=palette[2])
plt.bar(x + width/2, vals_other.values,  width, label="그 외 시간 (평일만)", color=palette[3])

plt.xticks(x, years_str)
plt.ylim(0, 100)
plt.ylabel("비율 (%)")
plt.title("연도별 (10–17시) vs (그 외 시간) 무임승차 이용 비율 – 평일만 (100% 정규화)")
plt.legend()

# 퍼센트 라벨
for xi, v in zip(x - width/2, vals_10_17.values):
    plt.text(xi, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
for xi, v in zip(x + width/2, vals_other.values):
    plt.text(xi, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)

plt.tight_layout()
plt.show()

# (선택) CSV 저장
# yearly_ratio.to_csv("연도별_평일_10to17_vs_기타_비율(100퍼센트정규화).csv", encoding="utf-8-sig")
