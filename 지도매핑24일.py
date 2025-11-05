import pandas as pd
import folium

# 1. 사용자 데이터 불러오기
file_path = "/Users/jihye/Documents/하이태커코드정리/A_화장실개수_추가csv.csv"
df = pd.read_csv(file_path, encoding="utf-8")

# 2. 서울 지하철 위경도 데이터 (예시 일부)
station_coords = {
    "제기동": [37.5822, 127.0345],
    "청량리": [37.5802, 127.0474],
    "종로5가": [37.5709, 127.0018],
    "연신내": [37.6190, 126.9210],
    "혜화": [37.5823, 127.0019],
    "안국": [37.5760, 126.9858],
    "선릉": [37.5045, 127.0490],
    "창동": [37.6531, 127.0474],
    "회현": [37.5585, 126.9780],
    "수유": [37.6380, 127.0265],
    # … 전체 역 추가 필요
}

# 3. 좌표 매핑
df["위도"] = df["역명"].map(lambda x: station_coords.get(x, [None, None])[0])
df["경도"] = df["역명"].map(lambda x: station_coords.get(x, [None, None])[1])

# 4. 지도 생성 (서울 중심 좌표)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 5. 마커 추가
for _, row in df.iterrows():
    if pd.notnull(row["위도"]):
        folium.CircleMarker(
            location=[row["위도"], row["경도"]],
            radius=row["총점"],  # 총점 크기 반영
            color="red" if row["총점"] >= 8 else "blue",
            fill=True,
            fill_opacity=0.6,
            popup=f"{row['역명']} (총점: {row['총점']})"
        ).add_to(m)

# 지도 저장
m.save("/Users/jihye/Documents/하이태커코드정리/station_score_map.html")
