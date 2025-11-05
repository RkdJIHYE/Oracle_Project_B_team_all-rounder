import pandas as pd
from pathlib import Path
import re

# ===== 0) 최종 컬럼 순서 (요일 + 일일합계 포함, 고정) =====
desired_order = [
    "06-07시간대","06시간대이전","07-08시간대","08-09시간대","09-10시간대","10-11시간대",
    "11-12시간대","12-13시간대","13-14시간대","14-15시간대","15-16시간대","16-17시간대",
    "17-18시간대","18-19시간대","19-20시간대","20-21시간대","21-22시간대","22-23시간대",
    "23-24시간대","24시간대이후",
    "수송일자","요일","일일합계","승하차구분","역명","역번호","연번","날짜"
]

# 시간대 컬럼 목록 (합계 계산용)
time_cols = [
    "06-07시간대","06시간대이전","07-08시간대","08-09시간대","09-10시간대","10-11시간대",
    "11-12시간대","12-13시간대","13-14시간대","14-15시간대","15-16시간대","16-17시간대",
    "17-18시간대","18-19시간대","19-20시간대","20-21시간대","21-22시간대","22-23시간대",
    "23-24시간대","24시간대이후"
]

# ===== 1) 요일 매핑 (월=0 … 일=6) =====
weekday_ko = {0:"월요일",1:"화요일",2:"수요일",3:"목요일",4:"금요일",5:"토요일",6:"일요일"}

# ===== 2) 열 이름 표준화 함수 =====
def normalize_col(c: str) -> str:
    s = str(c).strip().replace(" ", "").replace("\u3000", "")
    # 시간대 표기 통일
    s = s.replace("06~07시간대","06-07시간대").replace("06~07","06-07시간대")
    s = s.replace("07~08시간대","07-08시간대")
    s = s.replace("08~09시간대","08-09시간대")
    s = s.replace("09~10시간대","09-10시간대")
    s = s.replace("10~11시간대","10-11시간대")
    s = s.replace("11~12시간대","11-12시간대")
    s = s.replace("12~13시간대","12-13시간대")
    s = s.replace("13~14시간대","13-14시간대")
    s = s.replace("14~15시간대","14-15시간대")
    s = s.replace("15~16시간대","15-16시간대")
    s = s.replace("16~17시간대","16-17시간대")
    s = s.replace("17~18시간대","17-18시간대")
    s = s.replace("18~19시간대","18-19시간대")
    s = s.replace("19~20시간대","19-20시간대")
    s = s.replace("20~21시간대","20-21시간대")
    s = s.replace("21~22시간대","21-22시간대")
    s = s.replace("22~23시간대","22-23시간대")
    # 자주 섞이는 열 보정
    s = s.replace("23시간대이후","23-24시간대")
    s = s.replace("24시간대 이후","24시간대이후")
    return s

# ===== 3) 파일 목록 =====
files = [
    "/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/서울교통공사_역별 일별 시간대별 노인 승하차인원 정보_20211231.csv",
    "/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/서울교통공사_역별 일별 시간대별 노인 승하차인원 정보_20221231.csv",
    "/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/서울교통공사_역별 일별 시간대별 노인 승하차인원 정보_20231231.csv",
]

# ===== 4) 읽기 + 날짜/요일/일일합계 추가 + 컬럼 표준화/고정 =====
dfs = []
for f in files:
    try:
        df = pd.read_csv(f, dtype=str)   # dtype=str로 타입 혼선 방지
    except UnicodeDecodeError:
        df = pd.read_csv(f, dtype=str, encoding="cp949")

    # 파일명에서 '날짜' 생성
    date_str = Path(f).stem.split("_")[-1]
    df["날짜"] = pd.to_datetime(date_str, format="%Y%m%d")

    # 열 이름 표준화
    df.columns = [normalize_col(c) for c in df.columns]

    # 수송일자 → datetime → 요일
    if "수송일자" in df.columns:
        s = df["수송일자"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8)
        dt = pd.to_datetime(s, format="%Y%m%d", errors="coerce")
        df["수송일자"] = dt
        df["요일"] = df["수송일자"].dt.weekday.map(weekday_ko)
    else:
        df["수송일자"] = pd.NaT
        df["요일"] = pd.NA

    # ---- 일일합계 계산 ----
    # 시간대 컬럼이 누락돼도 안전하게 채우기
    for col in time_cols:
        if col not in df.columns:
            df[col] = pd.NA
    # 숫자 변환 후 합계(결측은 0으로 처리)
    df[time_cols] = df[time_cols].apply(pd.to_numeric, errors="coerce")
    df["일일합계"] = df[time_cols].sum(axis=1, skipna=True).fillna(0).astype("Int64")

    # 누락 컬럼 보완 후 순서 강제
    for col in desired_order:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[desired_order]

    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

# ===== 5) 통합본 저장 =====
out_root = Path("/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/출력")
out_root.mkdir(parents=True, exist_ok=True)
merged_csv = out_root / "서울지하철_노인승하차_통합(요일_일일합계_컬럼고정).csv"
merged.to_csv(merged_csv, index=False, encoding="utf-8-sig")

# ===== 6) 안전한 폴더명 =====
def safe_name(name: str) -> str:
    s = str(name).strip()
    s = re.sub(r'[\\/:*?"<>|]', "_", s)
    s = re.sub(r"\s+", " ", s)
    return s

# ===== 7) (승하차구분 × 역명) 기준 폴더 생성 + 원본행 그대로 저장 (순서 고정) =====
per_station_root = out_root / "승하차_역별(요일_일일합계_컬럼고정)"
per_station_root.mkdir(parents=True, exist_ok=True)

for (gubun, station), df_grp in merged.groupby(["승하차구분", "역명"], dropna=False, sort=False):
    gubun_safe = safe_name(gubun)
    station_safe = safe_name(station)

    station_dir = per_station_root / gubun_safe / station_safe
    station_dir.mkdir(parents=True, exist_ok=True)

    out_csv = station_dir / f"{station_safe}_{gubun_safe}.csv"
    df_grp[desired_order].to_csv(out_csv, index=False, encoding="utf-8-sig")

print(f"[완료] 통합 파일: {merged_csv}")
print(f"[완료] 개별 폴더 루트: {per_station_root}")
