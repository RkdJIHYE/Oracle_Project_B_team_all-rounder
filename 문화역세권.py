import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib import font_manager
import platform

def setup_korean_font():
    """
    한글 폰트 설정
    """
    system = platform.system()
    
    try:
        if system == 'Windows':
            font_candidates = ['Malgun Gothic', 'NanumGothic', 'NanumBarunGothic']
        elif system == 'Darwin':  # macOS
            font_candidates = ['AppleGothic', 'Arial Unicode MS']
        else:  # Linux
            font_candidates = ['NanumGothic', 'NanumBarunGothic', 'DejaVu Sans']
        
        available_fonts = [f.name for f in font_manager.fontManager.ttflist]
        
        korean_font = None
        for font in font_candidates:
            if font in available_fonts:
                korean_font = font
                break
        
        if korean_font:
            plt.rcParams['font.family'] = korean_font
            print(f"✅ 한글 폰트 설정: {korean_font}")
        else:
            plt.rcParams['font.family'] = 'DejaVu Sans'
            print("⚠️ 한글 폰트를 찾을 수 없습니다.")
    
    except Exception as e:
        plt.rcParams['font.family'] = 'DejaVu Sans'
        print(f"⚠️ 폰트 설정 오류: {e}")
    
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['figure.figsize'] = (12, 8)

def load_and_analyze_data(file_path):
    """
    CSV 파일 로드 및 기본 분석
    """
    try:
        # 다양한 인코딩으로 시도
        encodings = ['utf-8', 'utf-8-sig', 'euc-kr', 'cp949']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"✅ 파일 로드 성공 (인코딩: {encoding})")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise Exception("모든 인코딩 시도 실패")
        
        print(f"📊 데이터 크기: {len(df)}행 × {len(df.columns)}열")
        print(f"📋 컬럼 목록: {list(df.columns)}")
        
        # 연도 컬럼 확인 및 정리
        if '연도' in df.columns:
            year_col = '연도'
        elif 'BASE_DE' in df.columns:
            year_col = 'BASE_DE'
        else:
            print("❌ 연도 컬럼을 찾을 수 없습니다.")
            return None
        
        print(f"📅 연도 범위: {df[year_col].min()} ~ {df[year_col].max()}")
        print(f"📈 연도별 데이터 수:")
        year_counts = df[year_col].value_counts().sort_index()
        for year, count in year_counts.items():
            print(f"   {year}: {count}행")
        
        return df, year_col
        
    except Exception as e:
        print(f"❌ 파일 로드 실패: {e}")
        return None, None

def extract_facility_data(df, year_col):
    """
    CL_NM에서 문화시설 유형 추출
    """
    print("\n🏛️ 문화시설 유형 분석")
    print("=" * 50)
    
    # CL_NM 컬럼 확인
    if 'CL_NM' not in df.columns:
        print("❌ CL_NM 컬럼을 찾을 수 없습니다.")
        return None
    
    # 고유한 CL_NM 값들 확인
    unique_cl_nm = df['CL_NM'].unique()
    print(f"📝 고유한 CL_NM 값 개수: {len(unique_cl_nm)}")
    print("👀 CL_NM 샘플:")
    for i, cl_nm in enumerate(unique_cl_nm[:10]):
        print(f"   {i+1}. {cl_nm}")
    
    # 문화시설 키워드로 분류
    facility_keywords = {
        '전시회': ['전시', '갤러리', '미술관', 'gallery', '전시회', '전시관'],
        '도서관': ['도서관', '도서', 'library', '문고', '서재'],
        '공연장': ['공연', '극장', '콘서트', '무대', '연극', '음악', 'theater', '공연장'],
        '박물관': ['박물관', 'museum', '기념관', '역사관', '문화관']
    }
    
    # 각 행에 문화시설 유형 할당
    def classify_facility(cl_nm):
        if pd.isna(cl_nm):
            return '기타'
        
        cl_nm_lower = str(cl_nm).lower()
        
        for facility_type, keywords in facility_keywords.items():
            for keyword in keywords:
                if keyword in cl_nm_lower:
                    return facility_type
        
        return '기타'
    
    df['문화시설유형'] = df['CL_NM'].apply(classify_facility)
    
    # 시설별 분포 확인
    facility_counts = df['문화시설유형'].value_counts()
    print(f"\n📊 문화시설 유형별 분포:")
    for facility, count in facility_counts.items():
        print(f"   {facility}: {count}개 ({count/len(df)*100:.1f}%)")
    
    # 목표 시설만 필터링
    target_facilities = ['전시회', '도서관', '공연장', '박물관']
    filtered_df = df[df['문화시설유형'].isin(target_facilities)].copy()
    
    print(f"\n🎯 분석 대상 시설 데이터: {len(filtered_df)}행")
    
    if len(filtered_df) == 0:
        print("❌ 분석 대상 시설 데이터가 없습니다.")
        print("💡 CL_NM에서 시설명을 직접 확인해보세요:")
        print(df['CL_NM'].value_counts().head(20))
        return None
    
    return filtered_df

