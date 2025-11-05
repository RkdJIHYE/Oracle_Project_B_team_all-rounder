# -*- coding: utf-8 -*-
"""
월별 인기 하차역 Top5 추이 그래프 (한글 폰트 깨짐 방지 버전)
- 입력: 서울_하차_월평균.csv  (컬럼: 월, 평일휴일, 역명, 승하차구분, ... , 평균일일합계)
- 기능:
  1) '월' 값을 'YYYY-MM' 형식으로 통일 (예: Jul-21 -> 2021-07)
  2) 평일+하차만 필터 (해당 컬럼이 있으면)
  3) 역별 총 하차량(평균일일합계 합계) 기준 Top 5 선택
  4) 월별 추이 라인그래프 출력 및 저장
  5) 변환된 전체 CSV를 '서울_하차_월평균_변환.csv'로 저장 (UTF-8-SIG)
"""

import os
import platform
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
from pathlib import Path

# =========================
# 0) 사용자 설정
# =========================
# VS Code에서 현재 파일 기준 상대경로로 두거나, 절대경로로 변경하세요.
IN_CSV  = Path("/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/출력/서울_하차_월평균_형식정리.csv")      # 원본
OUT_CSV = Path("서울_하차_월평균_변환.csv")  # 변환 저장본
OUT_PNG = Path("월별_인기하차역_Top5_추이.png")

# =========================
# 1) 한글 폰트 자동 설정
# =========================
def set_korean_font():
    system = platform.system()
    # 우선순위 후보
    if system == "Darwin":   # macOS
        candidates = ["AppleGothic", "NanumGothic", "Malgun Gothic"]
    elif system == "Windows":
        candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic"]
    else:  # Linux
        candidates = ["NanumGothic", "Malgun Gothic", "AppleGothic"]

    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            rcParams["font.family"] = name
            break
    # 한글 마이너스 기호 깨짐 방지
    rcParams["axes.unicode_minus"] = False

set_korean_font()

# =========================
# 2) CSV 로드 (인코딩 안전)
# =========================
def read_csv_safely(p: Path) -> pd.DataFrame:
    last_err = None
    for enc in ["utf-8", "utf-8-sig", "cp949"]:
        try:
            return pd.read_csv(p, encoding=enc)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"CSV 읽기 실패: {p} / 마지막 오류: {last_err}")

if not IN_CSV.exists():
    raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {IN_CSV.resolve()}")

df = read_csv_safely(IN_CSV).copy()

# =========================
# 3) '월' 컬럼을 YYYY-MM으로 통일
# =========================
if "월" not in df.columns:
    raise KeyError("'월' 컬럼이 없습니다. CSV를 확인하세요.")

# 다양한 형식 대응: 'YYYY-MM' 또는 'Jul-21' 등
def normalize_month_col(series: pd.Series) -> pd.Series:
    # 1차: YYYY-MM
    s = pd.to_datetime(series, format="%Y-%m", errors="coerce")
    # 2차: 영문 약어-2자리 연도 (Jul-21 등)
    mask = s.isna()
    if mask.any():
        s2 = pd.to_datetime(series[mask], format="%b-%y", errors="coerce")
        s.loc[mask] = s2
    # 3차: 최종 파싱 (자동 추론)
    mask = s.isna()
    if mask.any():
        s3 = pd.to_datetime(series[mask], errors="coerce")
        s.loc[mask] = s3
    return s.dt.strftime("%Y-%m")

df["월"] = normalize_month_col(df["월"])

# =========================
# 4) 안전 캐스팅 & 필터 (평일+하차)
# =========================
# 평균일일합계 숫자화
if "평균일일합계" not in df.columns:
    raise KeyError("'평균일일합계' 컬럼이 없습니다. CSV를 확인하세요.")
df["평균일일합계"] = pd.to_numeric(df["평균일일합계"], errors="coerce").fillna(0)

# 선택적 필터: 해당 컬럼이 있을 때만 적용
if "평일휴일" in df.columns:
    df = df[df["평일휴일"] == "평일"]
if "승하차구분" in df.columns:
    df = df[df["승하차구분"] == "하차"]

# =========================
# 5) 변환본 전체 저장 (Excel 친화적 UTF-8-SIG)
# =========================
df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"[저장] 변환된 CSV -> {OUT_CSV.resolve()}  (행 {len(df):,} / 열 {df.shape[1]})")

# =========================
# 6) Top5 역 선정 (총 하차량 합계 기준)
# =========================
if "역명" not in df.columns:
    raise KeyError("'역명' 컬럼이 없습니다. CSV를 확인하세요.")

popular = (
    df.groupby("역명")["평균일일합계"]
      .sum()
      .sort_values(ascending=False)
)
top5 = list(popular.head(5).index)
print("[Top5 역]", ", ".join(top5))

# =========================
# 7) 월별 추이 라인그래프
# =========================
trend = (
    df.groupby(["월", "역명"])["평균일일합계"]
      .mean()
      .reset_index()
)

# 월을 시간으로 정렬
trend["_월_dt"] = pd.to_datetime(trend["월"], format="%Y-%m", errors="coerce")
trend = trend.sort_values(["_월_dt", "역명"])

plt.figure(figsize=(12, 6))
for st in top5:
    sub = trend[trend["역명"] == st]
    plt.plot(sub["_월_dt"], sub["평균일일합계"], marker="o", linewidth=2, label=st)

plt.title("월별 인기 하차역 Top 5 추이", fontsize=14)
plt.xlabel("월", fontsize=12)
plt.ylabel("평균 일일 하차 인원", fontsize=12)
plt.legend(loc="best")
plt.grid(True, alpha=0.3)
plt.tight_layout()

# 그래프 파일 저장
plt.savefig(OUT_PNG, dpi=200)
print(f"[저장] 그래프 이미지 -> {OUT_PNG.resolve()}")

# 창에 표시 (VS Code Python: plot viewer에서 확인 가능)
plt.show()
