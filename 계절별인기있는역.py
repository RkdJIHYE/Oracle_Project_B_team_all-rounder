# -*- coding: utf-8 -*-
"""
계절별 인기 역 Top10 분석 & 시각화 (한글 깨짐 방지 + openpyxl 엔진 사용)
- 입력: 시간대별_월평균_평일휴일_역별_승하차_통합(...) CSV
- 출력: seasonal_top10_stations.csv, seasonal_top10_stations.xlsx
       각 계절별 Top10 가로 막대 그래프 PNG
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
# 0) 사용자 설정: 입력 파일 경로 / 출력 폴더
# ------------------------------------------------------------
INPUT_CSV = r"# -*- coding: utf-8 -*-"
"""
계절별 인기 역 Top10 분석 & 시각화 (한글 깨짐 방지 + openpyxl 엔진 사용)
- 입력: 시간대별_월평균_평일휴일_역별_승하차_통합(...) CSV
- 출력: seasonal_top10_stations.csv, seasonal_top10_stations.xlsx
       각 계절별 Top10 가로 막대 그래프 PNG
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
# 0) 사용자 설정: 입력 파일 경로 / 출력 폴더
# ------------------------------------------------------------
INPUT_CSV = r"/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/출력/시간대별_월평균_평일휴일_역별_승하차_통합(반올림_행합계포함).csv"  # <-- 여기를 자신의 경로로 변경
OUTPUT_DIR = r"./seasonal_top10_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------
# 1) 한글 폰트 설정 (운영체제별 자동 선택)
# ------------------------------------------------------------
def set_korean_font():
    system = platform.system().lower()
    candidates = []
    if "darwin" in system or "mac" in system:
        candidates = ["AppleGothic"]
    elif "windows" in system:
        candidates = ["Malgun Gothic", "맑은 고딕"]
    else:  # Linux or others
        candidates = ["Noto Sans CJK KR", "NotoSansCJKkr", "Noto Sans KR", "NanumGothic"]

    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = None
    for name in candidates:
        if any(name.lower() in f.lower() for f in available):
            chosen = name
            break

    if chosen is None:
        print("[경고] 한글 폰트를 찾지 못했습니다. 그래프에 네모(□)가 보일 수 있어요.")
        if "linux" in system:
            print("리눅스인 경우 다음으로 설치 후 다시 실행하세요:")
            print("  sudo apt-get update && sudo apt-get install -y fonts-noto-cjk")
    else:
        rcParams["font.family"] = chosen

    rcParams["axes.unicode_minus"] = False

set_korean_font()

# ------------------------------------------------------------
# 2) CSV 강건 로딩
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
    print(f"[오류] 입력 파일을 찾을 수 없습니다: {INPUT_CSV}")
    sys.exit(1)

df = read_csv_robust(INPUT_CSV)
df.columns = [re.sub(r"\s+", "", str(c)) for c in df.columns]

# ------------------------------------------------------------
# 3) 필수 컬럼 탐지
# ------------------------------------------------------------
if "역명" not in df.columns:
    print("[오류] '역명' 컬럼을 찾지 못했습니다. 현재 컬럼:", df.columns.tolist())
    sys.exit(1)

STATION = "역명"

def to_month_value(x):
    s = str(x).strip()
    m = re.match(r"^\d{4}-(\d{1,2})$", s)
    if m: return int(m.group(1))
    m = re.match(r"^\d{6}$", s)
    if m: return int(s[4:6])
    if re.match(r"^\d{1,2}$", s):
        return int(s)
    try:
        return pd.to_datetime(s).month
    except Exception:
        return np.nan

MONTH_COL = None
if "월" in df.columns:
    MONTH_COL = "월"
else:
    for cand in ["날짜", "수송일자", "기준일자", "년월일", "Date"]:
        if cand in df.columns:
            df["_월"] = df[cand].apply(to_month_value)
            MONTH_COL = "_월"
            break

if MONTH_COL is None:
    print("[오류] 월/날짜 정보를 찾지 못했습니다.")
    sys.exit(1)

time_cols = [c for c in df.columns if "시간대" in c]
df[time_cols] = df[time_cols].apply(pd.to_numeric, errors="coerce")

TOTAL_COL = None
for cand in ["평균일일합계", "일일합계", "합계", "총합", "행합계"]:
    if cand in df.columns:
        TOTAL_COL = cand
        break
if TOTAL_COL is None:
    df["_총합(시간대합)"] = df[time_cols].sum(axis=1, skipna=True)
    TOTAL_COL = "_총합(시간대합)"

