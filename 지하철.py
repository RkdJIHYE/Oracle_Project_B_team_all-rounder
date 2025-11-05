import requests
import pandas as pd

# 1) 본인 서비스키 (이미 인코딩된 키여도 params에 그대로 넣어도 됩니다. 절대 다시 인코딩하지 마세요)
SERVICE_KEY = "Your Service Key"

# 2) Swagger에서 확인한 리소스(uddi) 매핑
UDDI_MAP = {
    "20221231": "uddi:404f57a3-6abf-412a-9b7a-e2b585fef07a",
    "20231231": "uddi:3320d994-ae3c-4ed6-9bdc-8f5d4bd6dfa9",
}

BASE = "https://api.odcloud.kr/api/15113638/v1"

def fetch_od(date_key: str, per_page: int = 1000, max_pages: int | None = None) -> pd.DataFrame:
    """
    서울특별시_지하철 역별 OD 데이터 수집
    - date_key: '20221231' 또는 '20231231'
    - per_page: 페이지당 행 수 (최대치는 API 정책에 따름, 1000 권장)
    - max_pages: 가져올 최대 페이지 수 (None이면 끝까지)
    """
    if date_key not in UDDI_MAP:
        raise ValueError(f"date_key는 {list(UDDI_MAP.keys())} 중 하나여야 합니다.")

    resource = UDDI_MAP[date_key]
    url = f"{BASE}/{resource}"

    page = 1
    all_rows = []

    while True:
        params = {
            "serviceKey": SERVICE_KEY,
            "page": page,
            "perPage": per_page,
            # "returnType": "JSON",  # 기본이 JSON이라 주석
            # 조건이 필요하면 cond[컬럼명] 사용 (예: 기준일자 필터)
            # "cond[기준일자]": "20231231",
        }

        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"[HTTP {resp.status_code}] {resp.text[:500]}")

        try:
            payload = resp.json()
        except Exception:
            raise RuntimeError("JSON 파싱 실패:\n" + resp.text[:500])

        data = payload.get("data", [])
        current = payload.get("currentCount", 0)

        if not data or current == 0:
            break

        all_rows.extend(data)

        # 페이지 제한에 도달했으면 중단
        if max_pages is not None and page >= max_pages:
            break

        # 다음 페이지로
        page += 1

    # DataFrame으로 변환
    df = pd.DataFrame(all_rows)
    return df


if __name__ == "__main__":
    # 예시: 2023-12-31 데이터 전부 가져오기
    df = fetch_od("20221231", per_page=1000, max_pages=None)

    # 미리보기
    print("rows:", len(df))
    print(df.head(5))

    # CSV 저장 (원하는 경로로 변경)
    out_path = "/Users/jihye/Documents/지하철_OD_20221231.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Saved: {out_path}")
