import requests
import pandas as pd

# 1) 본인 서비스키 (그대로 params에 넣으면 requests가 URL 인코딩 처리함)
SERVICE_KEY = "wQP+Lc2rTuL73q4QDodUwoZ/it0NfKJPw1Rt1Fsc3Y4kOBUh7faLIBCKx+WS1AfH7UgqV8+vv80hRalWA/7XvA=="

# 2) Swagger에서 확인한 리소스(uddi) 매핑
UDDI_MAP = {
    "20211231": "uddi:560f9015-ae01-4cc8-8dd8-932f44fefdc1",
    "20221231": "uddi:61d4d369-b866-4759-9ffa-b9ab5d584ce9",
    "20230430": "uddi:b6d94fc8-2c12-4596-9c95-c713930d6ac6",
    "20230930": "uddi:0d11027b-9e35-4e18-bdde-be748b05fa69",
    "20231231": "uddi:488c1590-90be-46d0-b826-f2b8187c683f",
}

# ✅ 실제 데이터 API Base URL (문서 URL 아님!)
BASE = "https://api.odcloud.kr/api/15101985/v1"

def fetch_od(date_key: str, per_page: int = 1000, max_pages: int | None = None) -> pd.DataFrame:
    """
    서울교통공사_역별 일별 시간대별 노인 승하차인원 데이터 수집
    - date_key: 위 UDDI_MAP의 키 중 하나 ('20211231' 등)
    """
    if date_key not in UDDI_MAP:
        raise ValueError(f"date_key는 {list(UDDI_MAP.keys())} 중 하나여야 합니다.")

    resource = UDDI_MAP[date_key]            # 예: 'uddi:560f9...'
    url = f"{BASE}/{resource}"               # 예: https://api.odcloud.kr/api/15101985/v1/uddi:560f9...

    page = 1
    all_rows = []

    while True:
        params = {
            "serviceKey": SERVICE_KEY,
            "page": page,
            "perPage": per_page,
            # "returnType": "JSON",  # 기본이 JSON
            # 조건 예시) "cond[역명]": "서울역"
        }

        resp = requests.get(url, params=params, timeout=30)

        # 방어적 체크: 200이 아니면 내용 출력
        if resp.status_code != 200:
            raise RuntimeError(f"[HTTP {resp.status_code}] {resp.text[:500]}")

        # JSON 파싱
        try:
            payload = resp.json()
        except Exception:
            raise RuntimeError("JSON 파싱 실패:\n" + resp.text[:500])

        data = payload.get("data", [])
        current = payload.get("currentCount", 0)

        if not data or current == 0:  # 더 이상 데이터 없음
            break

        all_rows.extend(data)

        if max_pages is not None and page >= max_pages:
            break

        page += 1

    return pd.DataFrame(all_rows)


if __name__ == "__main__":
    want = "20231231"  # 가져올 스냅샷 선택
    df = fetch_od(want, per_page=1000, max_pages=None)

    print("rows:", len(df))
    print(df.head(5))

    out_path = f"/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/노인_지하철_{want}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Saved: {out_path}")
