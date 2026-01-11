import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

# 페이지 설정
st.set_page_config(
    page_title="로로샵 재고 대여 관리",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4f46e5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f9fafb;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #e5e7eb;
    }
    .positive {
        color: #10b981;
        font-weight: bold;
    }
    .negative {
        color: #ef4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('lolo_shop.db', check_same_thread=False)
    c = conn.cursor()
    
    # 거래 내역 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            shop TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL,
            total INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            month TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 상품 정보 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            supply_price INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

# 데이터베이스 연결
@st.cache_resource
def get_connection():
    return init_db()

conn = get_connection()

# 거래 내역 추가
def add_transaction(date, shop, product_name, quantity, unit_price, transaction_type):
    c = conn.cursor()
    total = quantity * unit_price
    month = date.strftime('%Y-%m')
    
    c.execute('''
        INSERT INTO transactions (date, shop, product_name, quantity, unit_price, total, transaction_type, month)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date.strftime('%Y-%m-%d'), shop, product_name, quantity, unit_price, total, transaction_type, month))
    
    conn.commit()
    return True

# 상품 추가/업데이트
def upsert_product(product_name, sku, supply_price):
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO products (product_name, sku, supply_price)
            VALUES (?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                product_name = excluded.product_name,
                supply_price = excluded.supply_price
        ''', (product_name, sku, supply_price))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"오류: {e}")
        return False

# 데이터 조회
def get_transactions(month=None, shop=None, transaction_type=None):
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if month:
        query += " AND month = ?"
        params.append(month)
    if shop:
        query += " AND shop = ?"
        params.append(shop)
    if transaction_type:
        query += " AND transaction_type = ?"
        params.append(transaction_type)
    
    query += " ORDER BY date DESC"
    
    return pd.read_sql_query(query, conn, params=params)

def get_products():
    return pd.read_sql_query("SELECT * FROM products ORDER BY product_name", conn)

def delete_transaction(transaction_id):
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()

def delete_all_products():
    c = conn.cursor()
    c.execute("DELETE FROM products")
    conn.commit()

# CSV 업로드 처리
def process_csv(csv_file):
    try:
        df = pd.read_csv(csv_file)
        
        # 열 이름 찾기
        product_col = None
        sku_col = None
        price_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if '상품명' in col or 'product' in col_lower or 'name' in col_lower:
                product_col = col
            elif 'sku' in col_lower or '코드' in col:
                sku_col = col
            elif '공급가' in col or '가격' in col or 'price' in col_lower or 'supply' in col_lower:
                price_col = col
        
        if not all([product_col, sku_col, price_col]):
            return None, "필수 열(상품명, SKU, 공급가)을 찾을 수 없습니다."
        
        success_count = 0
        error_count = 0
        
        for _, row in df.iterrows():
            product_name = str(row[product_col]).strip()
            sku = str(row[sku_col]).strip()
            price_str = str(row[price_col]).replace(',', '').replace('원', '').strip()
            
            try:
                price = int(float(price_str))
            except:
                error_count += 1
                continue
            
            if product_name and sku and price > 0:
                if upsert_product(product_name, sku, price):
                    success_count += 1
                else:
                    error_count += 1
        
        return success_count, error_count
    except Exception as e:
        return None, str(e)

# 메인 앱
def main():
    # 헤더
    st.markdown('<div class="main-header">🏪 로로샵 재고 대여 관리</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">샵 간 재고 대여 현황과 정산 관리</div>', unsafe_allow_html=True)
    
    # 사이드바 네비게이션
    page = st.sidebar.radio(
        "메뉴",
        ["📊 대시보드", "💱 거래 내역", "📦 상품 관리", "📈 월별 통계"],
        label_visibility="collapsed"
    )
    
    if page == "📊 대시보드":
        show_dashboard()
    elif page == "💱 거래 내역":
        show_transactions()
    elif page == "📦 상품 관리":
        show_products()
    elif page == "📈 월별 통계":
        show_statistics()

