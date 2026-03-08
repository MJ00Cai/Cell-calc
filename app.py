import streamlit as st
import math

# --- 1. 核心函數 ---
def get_superscript(n):
    superscripts = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
    return "".join(superscripts.get(char, char) for char in str(n))

def format_lab_num(n):
    if n == 0: return "0"
    if n >= 10000:
        exponent = int(math.log10(n))
        base = n / (10**exponent)
        base_str = f"{base:.2f}".rstrip('0').rstrip('.')
        return f"{n:,.0f} ({base_str} × 10{get_superscript(exponent)})"
    return f"{n:,.0f}"

def smart_format_vol(ml_value):
    """智慧單位換算：自動切換 mL/μL 並精簡小數點"""
    if ml_value <= 0: return "0 μL"
    
    # 決定單位與數值
    if ml_value < 1.0:
        val = ml_value * 1000
        unit = "μL"
    else:
        val = ml_value
        unit = "mL"
    
    # 智慧小數點：如果是整數就隱藏小數點，否則最多保留四位並去除結尾 0
    formatted_val = f"{val:.4f}".rstrip('0').rstrip('.')
    return f"{formatted_val} {unit}"

# --- 2. 專業儀器視覺 UI ---
st.set_page_config(page_title="Cell Culture Calculator Pro", page_icon="🔬", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    .main-title { 
        color: #0f172a; 
        font-size: 2.2rem; 
        font-weight: 800; 
        text-align: center;
        padding: 20px 0 10px 0;
    }

    .content-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
    }

    /* 專業結果面板：淺色高對比設計 */
    .res-container {
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: #f8fafc;
        margin-top: 10px;
    }
    .res-title { 
        font-size: 1.1rem !important; 
        font-weight: 800 !important; 
        color: #1e293b !important; 
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }
    .res-value { 
        font-size: 2.2rem !important; 
        font-weight: 800 !important; 
        font-family: 'Consolas', monospace;
    }
    .text-stock { color: #2563eb; } /* 專業藍 */
    .text-media { color: #059669; } /* 專業綠 */
    
    /* Radio 按鈕優化 */
    div.row-widget.stRadio > div { flex-direction: row !important; gap: 12px; }
    label[data-baseweb="radio"] {
        background-color: #ffffff;
        padding: 12px 24px;
        border-radius: 8px;
        border: 2px solid #cbd5e1;
        font-weight: 700;
        color: #475569;
    }
    div[aria-checked="true"] {
        background-color: #1e3a8a !important;
        border-color: #2563eb !important;
        color: #ffffff !important;
    }
    
    .block-container { padding-top: 1.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">Cell Culture Calculator Pro</h1>', unsafe_allow_html=True)

# --- 3. 基礎參數 ---
with st.container():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.subheader("SYSTEM INPUTS | 基礎參數")
    input_mode = st.radio("模式切換：", ["傳統計數模式 (Hemocytometer)", "直接輸入濃度 (Direct Concentration)"], horizontal=True)

    if input_mode == "傳統計數模式 (Hemocytometer)":
        c1, c2, c3 = st.columns(3)
        with c1: total_count = st.number_input("細胞總和 (Count)", min_value=0, value=400)
        with c2: squares = st.number_input("方格數 (n)", min_value=1, value=4)
        with c3: dilution = st.number_input("稀釋倍數 (TB)", min_value=1, value=2)
        v1, v2 = st.columns(2)
        with v1: counting_vol = st.number_input("計數時總體積 (mL)", min_value=0.01, value=1.0)
        with v2: current_vol = st.number_input("目前操作總體積 (mL)", min_value=0.01, value=1.0)
        actual_current_conc = ((total_count / squares) * dilution * 10000 * counting_vol) / current_vol
    else:
        c1, v1 = st.columns(2)
        with c1: actual_current_conc = st.number_input("當前細胞濃度 (cells/mL)", min_value=0, value=1000000, step=10000, format="%d")
        with v1: current_vol = st.number_input("目前操作總體積 (mL)", min_value=0.01, value=1.0)
    
    st.markdown("---")
    col_stat1, col_stat2 = st.columns(2)
    col_stat1.metric("當前濃度 (Conc.)", format_lab_num(actual_current_conc))
    col_stat2.metric("細胞總量 (Total Cells)", format_lab_num(actual_current_conc * current_vol))
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 運算任務 ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("TASK SELECTION | 運算模式")
op_mode = st.radio("選擇計算任務：", ["目標濃度稀釋", "特定細胞取樣", "容器繼代分配"])

final_take_vol = 0.0
final_total_vol = 0.0
DISH_DATA = {"10cm Dish": 10.0, "6cm Dish": 3.0, "96-well": 0.1, "24-well": 0.5, "12-well": 1.0, "6-well": 2.0}

if op_mode == "目標濃度稀釋":
    tc, tv = st.columns(2)
    with tc: t_conc = st.number_input("目標濃度 (cells/mL)", value=100000, step=10000, format="%d")
    with tv: t_vol = st.number_input("目標最終體積 (mL)", value=10.0, step=1.0)
    final_take_vol = (t_conc * t_vol) / actual_current_conc if actual_current_conc > 0 else 0
    final_total_vol = t_vol
elif op_mode == "特定細胞取樣":
    tn, ta = st.columns(2)
    with tn: t_num = st.number_input("目標細胞總數", value=50000, step=5000, format="%d")
    with ta: t_add = st.number_input("最終稀釋總量 (mL)", value=0.0)
    final_take_vol = t_num / actual_current_conc if actual_current_conc > 0 else 0
    final_total_vol = t_add
elif op_mode == "容器繼代分配":
    v_type = st.selectbox("選擇容器類型：", list(DISH_DATA.keys()))
    tn, tc = st.columns(2)
    with tn: v_num = st.number_input("單孔目標細胞數", value=200000, format="%d")
    with tc: v_count = st.number_input("操作總孔數", min_value=1, value=1)
    final_take_vol = (v_num * v_count) / actual_current_conc if actual_current_conc > 0 else 0
    final_total_vol = DISH_DATA[v_type] * v_count

# --- 5. 最終結果看板 (優化版) ---
st.markdown("---")
st.subheader("ANALYTICS | 計算結果")

if actual_current_conc > 0:
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.markdown(f"""
            <div class="res-container">
                <div class="res-title">STOCK VOLUME (吸取原液)</div>
                <div class="res-value text-stock">{smart_format_vol(final_take_vol)}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with res_col2:
        if final_total_vol > 0:
            add_media = final_total_vol - final_take_vol
            if add_media >= 0:
                st.markdown(f"""
                    <div class="res-container">
                        <div class="res-title">MEDIA TO ADD (補足培養基)</div>
                        <div class="res-value text-media">{smart_format_vol(add_media)}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("⚠️ OVER LIMIT")

    # 預稀釋邏輯
    if 0 < final_take_vol < 0.005:
        with st.expander("PRE-DILUTION ADVISORY | 預稀釋建議", expanded=True):
            df = st.number_input("預稀釋倍數 (建議 10 或 100)", min_value=1.0, value=10.0)
            st.code(f"Step 1: Mix {smart_format_vol(1.0/df)} stock + {smart_format_vol(1.0-1.0/df)} media.\nStep 2: Take {smart_format_vol(final_take_vol * df)} from mixture.")
else:
    st.warning("請完成基礎參數輸入。")
