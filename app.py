import streamlit as st
import pandas as pd
import requests
import io

# 页面基本配置
st.set_page_config(
    page_title="共享商品极速查询系统",
    page_icon="📦",
    layout="wide"
)

# 标题与提示
st.title("📦 团队共享商品极速查询系统")
st.caption("数据实时同步自 WPS 金山在线文档，支持按 SKU、货号、商品名或负责人快速检索")

# WPS 金山文档共享链接
WPS_LINK = "https://www.kdocs.cn/l/cgLkQPC7A8Co?output=xlsx"

# 自动拼接 WPS 直连导出地址
def get_download_url(url):
    clean_url = url.split('?')[0]
    return f"{clean_url}?output=xlsx"

# 动态加载所有 Sheet 的数据并做清理
@st.cache_data(ttl=60) # 60秒自动更新缓存
def load_data(url):
    download_url = get_download_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(download_url, headers=headers, timeout=15)
        response.raise_for_status()
        excel_data = io.BytesIO(response.content)
        xls = pd.ExcelFile(excel_data)
    except Exception as e:
        try:
            xls = pd.ExcelFile("sku_data.xlsx")
        except Exception:
            return pd.DataFrame(), f"数据加载失败，请检查网络或WPS链接权限。错误信息: {e}"

    all_sheets_data = []

    for sheet_name in xls.sheet_names:
        if "首页" in sheet_name or "要求" in sheet_name:
            continue
        
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
            if df.empty:
                continue
            
            df = df.dropna(how='all')
            df.columns = [str(col).strip() for col in df.columns]
            df['负责人'] = sheet_name
            all_sheets_data.append(df)
        except Exception:
            continue

    if not all_sheets_data:
        return pd.DataFrame(), "未获取到有效的商品数据页。"

    full_df = pd.concat(all_sheets_data, ignore_index=True)
    
    for col in full_df.columns:
        full_df[col] = full_df[col].astype(str).str.strip().replace('nan', '')

    return full_df, None

# 加载数据
with st.spinner("正在同步 WPS 在线最新数据..."):
    df, error = load_data(WPS_LINK)

if error:
    st.error(error)
    st.stop()

# 侧边栏/顶部全局搜索框
st.write("---")
search_term = st.text_input("🔍 请输入跟卖SKU / 货号 / 商品编码 / 备注 / 负责人 进行模糊查询：", "").strip()

# 辅助读取函数，防止找不到列名报错
def get_val(row, key_words, default="—"):
    for kw in key_words:
        for col in row.index:
            if kw.lower() in str(col).lower():
                val = str(row[col]).strip()
                if val and val != "nan" and val != "None":
                    return val
    return default

if search_term:
    mask = df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)
    results = df[mask]
    
    st.success(f"共找到 **{len(results)}** 条匹配结果：")
    
    for idx, row in results.iterrows():
        sku = get_val(row, ["跟卖sku", "sku"])
        huohao = get_val(row, ["货号"])
        shoujia = get_val(row, ["售价"])
        caigoujia = get_val(row, ["采购价", "采购成本"])
        bingonglv = get_val(row, ["边贡率"])
        huodonglv = get_val(row, ["活动率"])
        zhongliang = get_val(row, ["重量"])
        link = get_val(row, ["货源链接", "链接"])
        beizhu = get_val(row, ["备注"])
        fuzeren = row.get("负责人", "未知")
        shangpin = get_val(row, ["商品", "名称"])

        with st.container():
            st.markdown(
                f"""
                <div style="border: 1px solid #e0e0e0; border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: #fafafa;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 20px; font-weight: bold; color: #2e7d32;">🏷️ 跟卖SKU: {sku}</span>
                        <span style="background-color: #e3f2fd; color: #1565c0; padding: 4px 12px; border-radius: 15px; font-size: 14px; font-weight: bold;">👤 负责人: {fuzeren}</span>
                    </div>
                    <hr style="margin: 10px 0;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 15px;">
                        <div><b>📦 货号：</b> {huohao}</div>
                        <div><b>💰 售价：</b> <span style="color: #d32f2f; font-weight: bold;">{shoujia} 元</span></div>
                        <div><b>🛒 采购价：</b> {caigoujia} 元</div>
                        <div><b>📈 边贡率：</b> {bingonglv}</div>
                        <div><b>🎉 活动率：</b> {huodonglv}</div>
                        <div><b>⚖️ 重量(g)：</b> {zhongliang}</div>
                        <div><b>📝 商品信息：</b> {shangpin}</div>
                    </div>
                    <div style="margin-top: 10px; font-size: 14px; color: #555;">
                        <b>💬 备注：</b> {beizhu}
                    </div>
                </div>
                """,
                unsafe_allow_html=1
            )
            
            if link.startswith("http"):
                st.link_button("🔗 点击直接打开货源链接", link, use_container_width=True)
            elif link != "—":
                st.info(f"货源链接文本: {link}")
                
        st.write("")
else:
    st.info("💡 提示：在上方搜索框输入关键词（如 SKU 数字、货号前缀、或团队成员名字）即可瞬间查询！")
    st.write(f"📊 当前系统已自动汇总 **{len(df)}** 条全组共享商品数据。")