# ------------------------------------------------------------
# 4) 월 → 계절 매핑
# ------------------------------------------------------------
def month_to_season(m):
    m = to_month_value(m)
    if pd.isna(m): return np.nan
    if m in [3,4,5]: return "봄(Spring)"
    if m in [6,7,8]: return "여름(Summer)"
    if m in [9,10,11]: return "가을(Autumn)"
    if m in [12,1,2]: return "겨울(Winter)"
    return np.nan

df["계절"] = df[MONTH_COL].apply(month_to_season)
df = df.dropna(subset=["계절"])

# ------------------------------------------------------------
# 5) 집계 및 Top10
# ------------------------------------------------------------
agg = df.groupby(["계절", STATION], as_index=False)[TOTAL_COL].sum()
SEASONS = ["봄(Spring)", "여름(Summer)", "가을(Autumn)", "겨울(Winter)"]

top10_all = []
for s in SEASONS:
    sub = agg[agg["계절"] == s].sort_values(TOTAL_COL, ascending=False).head(10).copy()
    if not sub.empty:
        sub["순위"] = range(1, len(sub)+1)
        top10_all.append(sub)
if not top10_all:
    print("[오류] 계절별 Top10 결과가 비었습니다.")
    sys.exit(1)

top10_all = pd.concat(top10_all, ignore_index=True)[["계절","순위",STATION,TOTAL_COL]]

# ------------------------------------------------------------
# 6) 저장 (CSV + XLSX with openpyxl)
# ------------------------------------------------------------
csv_out = os.path.join(OUTPUT_DIR, "seasonal_top10_stations.csv")
xlsx_out = os.path.join(OUTPUT_DIR, "seasonal_top10_stations.xlsx")
top10_all.to_csv(csv_out, index=False, encoding="utf-8-sig")

with pd.ExcelWriter(xlsx_out, engine="openpyxl") as writer:
    for s in SEASONS:
        sub = top10_all[top10_all["계절"] == s]
        if not sub.empty:
            sub.to_excel(writer, sheet_name=s, index=False)

print(f"[완료] CSV 저장: {csv_out}")
print(f"[완료] XLSX 저장: {xlsx_out}")

# ------------------------------------------------------------
# 7) 시각화
# ------------------------------------------------------------
def plot_top10(df_top10, season_name):
    data = df_top10.sort_values("순위")
    plt.figure(figsize=(10,6))
    plt.barh(data[STATION], data[TOTAL_COL])
    plt.gca().invert_yaxis()
    plt.title(f"{season_name} Top 10 역 (총 이용량 기준)")
    plt.xlabel("총 이용량(합계)")
    plt.ylabel("역명")
    plt.tight_layout()

    png_path = os.path.join(OUTPUT_DIR, f"{season_name.replace('/', '_')}_Top10.png")
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[완료] 그래프 저장: {png_path}")

for s in SEASONS:
    sub = top10_all[top10_all["계절"] == s]
    if not sub.empty:
        plot_top10(sub, s)

print("[전체 완료] 계절별 Top10 산출 및 그래프 저장이 끝났습니다.")
" # <-- 여기를 자신의 경로로 변경"
OUTPUT_DIR = r"./seasonal_top10_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------
# 1) 한글 폰트 설정 (운영체제별 자동 선택)
# ------------------------------------------------------------
def set_korean_font():
    system = platform.system().lower()
    candidates = []
    if "darwin" in system or "mac" in system:
        candidates = ["AppleGothic"]
    elif "windows" in system:
        candidates = ["Malgun Gothic", "맑은 고딕"]
    else:  # Linux or others
        candidates = ["Noto Sans CJK KR", "NotoSansCJKkr", "Noto Sans KR", "NanumGothic"]

    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = None
    for name in candidates:
        if any(name.lower() in f.lower() for f in available):
            chosen = name
            break

    if chosen is None:
        print("[경고] 한글 폰트를 찾지 못했습니다. 그래프에 네모(□)가 보일 수 있어요.")
        if "linux" in system:
            print("리눅스인 경우 다음으로 설치 후 다시 실행하세요:")
            print("  sudo apt-get update && sudo apt-get install -y fonts-noto-cjk")
    else:
        rcParams["font.family"] = chosen

    rcParams["axes.unicode_minus"] = False

set_korean_font()

# ------------------------------------------------------------
# 2) CSV 강건 로딩
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
    print(f"[오류] 입력 파일을 찾을 수 없습니다: {INPUT_CSV}")
    sys.exit(1)

df = read_csv_robust(INPUT_CSV)
df.columns = [re.sub(r"\s+", "", str(c)) for c in df.columns]