# 대시보드
def show_dashboard():
    st.header("📊 대시보드")
    
    # 월 선택
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_month = st.date_input(
            "조회 기간",
            value=date.today(),
            format="YYYY-MM"
        ).strftime('%Y-%m')
    with col2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    # 데이터 조회
    df = get_transactions(month=selected_month)
    
    if df.empty:
        st.info("이번 달 거래 내역이 없습니다.")
        return
    
    # 총 정산 금액 계산
    total_balance = 0
    for _, row in df.iterrows():
        if row['transaction_type'] == 'lend':
            total_balance += row['total']
        else:
            total_balance -= row['total']
    
    # 메트릭 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "총 정산 금액",
            f"₩{total_balance:,}",
            delta="받을 금액" if total_balance > 0 else "줄 금액" if total_balance < 0 else "정산 완료"
        )
    
    with col2:
        lend_total = df[df['transaction_type'] == 'lend']['total'].sum()
        st.metric("빌려준 총액", f"₩{lend_total:,}")
    
    with col3:
        borrow_total = df[df['transaction_type'] == 'borrow']['total'].sum()
        st.metric("빌린 총액", f"₩{borrow_total:,}")
    
    st.divider()
    
    # 샵별 정산 현황
    st.subheader("🏪 샵별 정산 현황")
    
    shop_balances = {}
    for _, row in df.iterrows():
        shop = row['shop']
        if shop not in shop_balances:
            shop_balances[shop] = 0
        
        if row['transaction_type'] == 'lend':
            shop_balances[shop] += row['total']
        else:
            shop_balances[shop] -= row['total']
    
    if shop_balances:
        for shop, balance in sorted(shop_balances.items(), key=lambda x: abs(x[1]), reverse=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**{shop}**")
            with col2:
                color = "positive" if balance > 0 else "negative" if balance < 0 else ""
                st.markdown(f'<span class="{color}">₩{balance:,}</span>', unsafe_allow_html=True)
        
        st.divider()
    
    # 최근 거래 내역
    st.subheader("📝 최근 거래 내역 (10건)")
    
    recent_df = df.head(10).copy()
    recent_df['거래유형'] = recent_df['transaction_type'].map({'lend': '빌려줌 (+)', 'borrow': '빌림 (-)'})
    recent_df['금액'] = recent_df.apply(
        lambda x: f"₩{x['total']:,}" if x['transaction_type'] == 'lend' else f"-₩{x['total']:,}",
        axis=1
    )
    
    display_df = recent_df[['date', 'shop', 'product_name', 'quantity', '거래유형', '금액']]
    display_df.columns = ['날짜', '거래처', '상품명', '수량', '거래유형', '금액']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# 거래 내역 관리
def show_transactions():
    st.header("💱 거래 내역 관리")
    
    # 새 거래 추가
    with st.expander("➕ 새 거래 추가", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tx_date = st.date_input("날짜", value=date.today())
        
        with col2:
            tx_shop = st.selectbox(
                "거래처",
                ["원더조이", "뚜샵", "코스블라", "온리", "여진", "소연"]
            )
        
        with col3:
            tx_type = st.selectbox(
                "거래 유형",
                ["lend", "borrow"],
                format_func=lambda x: "빌려줌 (+)" if x == "lend" else "빌림 (-)"
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            products_df = get_products()
            if not products_df.empty:
                product_options = products_df['product_name'].tolist()
                tx_product = st.selectbox("상품명", [""] + product_options)
                
                if tx_product:
                    selected_product = products_df[products_df['product_name'] == tx_product].iloc[0]
                    default_price = int(selected_product['supply_price'])
                else:
                    default_price = 0
            else:
                tx_product = st.text_input("상품명")
                default_price = 0
        
        with col2:
            tx_quantity = st.number_input("수량", min_value=1, value=1)
        
        with col3:
            tx_price = st.number_input("단가", min_value=0, value=default_price)
        
        if st.button("💾 저장", type="primary", use_container_width=True):
            if tx_product and tx_quantity and tx_price:
                if add_transaction(tx_date, tx_shop, tx_product, tx_quantity, tx_price, tx_type):
                    st.success("✅ 거래가 추가되었습니다!")
                    st.rerun()
            else:
                st.error("모든 필드를 입력해주세요.")
    
    st.divider()
    
    # 거래 내역 조회
    st.subheader("📋 거래 내역 목록")
    
    # 필터
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_month = st.text_input("월 필터 (YYYY-MM)", placeholder="예: 2026-01")
    
    with col2:
        filter_shop = st.selectbox("거래처 필터", ["전체"] + ["원더조이", "뚜샵", "코스블라", "온리", "여진", "소연"])
    
    with col3:
        filter_type = st.selectbox("거래 유형 필터", ["전체", "lend", "borrow"],
                                    format_func=lambda x: x if x == "전체" else "빌려줌 (+)" if x == "lend" else "빌림 (-)")
    
    # 데이터 조회
    df = get_transactions(
        month=filter_month if filter_month else None,
        shop=filter_shop if filter_shop != "전체" else None,
        transaction_type=filter_type if filter_type != "전체" else None
    )
    
    if df.empty:
        st.info("거래 내역이 없습니다.")
    else:
        df_display = df.copy()
        df_display['거래유형'] = df_display['transaction_type'].map({'lend': '빌려줌 (+)', 'borrow': '빌림 (-)'})
        df_display['금액'] = df_display.apply(
            lambda x: f"₩{x['total']:,}" if x['transaction_type'] == 'lend' else f"-₩{x['total']:,}",
            axis=1
        )
        
        display_cols = ['date', 'shop', 'product_name', 'quantity', 'unit_price', '거래유형', '금액', 'id']
        df_show = df_display[display_cols]
        df_show.columns = ['날짜', '거래처', '상품명', '수량', '단가', '거래유형', '금액', 'ID']
        
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        
        # 삭제 기능
        st.write("---")
        delete_id = st.number_input("삭제할 거래 ID", min_value=1, step=1)
        if st.button("🗑️ 선택한 거래 삭제", type="secondary"):
            delete_transaction(delete_id)
            st.success("삭제되었습니다!")
            st.rerun()

# 상품 관리
def show_products():
    st.header("📦 상품 관리")
    
    # CSV 업로드
    with st.expander("📁 CSV 파일로 상품 불러오기", expanded=True):
        st.info("💡 Google Sheets에서 '파일 → 다운로드 → 쉼표로 구분된 값(.csv)' 선택 후 업로드하세요.")
        
        csv_file = st.file_uploader("CSV 파일 선택", type=['csv'])
        
        if csv_file is not None:
            if st.button("📤 CSV 업로드", type="primary", use_container_width=True):
                with st.spinner("처리 중..."):
                    success, error = process_csv(csv_file)
                    
                    if success is not None:
                        st.success(f"✅ {success}개 상품이 저장되었습니다!" + 
                                  (f" ({error}개 실패)" if error > 0 else ""))
                        st.rerun()
                    else:
                        st.error(f"❌ 오류: {error}")
    
    st.divider()
    
    # 수동 추가
    with st.expander("➕ 새 상품 추가 (수동)"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            prod_name = st.text_input("상품명")
        with col2:
            prod_sku = st.text_input("SKU")
        with col3:
            prod_price = st.number_input("공급가", min_value=0, step=100)
        
        if st.button("💾 상품 저장", use_container_width=True):
            if prod_name and prod_sku and prod_price > 0:
                if upsert_product(prod_name, prod_sku, prod_price):
                    st.success("✅ 상품이 저장되었습니다!")
                    st.rerun()
            else:
                st.error("모든 필드를 입력해주세요.")
    
    st.divider()
    
    # 상품 목록
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📋 상품 목록")
    with col2:
        if st.button("🗑️ 전체 삭제", type="secondary", use_container_width=True):
            if st.session_state.get('confirm_delete'):
                delete_all_products()
                st.success("모든 상품이 삭제되었습니다!")
                st.session_state['confirm_delete'] = False
                st.rerun()
            else:
                st.session_state['confirm_delete'] = True
                st.warning("다시 한 번 클릭하면 삭제됩니다.")
    
    products_df = get_products()
    
    if products_df.empty:
        st.info("등록된 상품이 없습니다.")
    else:
        display_df = products_df[['product_name', 'sku', 'supply_price']]
        display_df.columns = ['상품명', 'SKU', '공급가']
        display_df['공급가'] = display_df['공급가'].apply(lambda x: f"₩{x:,}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.caption(f"총 {len(products_df)}개 상품")

# 월별 통계
def show_statistics():
    st.header("📈 월별 통계")
    
    # 월 선택
    selected_month = st.date_input(
        "조회 월",
        value=date.today(),
        format="YYYY-MM"
    ).strftime('%Y-%m')
    
    df = get_transactions(month=selected_month)
    
    if df.empty:
        st.info("선택한 월의 거래 내역이 없습니다.")
        return
    
    # 통계 계산
    lend_df = df[df['transaction_type'] == 'lend']
    borrow_df = df[df['transaction_type'] == 'borrow']
    
    lend_total = lend_df['total'].sum()
    borrow_total = borrow_df['total'].sum()
    net_balance = lend_total - borrow_total
    
    lend_count = len(lend_df)
    borrow_count = len(borrow_df)
    
    # 메트릭
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("빌려준 총액", f"₩{lend_total:,}", f"{lend_count}건")
    with col2:
        st.metric("빌린 총액", f"₩{borrow_total:,}", f"{borrow_count}건")
    with col3:
        st.metric("순 정산 금액", f"₩{net_balance:,}", 
                 "받을 금액" if net_balance > 0 else "줄 금액")
    with col4:
        st.metric("총 거래 건수", f"{lend_count + borrow_count}건")
    
    st.divider()
    
    # 샵별 누적 통계
    st.subheader("🏪 샵별 누적 통계 (전체 기간)")
    
    all_df = get_transactions()
    
    if not all_df.empty:
        shop_stats = {}
        for _, row in all_df.iterrows():
            shop = row['shop']
            if shop not in shop_stats:
                shop_stats[shop] = {'lend': 0, 'borrow': 0, 'net': 0}
            
            if row['transaction_type'] == 'lend':
                shop_stats[shop]['lend'] += row['total']
                shop_stats[shop]['net'] += row['total']
            else:
                shop_stats[shop]['borrow'] += row['total']
                shop_stats[shop]['net'] -= row['total']
        
        # 차트 데이터 준비
        chart_data = []
        for shop, stats in shop_stats.items():
            chart_data.append({
                '거래처': shop,
                '빌려준 금액': stats['lend'],
                '빌린 금액': stats['borrow'],
                '순 정산': stats['net']
            })
        
        chart_df = pd.DataFrame(chart_data)
        
        # 막대 그래프
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='빌려준 금액',
            x=chart_df['거래처'],
            y=chart_df['빌려준 금액'],
            marker_color='#10b981'
        ))
        
        fig.add_trace(go.Bar(
            name='빌린 금액',
            x=chart_df['거래처'],
            y=chart_df['빌린 금액'],
            marker_color='#ef4444'
        ))
        
        fig.update_layout(
            barmode='group',
            title='샵별 거래 금액 비교',
            xaxis_title='거래처',
            yaxis_title='금액 (원)',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 표 형식
        st.dataframe(chart_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
