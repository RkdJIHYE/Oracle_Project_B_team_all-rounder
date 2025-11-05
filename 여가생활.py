import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib import font_manager
import platform

def setup_korean_font():
    """
    운영체제별 한글 폰트 설정
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

def load_elderly_data(file_path):
    """
    CSV에서 고령층 데이터만 추출
    """
    try:
        # 다양한 인코딩으로 시도
        encodings = ['utf-8', 'euc-kr', 'cp949', 'utf-8-sig']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"✅ 파일 로드 성공 (인코딩: {encoding})")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise Exception("모든 인코딩으로 파일 로드 실패")
        
        # 컬럼명 정리
        df.columns = df.columns.str.strip()
        
        # 고령층 연령대 필터링
        target_ages = ['65~69세', '70~74세', '75~79세', '80~84세', '85~89세', '90세 이상']
        elderly_data = df[df['특성'].isin(target_ages)].copy()
        
        if elderly_data.empty:
            print("❌ 해당 연령대 데이터가 없습니다.")
            print("📝 사용 가능한 특성들:")
            print(df['특성'].tolist())
            return None
        
        # 연령대 순서대로 정렬
        elderly_data['age_order'] = elderly_data['특성'].map({
            '65~69세': 1, '70~74세': 2, '75~79세': 3, 
            '80~84세': 4, '85~89세': 5, '90세 이상': 6
        })
        elderly_data = elderly_data.sort_values('age_order').reset_index(drop=True)
        
        print(f"✅ 고령층 데이터 추출 완료: {len(elderly_data)}개 연령대")
        print("📊 추출된 연령대:", elderly_data['특성'].tolist())
        
        return elderly_data
        
    except Exception as e:
        print(f"❌ 데이터 로드 오류: {e}")
        return None

def create_sample_data():
    """
    샘플 데이터 생성 (실제 파일이 없을 경우)
    """
    print("📄 샘플 데이터를 생성합니다...")
    
    sample_data = {
        '특성': ['65~69세', '70~74세', '75~79세', '80~84세', '85~89세', '90세 이상'],
        '시간이 없어서': [25.3, 18.9, 12.4, 8.7, 6.2, 4.1],
        '경제적 여유가 없어서': [31.2, 29.8, 27.6, 26.1, 24.8, 23.5],
        '무엇을 해야할지 몰라서': [18.7, 21.3, 24.8, 27.2, 29.6, 31.8],
        '어떻게 해야하는지 몰라서': [15.4, 18.2, 21.7, 24.8, 27.3, 29.9],
        '기관이멀어서': [22.1, 26.7, 30.2, 33.8, 36.5, 38.9],
        '건강이좋지않아서': [28.9, 34.5, 41.2, 48.6, 56.3, 64.7],
        '함께 할 사람이 없어서': [35.6, 38.2, 42.8, 47.5, 52.1, 58.3]
    }
    
    df = pd.DataFrame(sample_data)
    return df

def create_line_chart(data, save_path=None):
    """
    고령층 연령대별 꺾은선 그래프 생성
    """
    # 이유별 컬럼들
    reason_columns = [
        '시간이 없어서',
        '경제적 여유가 없어서', 
        '무엇을 해야할지 몰라서',
        '어떻게 해야하는지 몰라서',
        '기관이멀어서',
        '건강이좋지않아서',
        '함께 할 사람이 없어서'
    ]
    
    # 그래프 설정
    plt.figure(figsize=(14, 10))
    
    # 색상 팔레트 설정
    colors = [
        '#FF6B6B',  # 빨간색 계열 - 시간
        '#4ECDC4',  # 청록색 계열 - 경제적
        '#45B7D1',  # 파란색 계열 - 무엇을
        '#96CEB4',  # 연두색 계열 - 어떻게
        '#FFEAA7',  # 노란색 계열 - 기관
        '#DDA0DD',  # 보라색 계열 - 건강
        '#98D8C8'   # 민트색 계열 - 함께할사람
    ]
    
    # 연령대 라벨
    x_labels = data['특성'].tolist()
    x_positions = range(len(x_labels))
    
    # 각 이유별로 선 그래프 그리기
    for i, reason in enumerate(reason_columns):
        if reason in data.columns:
            values = data[reason].values
            plt.plot(x_positions, values, 
                    marker='o', 
                    linewidth=2.5, 
                    markersize=8,
                    color=colors[i], 
                    label=reason.replace('어서', ''),
                    markerfacecolor='white',
                    markeredgewidth=2,
                    markeredgecolor=colors[i])
    
    # 그래프 스타일링
    plt.title('고령층 연령대별 여가활동 미참여 이유', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('연령대', fontsize=12, fontweight='bold')
    plt.ylabel('응답 비율 (%)', fontsize=12, fontweight='bold')
    
    # x축 설정
    plt.xticks(x_positions, x_labels, fontsize=11)
    plt.xlim(-0.2, len(x_labels)-0.8)
    
    # y축 설정
    plt.ylim(0, max([data[col].max() for col in reason_columns if col in data.columns]) + 5)
    
    # 격자 추가
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # 범례 설정
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
              fontsize=10, frameon=True, fancybox=True, shadow=True)
    
    # 각 데이터 포인트에 값 표시 (선택적)
    for i, reason in enumerate(reason_columns[:3]):  # 상위 3개만 값 표시
        if reason in data.columns:
            values = data[reason].values
            for j, value in enumerate(values):
                plt.annotate(f'{value:.1f}%', 
                           (j, value), 
                           textcoords="offset points", 
                           xytext=(0,10), 
                           ha='center', 
                           fontsize=8, 
                           alpha=0.7,
                           color=colors[i])
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 그래프 저장 (선택적)
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"📁 그래프가 '{save_path}'에 저장되었습니다.")
    
    # 그래프 표시
    plt.show()

def analyze_elderly_trends(data):
    """
    고령층 트렌드 분석
    """
    print("\n" + "="*60)
    print("📊 고령층 연령대별 여가활동 미참여 이유 트렌드 분석")
    print("="*60)
    
    reason_columns = [
        '시간이 없어서',
        '경제적 여유가 없어서', 
        '무엇을 해야할지 몰라서',
        '어떻게 해야하는지 몰라서',
        '기관이멀어서',
        '건강이좋지않아서',
        '함께 할 사람이 없어서'
    ]
    
    print("\n🔍 연령대별 주요 특징:")
    for _, row in data.iterrows():
        age = row['특성']
        reason_values = row[reason_columns]
        top_reason = reason_values.idxmax()
        top_value = reason_values.max()
        print(f"   {age}: {top_reason} ({top_value:.1f}%)")
    
    print("\n📈 연령 증가에 따른 트렌드:")
    first_age_values = data.iloc[0][reason_columns]
    last_age_values = data.iloc[-1][reason_columns]
    
    trends = {}
    for reason in reason_columns:
        change = last_age_values[reason] - first_age_values[reason]
        trends[reason] = change
        trend_direction = "증가" if change > 0 else "감소"
        print(f"   {reason}: {change:+.1f}%p ({trend_direction})")
    
    print("\n🏆 가장 큰 변화를 보인 이유:")
    max_increase = max(trends, key=trends.get)
    max_decrease = min(trends, key=trends.get)
    print(f"   증가: {max_increase} (+{trends[max_increase]:.1f}%p)")
    print(f"   감소: {max_decrease} ({trends[max_decrease]:.1f}%p)")
    
    return trends

def create_detailed_analysis(data):
    """
    상세 분석 그래프 추가 생성
    """
    reason_columns = [
        '시간이 없어서',
        '경제적 여유가 없어서', 
        '무엇을 해야할지 몰라서',
        '어떻게 해야하는지 몰라서',
        '기관이멀어서',
        '건강이좋지않아서',
        '함께 할 사람이 없어서'
    ]
    
    # 2x2 서브플롯 생성
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('고령층 여가활동 미참여 이유 상세 분석', fontsize=16, fontweight='bold')
    
    # 1. 상위 3개 이유 강조 그래프
    ax1 = axes[0, 0]
    avg_values = data[reason_columns].mean().sort_values(ascending=False)
    top_3_reasons = avg_values.head(3).index
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    x_positions = range(len(data))
    
    for i, reason in enumerate(top_3_reasons):
        values = data[reason].values
        ax1.plot(x_positions, values, 
                marker='o', linewidth=3, markersize=10,
                color=colors[i], label=reason.replace('어서', ''))
    
    ax1.set_title('주요 미참여 이유 (상위 3개)', fontweight='bold')
    ax1.set_xlabel('연령대')
    ax1.set_ylabel('응답 비율 (%)')
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels(data['특성'], rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 건강 관련 이유 vs 기타
    ax2 = axes[0, 1]
    health_reason = '건강이좋지않아서'
    social_reason = '함께 할 사람이 없어서'
    
    ax2.plot(x_positions, data[health_reason], 
            marker='s', linewidth=3, markersize=8,
            color='#FF6B6B', label='건강 문제')
    ax2.plot(x_positions, data[social_reason], 
            marker='^', linewidth=3, markersize=8,
            color='#4ECDC4', label='사회적 고립')
    
    ax2.set_title('건강 vs 사회적 요인', fontweight='bold')
    ax2.set_xlabel('연령대')
    ax2.set_ylabel('응답 비율 (%)')
    ax2.set_xticks(x_positions)
    ax2.set_xticklabels(data['특성'], rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 정보 부족 관련 이유들
    ax3 = axes[1, 0]
    info_reasons = ['무엇을 해야할지 몰라서', '어떻게 해야하는지 몰라서']
    colors_info = ['#96CEB4', '#FFEAA7']
    
    for i, reason in enumerate(info_reasons):
        ax3.plot(x_positions, data[reason], 
                marker='d', linewidth=2.5, markersize=8,
                color=colors_info[i], label=reason.replace('어서', ''))
    
    ax3.set_title('정보 부족 관련 요인', fontweight='bold')
    ax3.set_xlabel('연령대')
    ax3.set_ylabel('응답 비율 (%)')
    ax3.set_xticks(x_positions)
    ax3.set_xticklabels(data['특성'], rotation=45)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 모든 이유의 평균 변화율
    ax4 = axes[1, 1]
    
    first_values = data.iloc[0][reason_columns].values
    last_values = data.iloc[-1][reason_columns].values
    change_rates = ((last_values - first_values) / first_values * 100)
    
    colors_bar = plt.cm.RdYlBu_r(np.linspace(0, 1, len(reason_columns)))
    bars = ax4.bar(range(len(reason_columns)), change_rates, color=colors_bar)
    
    ax4.set_title('65~69세 대비 90세 이상 변화율', fontweight='bold')
    ax4.set_xlabel('미참여 이유')
    ax4.set_ylabel('변화율 (%)')
    ax4.set_xticks(range(len(reason_columns)))
    ax4.set_xticklabels([r.replace('어서', '').replace('이', '') for r in reason_columns], 
                       rotation=45, ha='right')
    ax4.grid(axis='y', alpha=0.3)
    ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    
    # 막대 위에 값 표시
    for bar, rate in zip(bars, change_rates):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + (5 if height > 0 else -15),
                f'{rate:.1f}%', ha='center', va='bottom' if height > 0 else 'top',
                fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.show()

def main():
    """
    메인 실행 함수
    """
    print("🚀 고령층 여가활동 미참여 이유 분석 시작")
    print("="*50)
    
    # 한글 폰트 설정
    setup_korean_font()
    
    # 데이터 로드 시도
    file_path = '/Users/jihye/Documents/하이태커코드정리/여가미참여이유/지난1년간여가활동미참여이유.csv'
    data = load_elderly_data(file_path)
    
    # 파일이 없으면 샘플 데이터 사용
    if data is None:
        data = create_sample_data()
    
    if data is not None:
        print("\n📊 데이터 확인:")
        print(data)
        
        # 메인 꺾은선 그래프 생성
        print("\n📈 꺾은선 그래프 생성 중...")
        create_line_chart(data, save_path='elderly_leisure_analysis.png')
        
        # 트렌드 분석
        analyze_elderly_trends(data)
        
        # 상세 분석 그래프
        print("\n📊 상세 분석 그래프 생성 중...")
        create_detailed_analysis(data)
        
        print("\n✅ 분석 완료!")
        print("💡 주요 발견사항:")
        print("   - 연령이 증가할수록 건강 문제가 주요 요인으로 부상")
        print("   - 사회적 고립 문제도 연령과 함께 증가")
        print("   - 시간 부족은 연령이 높아질수록 감소")
        print("   - 정보 부족 문제는 연령과 함께 증가 추세")
        
    else:
        print("❌ 분석을 수행할 수 없습니다.")

if __name__ == "__main__":
    main()