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
    if ml_value <= 0: return "0 mL"
    if ml_value < 1.0:
        return f"{ml_value * 1000:.2f} μL"
    else:
        return f"{ml_value:.4f} mL"

# --- 2. 頁面配置與手機樣式 ---
st.set_page_config(page_title="專業細胞助手", page_icon="🔬")

st.markdown("""
    <style>
    div.row-widget.stRadio > div{ flex-direction: column; }
    label[data-baseweb="radio"] {
        background-color: #f0f2f6;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        border: 1px solid #d1d5db;
    }
    div[aria-checked="true"] { background-color: #e1f5fe !important; border: 2px solid #03a9f4 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔬 細胞繼代助手")

# --- 3. 第一步：原始數據 (側邊欄) ---
with st.sidebar:
    st.header("📊 原始計數")
    total_count = st.number_input("細胞總和 (Counts)", min_value=0, value=400)
    squares = st.number_input("方格數 (n)", min_value=1, value=4)
    dilution = st.number_input("稀釋倍數 (TB)", min_value=1, value=2)
    st.markdown("---")
    st.subheader("🧪 體積設定 (mL)")
    counting_vol = st.number_input("計數時總體積", min_value=0.01, value=1.0)
    current_vol = st.number_input("目前操作總體積", min_value=0.01, value=1.0)

# 核心計算
conc_at_counting = (total_count / squares) * dilution * 10000
absolute_total_cells = conc_at_counting * counting_vol
actual_current_conc = absolute_total_cells / current_vol

# 顯示當前狀態
st.subheader("📍 當前細胞狀態")
col_a, col_b = st.columns(2)
with col_a:
    st.metric("當前濃度 (cells/mL)", format_lab_num(actual_current_conc))
with col_b:
    st.metric("原液細胞總數 (cells)", format_lab_num(absolute_total_cells))

st.markdown("---")

# --- 4. 第二步：模式選擇 ---
st.header("🧪 第二步：選擇計算模式")

mode = st.radio(
    "請直接點選需求：",
    ["🎯 稀釋至目標濃度", "🔢 獲取特定細胞數", "🧫 繼代至特定容器"],
    index=0
)

final_take_vol = 0.0
final_total_vol = 0.0

if mode == "🎯 稀釋至目標濃度":
    c1 = st.number_input("目標濃度 (cells/mL)", value=100000, step=10000)
    v1 = st.number_input("目標最終體積 (mL)", value=10.0, step=1.0)
    if actual_current_conc > 0:
        final_take_vol = (c1 * v1) / actual_current_conc
        final_total_vol = v1

elif mode == "🔢 獲取特定細胞數":
    n2 = st.number_input("目標細胞總數", value=3000, step=1000)
    v2 = st.number_input("最終稀釋總量 (mL) [不補液填0]", value=0.0, format="%.4f")
    if actual_current_conc > 0:
        final_take_vol = n2 / actual_current_conc
        final_total_vol = v2

elif mode == "🧫 繼代至特定容器":
    DISH_DATA = {"10cm": 10.0, "6cm": 3.0, "96-well": 0.1, "24-well": 0.5, "12-well": 1.0, "6-well": 2.0}
    v_type = st.radio("選擇容器：", list(DISH_DATA.keys()), horizontal=True)
    n3 = st.number_input("單孔目標細胞數", value=200000, step=10000)
    c3 = st.number_input("孔數 / 盤數", min_value=1, value=1)
    if actual_current_conc > 0:
        final_take_vol = (n3 * c3) / actual_current_conc
        final_total_vol = DISH_DATA[v_type] * c3

# --- 5. 第三步：計算結果 ---
st.markdown("---")
st.header("📝 第三步：計算結果")

if actual_current_conc > 0:
    st.success(f"💉 **吸取細胞原液**：\n## {smart_format_vol(final_take_vol)}")
    
    if final_total_vol > 0:
        add_media = final_total_vol - final_take_vol
        if add_media >= 0:
            st.info(f"🧪 **補足培養基量**：\n## {smart_format_vol(add_media)}")
        else:
            st.error("⚠️ 警告：所需量已超過目標總體積！")

    # 預稀釋建議 (自填倍數)
    if 0 < final_take_vol < 0.005:
        st.markdown("---")
        with st.expander("🔍 體積太小？開啟手動預稀釋計算", expanded=True):
            st.warning("取樣量 < 5μL 誤差較大，建議先稀釋再取。")
            custom_df = st.number_input("請輸入預稀釋倍數 (例如 10 或 100)", min_value=1.0, value=10.0, step=1.0)
            
            pre_dil_take = 1.0 / custom_df
            st.write(f"**Step 1:** 取 {smart_format_vol(pre_dil_take)} 原液 + {smart_format_vol(1.0 - pre_dil_take)} 培養基 (混勻)")
            st.subheader(f"**Step 2:** 改從稀釋液吸取 {smart_format_vol(final_take_vol * custom_df)}")
else:
    st.warning("請先於左側輸入計數值。")
