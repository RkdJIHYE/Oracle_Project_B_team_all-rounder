# -*- coding: utf-8 -*-
"""
[평일만] 계절별 인기 역 Top10 (한 plot에 4계절 표시)
- 입력: CSV (서울시 지하철 월평균 승하차 통합)
- 조건: 평일만 사용
- 출력: CSV, XLSX, 계절별 Top10을 한 그림으로 (subplot) 저장
"""

import os
import re
import sys
import platform
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams

warnings.filterwarnings("ignore")

# ------------------------------------------------------------
# 0) 사용자 설정
# ------------------------------------------------------------
INPUT_CSV = r"/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/출력/시간대별_월평균_평일휴일_역별_승하차_통합(반올림_행합계포함).csv"  # <-- 여기를 자신의 경로로 변경
OUTPUT_DIR = r"./seasonal_top10_weekday_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------
# 1) 한글 폰트 자동 설정
# ------------------------------------------------------------
def set_korean_font():
    system = platform.system().lower()
    candidates = []
    if "darwin" in system or "mac" in system:
        candidates = ["AppleGothic"]
    elif "windows" in system:
        candidates = ["Malgun Gothic", "맑은 고딕"]
    else:  # Linux
        candidates = ["Noto Sans CJK KR", "NanumGothic", "UnDotum", "DejaVu Sans"]

    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = None
    for name in candidates:
        if any(name.lower() in f.lower() for f in available):
            chosen = name
            break
    if chosen is None:
        print("[경고] 한글 폰트가 없어 그래프에 네모(□)가 보일 수 있습니다.")
    else:
        rcParams["font.family"] = chosen
    rcParams["axes.unicode_minus"] = False

set_korean_font()

# ------------------------------------------------------------
# 2) CSV 읽기 (인코딩 자동 탐색)
# ------------------------------------------------------------
def read_csv_robust(path):
    encodings = ["utf-8-sig", "cp949", "euc-kr", "utf-8"]
    last_err = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:
            last_err = e
    raise last_err

if not os.path.exists(INPUT_CSV):
    print(f"[오류] 입력 파일 없음: {INPUT_CSV}")
    sys.exit(1)

df = read_csv_robust(INPUT_CSV)
df.columns = [re.sub(r"\s+", "", str(c)) for c in df.columns]

# ------------------------------------------------------------
# 3) 주요 컬럼 처리
# ------------------------------------------------------------
if "역명" not in df.columns:
    print("[오류] '역명' 컬럼이 없습니다. 현재 컬럼:", df.columns.tolist())
    sys.exit(1)
STATION = "역명"

def to_month_value(x):
    s = str(x).strip()
    m = re.match(r"^\d{4}-(\d{1,2})$", s)
    if m:
        return int(m.group(1))
    m = re.match(r"^\d{6}$", s)
    if m:
        return int(s[4:6])
    if re.match(r"^\d{1,2}$", s):
        return int(s)
    try:
        return pd.to_datetime(s).month
    except Exception:
        return np.nan

MONTH_COL = "월" if "월" in df.columns else None
if MONTH_COL is None:
    for cand in ["날짜", "수송일자", "기준일자", "년월일", "Date"]:
        if cand in df.columns:
            df["_월"] = df[cand].apply(to_month_value)
            MONTH_COL = "_월"
            break
if MONTH_COL is None:
    print("[오류] 월/날짜 정보가 없습니다.")
    sys.exit(1)

WEEKFLAG_COL = None
for cand in ["평일휴일", "평일/휴일", "평일휴일구분", "요일구분"]:
    if cand in df.columns:
        WEEKFLAG_COL = cand
        break
if WEEKFLAG_COL is None:
    print("[오류] 평일/휴일 컬럼 없음.")
    sys.exit(1)

time_cols = [c for c in df.columns if "시간대" in c]
df[time_cols] = df[time_cols].apply(pd.to_numeric, errors="coerce")

