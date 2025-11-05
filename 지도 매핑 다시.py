import json
import pandas as pd
import numpy as np
import folium
from folium.features import DivIcon
from branca.colormap import LinearColormap

# ----------------------------------
# 1) 입력 경로
# ----------------------------------
# 역 단위 데이터(자치구, 총점 등 포함)
station_csv = "/Users/jihye/Documents/하이태커코드정리/찐최종+위경도합.csv"
# 서울 '자치구' 경계 GeoJSON (예: seoul_municipalities_geo_simple.json)
seoul_geojson_path = "/Users/jihye/Documents/하이태커코드정리/seoul_gu_boundary.geojson"

# ----------------------------------
# 2) 데이터 로드 & 자치구 점수 집계
# ----------------------------------
def read_csv_smart(p):
    try:
        return pd.read_csv(p, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(p, encoding="cp949")

df = read_csv_smart(station_csv)

# 컬럼 자동 인식
def pick(cols, cands):
    for c in cands:
        if c in cols: return c
    return None

cols = df.columns.tolist()
col_gu    = pick(cols, ["자치구","구","district","District"])
col_score = pick(cols, ["우선순위 점수","총점","score","Score"])

if col_gu is None:
    raise ValueError("CSV에 '자치구' 컬럼이 필요합니다.")
if col_score is None:
    # 총점이 없으면 역 개수 등 다른 지표로 만들어도 됩니다.
    # 여기서는 예시로 역 개수를 점수로 사용
    col_score = "_count_"
    df[col_score] = 1

# 자치구별 집계 (평균/합계 중 선택)
gu_score = (
    df.groupby(col_gu, as_index=False)[col_score]
      .mean()  # 필요시 .sum() 으로 변경
      .rename(columns={col_gu: "gu_name", col_score: "score"})
)

# 정규화(0~1) — 색상 일관된 표현을 위해
if gu_score["score"].nunique() > 1:
    s = gu_score["score"]
    gu_score["score_norm"] = (s - s.min()) / (s.max() - s.min())
else:
    gu_score["score_norm"] = 0.5  # 값이 모두 같으면 중간값

# ----------------------------------
# 3) GeoJSON 로드 & 중심 계산
# ----------------------------------
with open(seoul_geojson_path, "r", encoding="utf-8") as f:
    seoul_geo = json.load(f)

# 지도 중심(대략 서울시청 부근)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11, tiles="cartodbpositron")

# ----------------------------------
# 4) 색상 맵 & 범례(colormap)
# ----------------------------------
# 흰색→빨강 그라디언트
cmap = LinearColormap(colors=["#ffffff", "#ff0000"], vmin=0, vmax=1)
cmap.caption = "우선순위 점수"  # 하단 범례 제목

# ----------------------------------
# 5) 구 폴리곤 채우기(choropleth와 동일한 효과)
#    - feature.properties['SIG_KOR_NM'] 등 '구 이름' 속성 key가 파일마다 다릅니다.
#      아래 key_candidates 중 실제 있는 것으로 자동 선택합니다.
# ----------------------------------
# GeoJSON 속성에서 '구 이름' 키 추정
if len(seoul_geo["features"]) == 0:
    raise ValueError("GeoJSON에 features가 없습니다.")
prop_keys = seoul_geo["features"][0]["properties"].keys()
name_key = None
for cand in ["SIG_KOR_NM","name","gu_name","SIG_CD","SIG_ENG_NM"]:
    if cand in prop_keys:
        name_key = cand
        break
if name_key is None:
    raise ValueError(f"GeoJSON 속성에서 구 이름 키를 찾지 못했습니다. 속성 키 예: {list(prop_keys)}")

# 자치구 이름 정리(좌/우 공백 제거 등)
gu_score["gu_name_norm"] = gu_score["gu_name"].astype(str).str.strip()

# 지도에 폴리곤 + 라벨 추가
for feat in seoul_geo["features"]:
    gu_name = str(feat["properties"][name_key]).strip()
    # 점수 매칭
    row = gu_score[gu_score["gu_name_norm"] == gu_name]
    if row.empty:
        score_norm = 0.0
        score_disp = ""
    else:
        score_norm = float(row["score_norm"].iloc[0])
        score_disp = f"{row['score'].iloc[0]:.2f}"

    fill_color = cmap(score_norm)
    # GeoJson으로 폴리곤(검은 테두리 + 채우기)
    gj = folium.GeoJson(
        data=feat,
        style_function=lambda x, fc=fill_color: {
            "fillColor": fc,
            "color": "#222222",
            "weight": 1.5,
            "fillOpacity": 0.85,
        },
        highlight_function=lambda x: {
            "weight": 3,
            "color": "#000000",
            "fillOpacity": 0.95
        },
        tooltip=folium.Tooltip(gu_name, sticky=True),
        name=gu_name
    )
    gj.add_to(m)

    # 센트로이드 계산(간단 평균) → 라벨 배치
    def centroid_of_feature(feature):
        # Polygon/MultiPolygon 모두 처리
        geom = feature["geometry"]
        coords_all = []
        if geom["type"] == "Polygon":
            for ring in geom["coordinates"]:
                coords_all.extend(ring)
        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                for ring in poly:
                    coords_all.extend(ring)
        if not coords_all:
            return None
        # lon, lat 평균
        lons = [c[0] for c in coords_all]
        lats = [c[1] for c in coords_all]
        return (np.mean(lats), np.mean(lons))  # (lat, lon)

    cent = centroid_of_feature(feat)
    if cent:
        lat, lon = cent
        # 라벨: 구이름 + (점수)
        label_html = f"""
        <div style="
            background-color: rgba(255,255,255,0.9);
            border: 1px solid #f5a5a5;
            border-radius: 10px;
            padding: 4px 8px;
            font-size: 12px;
            color: #c43d3d;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
            ">
            <b>{gu_name}</b>{f" ({score_disp})" if score_disp else ""}
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            icon=DivIcon(icon_size=(150,36), icon_anchor=(0,0), html=label_html)
        ).add_to(m)

# 범례(그라디언트) 추가
m.add_child(cmap)

# 저장
out_html = "/Users/jihye/Documents/하이태커코드정리/seoul_gu_choropleth.html"
m.save(out_html)
print(f"완료: {out_html}")
# 주피터에서는 m 객체를 출력하면 즉시 미리보기 가능합니다.
# m
