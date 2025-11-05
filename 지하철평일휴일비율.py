import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import platform

# ==============================
# 0) 한글 폰트 설정
# ==============================
if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    # 리눅스/서버 등 한글 폰트 미설치 환경 대비
    plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

# ==============================
# 1) 데이터 로드
# ==============================
file_path = "/Users/jihye/Documents/하이태커코드정리/서울지하철_노인파일/출력/시간대별_월평균_평일휴일_역별_승하차_통합(반올림_행합계포함).csv"
try:
    df = pd.read_csv(file_path, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="cp949")

# 분석 기간(2021-07 ~ 2023-12)만 사용하고 싶다면 주석 해제
# df = df[(df["월"] >= "2021-07") & (df["월"] <= "2023-12")].copy()

# ==============================
# 2) 월별 평일/휴일 비율 산출용 전처리
#    - 이 파일의 시간대 컬럼들은 이미 "월평균 하루치" (역·승/하차별) 값입니다.
#    - 따라서 월별 '서울시 하루'를 만들려면 역/승하차별 일평균을 합산하면 됩니다.
# ==============================
# 시간대 컬럼 목록
time_cols = [c for c in df.columns if "시간대" in c]

# 각 행(월·평일/휴일·역·승/하차)의 하루 총합
df["합계"] = df[time_cols].sum(axis=1)

# ==============================
# 3) monthly_ratio 정의
#    monthly_sum    : 월 x 평일/휴일의 '하루 합계' (역·승/하차를 모두 합한 값)
#    monthly_ratio  : 각 월에서 평일/휴일이 차지하는 비율(%), 월별로 100% 정규화
# ==============================
monthly_sum = df.groupby(["월", "평일휴일"])["합계"].sum().unstack(fill_value=0)
monthly_ratio = monthly_sum.div(monthly_sum.sum(axis=1), axis=0) * 100  # <= ★ 여기서 정의됨

# (선택) CSV로 저장
# monthly_ratio.to_csv("월별_평일휴일_비율(100퍼센트_정규화).csv", encoding="utf-8-sig")

# ==============================
# 4) 시각화: 월별 평일/휴일 비율 (누적 막대, 100% 기준)
#    - 평일: 빨간색, 휴일: 파란색
#    - 막대 내부에 비율 라벨 표시
# ==============================
months = monthly_ratio.index.astype(str)

plt.figure(figsize=(14, 6))

# 평일(파랑) 막대
plt.bar(months,
        monthly_ratio["평일"],
        color="blue",
        label="평일")

# 휴일(빨강) 막대 - 평일 위에 누적
plt.bar(months,
        monthly_ratio["휴일"],
        bottom=monthly_ratio["평일"],
        color="red",
        label="휴일")



plt.xticks(rotation=45, ha="right")
plt.ylim(0, 100)
plt.ylabel("비율 (%)")
plt.title("월별 평일/휴일 무임승차인원 이용 비율 (누적 막대, 월별 100% 정규화)")
plt.legend()
plt.tight_layout()
plt.show()