def calculate_yearly_averages(df, year_col):
    """
    연도별, 시설별 60대, 70대 문화지수 평균 계산
    """
    print("\n📊 연도별 평균 문화지수 계산")
    print("=" * 50)
    
    # 60대, 70대 문화지수 컬럼 확인
    age_columns = ['N60S_CLTUR_IDEX_VALUE', 'N70S_CLTUR_IDEX_VALUE']
    
    for col in age_columns:
        if col not in df.columns:
            print(f"❌ {col} 컬럼을 찾을 수 없습니다.")
            return None
    
    # 연도별, 시설별 그룹화하여 평균 계산
    yearly_averages = df.groupby([year_col, '문화시설유형'])[age_columns].mean().reset_index()
    
    print(f"✅ 그룹별 평균 계산 완료: {len(yearly_averages)}개 그룹")
    
    # 피벗 테이블로 변환 (시각화를 위해)
    pivot_60s = yearly_averages.pivot(index=year_col, columns='문화시설유형', values='N60S_CLTUR_IDEX_VALUE')
    pivot_70s = yearly_averages.pivot(index=year_col, columns='문화시설유형', values='N70S_CLTUR_IDEX_VALUE')
    
    print(f"\n📈 60대 문화지수 연도별 평균:")
    print(pivot_60s.round(2))
    
    print(f"\n📈 70대 문화지수 연도별 평균:")
    print(pivot_70s.round(2))
    
    return yearly_averages, pivot_60s, pivot_70s

