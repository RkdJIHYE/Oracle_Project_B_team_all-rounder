import folium
import pandas as pd
import numpy as np
from pathlib import Path

fac_dist = pd.read_csv("/Users/jihye/Documents/하이태커코드정리/서울교통공사1~9호선/1000m이내 시설 모음 .csv")

# 중심점 (서울 시청 좌표)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 지하철역 표시
for _, row in fac_dist.drop_duplicates("최근접_역명").iterrows():
    folium.CircleMarker(
        location=[row["최근접_역_위도"], row["최근접_역_경도"]],
        radius=5, color="blue", fill=True, fill_opacity=0.7,
        popup=f"{row['최근접_역명']} ({row['최근접_역_호선']})"
    ).add_to(m)

# 시설 표시
for _, row in fac_dist.iterrows():
    folium.CircleMarker(
        location=[row["시설위도"], row["시설경도"]],
        radius=3, color="red", fill=True, fill_opacity=0.6,
        popup=row["시설명"]
    ).add_to(m)

# (옵션) 시설→최근접역 선 연결
for _, row in fac_dist.iterrows():
    folium.PolyLine(
        locations=[
            [row["시설위도"], row["시설경도"]],
            [row["최근접_역_위도"], row["최근접_역_경도"]],
        ],
        color="gray", weight=1, opacity=0.4
    ).add_to(m)

m.save("서울_시설_역_접근성_지도_1000m.html")