TOTAL_COL = None
for cand in ["평균일일합계", "일일합계", "합계", "총합", "행합계"]:
    if cand in df.columns:
        TOTAL_COL = cand
        break
if TOTAL_COL is None:
    df["_총합"] = df[time_cols].sum(axis=1, skipna=True)
    TOTAL_COL = "_총합"

# ------------------------------------------------------------
# 4) 월 → 계절
# ------------------------------------------------------------
def month_to_season(m):
    m = to_month_value(m)
    if pd.isna(m): return np.nan
    m = int(m)
    if m in [3,4,5]: return "봄(Spring)"
    if m in [6,7,8]: return "여름(Summer)"
    if m in [9,10,11]: return "가을(Autumn)"
    if m in [12,1,2]: return "겨울(Winter)"
    return np.nan

df["계절"] = df[MONTH_COL].apply(month_to_season)
df = df.dropna(subset=["계절"])

# ------------------------------------------------------------
# 5) 평일만 필터링
# ------------------------------------------------------------
weekday_keywords = ["평일", "주중", "weekday"]
def is_weekday(val):
    if pd.isna(val): return False
    s = str(val).lower()
    return any(kw in s for kw in weekday_keywords)

df_weekday = df[df[WEEKFLAG_COL].apply(is_weekday)].copy()
if df_weekday.empty:
    print("[오류] 평일 데이터가 없습니다. 현재 값 예시:", df[WEEKFLAG_COL].unique()[:20])
    sys.exit(1)

# ------------------------------------------------------------
# 6) 집계 & Top10
# ------------------------------------------------------------
agg = df_weekday.groupby(["계절", STATION], as_index=False)[TOTAL_COL].sum()

SEASONS = ["봄(Spring)", "여름(Summer)", "가을(Autumn)", "겨울(Winter)"]
top10_all = []
for s in SEASONS:
    sub = agg[agg["계절"]==s].sort_values(TOTAL_COL, ascending=False).head(10).copy()
    if not sub.empty:
        sub["순위"] = range(1,len(sub)+1)
        top10_all.append(sub)
top10_all = pd.concat(top10_all, ignore_index=True)

# ------------------------------------------------------------
# 7) 저장 (CSV, XLSX)
# ------------------------------------------------------------
csv_out = os.path.join(OUTPUT_DIR,"seasonal_top10_weekday.csv")
xlsx_out = os.path.join(OUTPUT_DIR,"seasonal_top10_weekday.xlsx")
top10_all.to_csv(csv_out, index=False, encoding="utf-8-sig")
with pd.ExcelWriter(xlsx_out, engine="openpyxl") as writer:
    for s in SEASONS:
        sub = top10_all[top10_all["계절"]==s]
        if not sub.empty:
            sub.to_excel(writer, sheet_name=s, index=False)

print(f"[완료] CSV: {csv_out}")
print(f"[완료] XLSX: {xlsx_out}")

# ------------------------------------------------------------
# 8) 한 Plot에 4계절 서브플롯
# ------------------------------------------------------------
colors = {
    "봄(Spring)": "green",
    "여름(Summer)": "orange",
    "가을(Autumn)": "brown",
    "겨울(Winter)": "blue"
}

fig, axes = plt.subplots(2,2, figsize=(14,10))
axes = axes.flatten()

for i, season in enumerate(SEASONS):
    sub = top10_all[top10_all["계절"]==season].sort_values("순위")
    ax = axes[i]
    ax.barh(sub[STATION], sub[TOTAL_COL], color=colors.get(season,"gray"))
    ax.invert_yaxis()
    ax.set_title(season)
    ax.set_xlabel("총 이용량")
    ax.set_ylabel("역명")

plt.tight_layout()
png_out = os.path.join(OUTPUT_DIR,"seasonal_top10_weekday_subplot.png")
plt.savefig(png_out, dpi=150, bbox_inches="tight")
plt.close()
print(f"[완료] 한 Plot 그래프 저장: {png_out}")