# ------------------------------------------------------------
# 3) 필수 컬럼 탐지
# ------------------------------------------------------------
if "역명" not in df.columns:
    print("[오류] '역명' 컬럼을 찾지 못했습니다. 현재 컬럼:", df.columns.tolist())
    sys.exit(1)

STATION = "역명"

def to_month_value(x):
    s = str(x).strip()
    m = re.match(r"^\d{4}-(\d{1,2})$", s)
    if m: return int(m.group(1))
    m = re.match(r"^\d{6}$", s)
    if m: return int(s[4:6])
    if re.match(r"^\d{1,2}$", s):
        return int(s)
    try:
        return pd.to_datetime(s).month
    except Exception:
        return np.nan

MONTH_COL = None
if "월" in df.columns:
    MONTH_COL = "월"
else:
    for cand in ["날짜", "수송일자", "기준일자", "년월일", "Date"]:
        if cand in df.columns:
            df["_월"] = df[cand].apply(to_month_value)
            MONTH_COL = "_월"
            break

if MONTH_COL is None:
    print("[오류] 월/날짜 정보를 찾지 못했습니다.")
    sys.exit(1)

time_cols = [c for c in df.columns if "시간대" in c]
df[time_cols] = df[time_cols].apply(pd.to_numeric, errors="coerce")

TOTAL_COL = None
for cand in ["평균일일합계", "일일합계", "합계", "총합", "행합계"]:
    if cand in df.columns:
        TOTAL_COL = cand
        break
if TOTAL_COL is None:
    df["_총합(시간대합)"] = df[time_cols].sum(axis=1, skipna=True)
    TOTAL_COL = "_총합(시간대합)"

# ------------------------------------------------------------
# 4) 월 → 계절 매핑
# ------------------------------------------------------------
def month_to_season(m):
    m = to_month_value(m)
    if pd.isna(m): return np.nan
    if m in [3,4,5]: return "봄(Spring)"
    if m in [6,7,8]: return "여름(Summer)"
    if m in [9,10,11]: return "가을(Autumn)"
    if m in [12,1,2]: return "겨울(Winter)"
    return np.nan

df["계절"] = df[MONTH_COL].apply(month_to_season)
df = df.dropna(subset=["계절"])

# ------------------------------------------------------------
# 5) 집계 및 Top10
# ------------------------------------------------------------
agg = df.groupby(["계절", STATION], as_index=False)[TOTAL_COL].sum()
SEASONS = ["봄(Spring)", "여름(Summer)", "가을(Autumn)", "겨울(Winter)"]

top10_all = []
for s in SEASONS:
    sub = agg[agg["계절"] == s].sort_values(TOTAL_COL, ascending=False).head(10).copy()
    if not sub.empty:
        sub["순위"] = range(1, len(sub)+1)
        top10_all.append(sub)
if not top10_all:
    print("[오류] 계절별 Top10 결과가 비었습니다.")
    sys.exit(1)

top10_all = pd.concat(top10_all, ignore_index=True)[["계절","순위",STATION,TOTAL_COL]]

# ------------------------------------------------------------
# 6) 저장 (CSV + XLSX with openpyxl)
# ------------------------------------------------------------
csv_out = os.path.join(OUTPUT_DIR, "seasonal_top10_stations.csv")
xlsx_out = os.path.join(OUTPUT_DIR, "seasonal_top10_stations.xlsx")
top10_all.to_csv(csv_out, index=False, encoding="utf-8-sig")

with pd.ExcelWriter(xlsx_out, engine="openpyxl") as writer:
    for s in SEASONS:
        sub = top10_all[top10_all["계절"] == s]
        if not sub.empty:
            sub.to_excel(writer, sheet_name=s, index=False)

print(f"[완료] CSV 저장: {csv_out}")
print(f"[완료] XLSX 저장: {xlsx_out}")

# ------------------------------------------------------------
# 7) 시각화
# ------------------------------------------------------------
def plot_top10(df_top10, season_name):
    data = df_top10.sort_values("순위")
    plt.figure(figsize=(10,6))
    plt.barh(data[STATION], data[TOTAL_COL])
    plt.gca().invert_yaxis()
    plt.title(f"{season_name} Top 10 역 (총 이용량 기준)")
    plt.xlabel("총 이용량(합계)")
    plt.ylabel("역명")
    plt.tight_layout()

    png_path = os.path.join(OUTPUT_DIR, f"{season_name.replace('/', '_')}_Top10.png")
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[완료] 그래프 저장: {png_path}")

for s in SEASONS:
    sub = top10_all[top10_all["계절"] == s]
    if not sub.empty:
        plot_top10(sub, s)

print("[전체 완료] 계절별 Top10 산출 및 그래프 저장이 끝났습니다.")