def create_line_charts(yearly_averages, pivot_60s, pivot_70s):
    """
    선 그래프 생성
    """
    print("\n📊 선 그래프 생성 중...")
    
    # 컬러 팔레트 설정
    colors = {
        '전시회': '#FF6B6B',
        '도서관': '#4ECDC4', 
        '공연장': '#45B7D1',
        '박물관': '#96CEB4'
    }
    
    # 2x2 서브플롯 구성
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('문화시설별 고령층(60대, 70대) 문화지수 연도별 변화', fontsize=16, fontweight='bold')
    
    # 1. 60대 문화지수 트렌드
    ax1 = axes[0, 0]
    for facility in pivot_60s.columns:
        if facility in colors:
            years = pivot_60s.index
            values = pivot_60s[facility]
            # NaN 값 제거
            mask = ~pd.isna(values)
            if mask.sum() > 0:
                ax1.plot(years[mask], values[mask], 
                        marker='o', linewidth=2.5, markersize=8,
                        color=colors[facility], label=facility,
                        markerfacecolor='white', markeredgewidth=2,
                        markeredgecolor=colors[facility])
    
    ax1.set_title('60대 문화지수 연도별 변화', fontweight='bold', fontsize=12)
    ax1.set_xlabel('연도', fontsize=11)
    ax1.set_ylabel('문화지수', fontsize=11)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)
    
    # 2. 70대 문화지수 트렌드
    ax2 = axes[0, 1]
    for facility in pivot_70s.columns:
        if facility in colors:
            years = pivot_70s.index
            values = pivot_70s[facility]
            mask = ~pd.isna(values)
            if mask.sum() > 0:
                ax2.plot(years[mask], values[mask], 
                        marker='s', linewidth=2.5, markersize=8,
                        color=colors[facility], label=facility,
                        markerfacecolor='white', markeredgewidth=2,
                        markeredgecolor=colors[facility])
    
    ax2.set_title('70대 문화지수 연도별 변화', fontweight='bold', fontsize=12)
    ax2.set_xlabel('연도', fontsize=11)
    ax2.set_ylabel('문화지수', fontsize=11)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)
    
    # 3. 시설별 60대 vs 70대 비교
    ax3 = axes[1, 0]
    facilities = list(colors.keys())
    x_pos = np.arange(len(facilities))
    width = 0.35
    
    # 각 시설의 전체 기간 평균 계산
    avg_60s = [pivot_60s[facility].mean() for facility in facilities if facility in pivot_60s.columns]
    avg_70s = [pivot_70s[facility].mean() for facility in facilities if facility in pivot_70s.columns]
    
    # 데이터가 있는 시설만 표시
    valid_facilities = []
    valid_60s = []
    valid_70s = []
    
    for i, facility in enumerate(facilities):
        if facility in pivot_60s.columns and facility in pivot_70s.columns:
            avg_60 = pivot_60s[facility].mean()
            avg_70 = pivot_70s[facility].mean()
            if not (pd.isna(avg_60) or pd.isna(avg_70)):
                valid_facilities.append(facility)
                valid_60s.append(avg_60)
                valid_70s.append(avg_70)
    
    if valid_facilities:
        x_pos = np.arange(len(valid_facilities))
        bars1 = ax3.bar(x_pos - width/2, valid_60s, width, label='60대', alpha=0.8, color='skyblue')
        bars2 = ax3.bar(x_pos + width/2, valid_70s, width, label='70대', alpha=0.8, color='lightcoral')
        
        ax3.set_title('시설별 연령대 평균 문화지수 비교', fontweight='bold', fontsize=12)
        ax3.set_xlabel('문화시설', fontsize=11)
        ax3.set_ylabel('평균 문화지수', fontsize=11)
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(valid_facilities)
        ax3.legend(fontsize=10)
        ax3.grid(axis='y', alpha=0.3)
        
        # 막대 위에 값 표시
        for bar, value in zip(bars1, valid_60s):
            ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                    f'{value:.1f}', ha='center', va='bottom', fontsize=9)
        
        for bar, value in zip(bars2, valid_70s):
            ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                    f'{value:.1f}', ha='center', va='bottom', fontsize=9)
    
    # 4. 연도별 전체 평균 트렌드 (60대, 70대)
    ax4 = axes[1, 1]
    
    # 연도별 전체 평균 계산
    yearly_overall_60s = pivot_60s.mean(axis=1)
    yearly_overall_70s = pivot_70s.mean(axis=1)
    
    years = yearly_overall_60s.index
    ax4.plot(years, yearly_overall_60s, marker='o', linewidth=3, markersize=10,
            color='#FF6B6B', label='60대 전체 평균', markerfacecolor='white',
            markeredgewidth=2, markeredgecolor='#FF6B6B')
    ax4.plot(years, yearly_overall_70s, marker='s', linewidth=3, markersize=10,
            color='#4ECDC4', label='70대 전체 평균', markerfacecolor='white',
            markeredgewidth=2, markeredgecolor='#4ECDC4')
    
    ax4.set_title('전체 문화시설 평균 문화지수 연도별 변화', fontweight='bold', fontsize=12)
    ax4.set_xlabel('연도', fontsize=11)
    ax4.set_ylabel('평균 문화지수', fontsize=11)
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(bottom=0)
    
    # 값 표시
    for year, value in yearly_overall_60s.items():
        if not pd.isna(value):
            ax4.annotate(f'{value:.1f}', (year, value), textcoords="offset points",
                        xytext=(0,10), ha='center', fontsize=8, alpha=0.7)
    
    for year, value in yearly_overall_70s.items():
        if not pd.isna(value):
            ax4.annotate(f'{value:.1f}', (year, value), textcoords="offset points",
                        xytext=(0,-15), ha='center', fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.show()

def analyze_trends(yearly_averages, pivot_60s, pivot_70s):
    """
    트렌드 분석 및 인사이트 도출
    """
    print("\n📈 트렌드 분석 및 인사이트")
    print("=" * 60)
    
    # 1. 시설별 증감 분석
    print("🏛️ 시설별 문화지수 증감 분석 (첫해 대비 마지막해):")
    
    for facility in pivot_60s.columns:
        # 60대 분석
        values_60 = pivot_60s[facility].dropna()
        if len(values_60) >= 2:
            first_60 = values_60.iloc[0]
            last_60 = values_60.iloc[-1]
            change_60 = last_60 - first_60
            change_pct_60 = (change_60 / first_60) * 100
            
            # 70대 분석
            values_70 = pivot_70s[facility].dropna()
            if len(values_70) >= 2:
                first_70 = values_70.iloc[0]
                last_70 = values_70.iloc[-1]
                change_70 = last_70 - first_70
                change_pct_70 = (change_70 / first_70) * 100
                
                print(f"\n   📍 {facility}:")
                print(f"      60대: {first_60:.1f} → {last_60:.1f} ({change_60:+.1f}, {change_pct_60:+.1f}%)")
                print(f"      70대: {first_70:.1f} → {last_70:.1f} ({change_70:+.1f}, {change_pct_70:+.1f}%)")
    
    # 2. 연령대 간 차이 분석
    print(f"\n👥 연령대 간 문화지수 차이 분석:")
    
    overall_60s = pivot_60s.mean().mean()
    overall_70s = pivot_70s.mean().mean()
    age_gap = overall_60s - overall_70s
    
    print(f"   전체 평균 - 60대: {overall_60s:.2f}")
    print(f"   전체 평균 - 70대: {overall_70s:.2f}")
    print(f"   연령대 간 차이: {age_gap:+.2f} (60대가 {'높음' if age_gap > 0 else '낮음'})")
    
    # 3. 시설별 선호도 분석
    print(f"\n🏆 연령대별 선호 시설 순위:")
    
    print("   60대 선호도 순위:")
    facility_rank_60s = pivot_60s.mean().sort_values(ascending=False)
    for i, (facility, score) in enumerate(facility_rank_60s.items(), 1):
        if not pd.isna(score):
            print(f"      {i}. {facility}: {score:.2f}")
    
    print("   70대 선호도 순위:")
    facility_rank_70s = pivot_70s.mean().sort_values(ascending=False)
    for i, (facility, score) in enumerate(facility_rank_70s.items(), 1):
        if not pd.isna(score):
            print(f"      {i}. {facility}: {score:.2f}")

def main():
    """
    메인 실행 함수
    """
    print("🎭 서울시 문화시설별 고령층 문화지수 분석")
    print("=" * 70)
    
    # 한글 폰트 설정
    setup_korean_font()
    
    # 파일 경로
    file_path = '/Users/jihye/Documents/하이태커코드정리/연령별문화역세권아웃풋/서울특별시_문화역세권_2019-2024_병합.csv'
    
    # 1. 데이터 로드
    df, year_col = load_and_analyze_data(file_path)
    
    if df is None:
        print("❌ 분석을 진행할 수 없습니다.")
        return
    
    # 2. 문화시설 데이터 추출
    filtered_df = extract_facility_data(df, year_col)
    
    if filtered_df is None:
        print("❌ 문화시설 데이터를 추출할 수 없습니다.")
        return
    
    # 3. 연도별 평균 계산
    result = calculate_yearly_averages(filtered_df, year_col)
    
    if result is None:
        print("❌ 평균 계산을 완료할 수 없습니다.")
        return
    
    yearly_averages, pivot_60s, pivot_70s = result
    
    # 4. 시각화
    create_line_charts(yearly_averages, pivot_60s, pivot_70s)
    
    # 5. 트렌드 분석
    analyze_trends(yearly_averages, pivot_60s, pivot_70s)
    
    print("\n✅ 분석 완료!")
    print("💡 주요 발견사항:")
    print("   - 문화시설별 고령층 이용 패턴 파악")
    print("   - 연도별 문화지수 변화 추이 확인")
    print("   - 60대와 70대 간 선호도 차이 분석")

if __name__ == "__main__":
    main()