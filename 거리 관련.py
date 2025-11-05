# -*- coding: utf-8 -*-
"""
서울 지하철 역 ↔ 문화체육관광 전시/시설 거리 계산 스크립트
- 같은 자치구 내에서만 역×시설 거리(하버사인, 미터)를 계산합니다.
- 결과물:
  1) 구별_역_vs_시설_모든쌍_거리_m.csv
  2) 역별_최근접시설.csv
  3) 시설별_최근접역.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ===== 설정값 =====
BASE_DIR = "."  # 현재 폴더 기준 (필요시 절대경로로 수정)
STATION_CSV = "서울교통공사 1~9호선과 위경도 자치구 포함.csv"
FACILITY_CSV = "서울 문화체육 관광분야전시관 시설 데이터.csv"
OUT_DIR = "station_facility_distances"  # 결과 저장 폴더

# ===== 유틸 =====
def read_csv_smart(path: str) -> pd.DataFrame:
    """인코딩을 자동 시도하여 CSV 읽기"""
    for enc in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    # 마지막 시도 (에러 무시)
    return pd.read_csv(path, encoding_errors="ignore")

def haversine_m(lat1, lon1, lat2, lon2):
    """
    하버사인 거리 계산 (미터)
    - lat1, lon1: (n,1) 형태 배열
    - lat2, lon2: (1,m) 형태 배열
    반환: (n,m) 거리 행렬
    """
    R = 6371000.0  # meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dl   = np.radians(lon2 - lon1)
    a = np.sin(dphi/2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dl/2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

# ===== 메인 로직 =====
def main():
    base = Path(BASE_DIR)
    out_dir = base / OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) 데이터 로딩
    st = read_csv_smart(str(base / STATION_CSV))
    fc = read_csv_smart(str(base / FACILITY_CSV))

    # 2) 컬럼 정리(공백 제거)
    st.columns = [c.strip() for c in st.columns]
    fc.columns = [c.strip() for c in fc.columns]

    # 3) 현재 파일에 맞춘 명시적 컬럼 매핑
    #    (필요 시 아래를 본인 데이터에 맞춰 바꾸세요)
    st_cols = dict(gu="자치구", name="역명", line="호선", lat="위도", lng="경도")
    fc_cols = dict(gu="SIGNGU_NM", name="POI_NM", cat="CL_NM", lat="위도", lng="경도")

    # (안전) 숫자 변환
    for df, lat, lng in ((st, st_cols["lat"], st_cols["lng"]),
                         (fc, fc_cols["lat"], fc_cols["lng"])):
        df[lat] = pd.to_numeric(df[lat], errors="coerce")
        df[lng] = pd.to_numeric(df[lng], errors="coerce")

    # 유효 좌표/자치구만
    st_v = st.dropna(subset=[st_cols["gu"], st_cols["lat"], st_cols["lng"]]).copy()
    fc_v = fc.dropna(subset=[fc_cols["gu"], fc_cols["lat"], fc_cols["lng"]]).copy()

    # 4) 자치구 교집합만 대상으로 처리
    districts = sorted(set(st_v[st_cols["gu"]]).intersection(set(fc_v[fc_cols["gu"]])))

    rows = []
    for gu in districts:
        st_g = st_v[st_v[st_cols["gu"]] == gu][[st_cols["name"], st_cols["line"], st_cols["lat"], st_cols["lng"]]].reset_index(drop=True)
        fc_g = fc_v[fc_v[fc_cols["gu"]] == gu][[fc_cols["name"], fc_cols["cat"], fc_cols["lat"], fc_cols["lng"]]].reset_index(drop=True)
        if st_g.empty or fc_g.empty:
            continue

        # 벡터화 계산 (n역 × m시설)
        s_lat = st_g[st_cols["lat"]].values.reshape(-1, 1)
        s_lng = st_g[st_cols["lng"]].values.reshape(-1, 1)
        f_lat = fc_g[fc_cols["lat"]].values.reshape(1, -1)
        f_lng = fc_g[fc_cols["lng"]].values.reshape(1, -1)

        dmat = haversine_m(s_lat, s_lng, f_lat, f_lng)  # (n, m)

        # 롱테이블로 펼치기
        for i in range(st_g.shape[0]):
            for j in range(fc_g.shape[0]):
                rows.append([
                    gu,
                    st_g.loc[i, st_cols["name"]],
                    st_g.loc[i, st_cols["line"]],
                    float(st_g.loc[i, st_cols["lat"]]),
                    float(st_g.loc[i, st_cols["lng"]]),
                    fc_g.loc[j, fc_cols["name"]],
                    fc_g.loc[j, fc_cols["cat"]],
                    float(fc_g.loc[j, fc_cols["lat"]]),
                    float(fc_g.loc[j, fc_cols["lng"]]),
                    float(dmat[i, j])
                ])

    # 5) 결과 데이터프레임
    dist_cols = ["자치구", "역명", "호선", "역위도", "역경도", "시설명", "시설유형", "시설위도", "시설경도", "거리_m"]
    dist_df = pd.DataFrame(rows, columns=dist_cols)

    # 6) 저장: 전체쌍
    full_path = out_dir / "구별_역_vs_시설_모든쌍_거리_m.csv"
    dist_df.to_csv(full_path, index=False, encoding="utf-8-sig")

    # 7) 역별 최근접 시설
    nearest_fac_per_station = (
        dist_df.sort_values(["자치구", "역명", "거리_m"])
               .groupby(["자치구", "역명"], as_index=False)
               .first()
               .rename(columns={
                   "시설명":"최근접_시설명",
                   "시설유형":"최근접_시설유형",
                   "시설위도":"최근접_시설_위도",
                   "시설경도":"최근접_시설_경도",
                   "거리_m":"최근접_시설까지_m"
               })
    )
    near_fac_path = out_dir / "역별_최근접시설.csv"
    nearest_fac_per_station.to_csv(near_fac_path, index=False, encoding="utf-8-sig")

    # 8) 시설별 최근접 역
    nearest_st_per_fac = (
        dist_df.sort_values(["자치구", "시설명", "거리_m"])
               .groupby(["자치구", "시설명"], as_index=False)
               .first()
               .rename(columns={
                   "역명":"최근접_역명",
                   "호선":"최근접_역_호선",
                   "역위도":"최근접_역_위도",
                   "역경도":"최근접_역_경도",
                   "거리_m":"최근접_역까지_m"
               })
    )
    near_st_path = out_dir / "시설별_최근접역.csv"
    nearest_st_per_fac.to_csv(near_st_path, index=False, encoding="utf-8-sig")

    print("✅ 완료")
    print(f"- 전체쌍: {full_path}")
    print(f"- 역별 최근접: {near_fac_path}")
    print(f"- 시설별 최근접: {near_st_path}")
    print(f"행 개수(전체쌍/역->시설/시설->역): {dist_df.shape} / {nearest_fac_per_station.shape} / {nearest_st_per_fac.shape}")

if __name__ == "__main__":
    main()
