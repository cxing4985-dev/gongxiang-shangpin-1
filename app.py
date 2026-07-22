import io
import pandas as pd
import requests
import streamlit as st

# 页面基本配置
st.set_page_config(
    page_title="共享商品极速查询系统", page_icon="📦", layout="wide"
)

# 标题与提示
st.title("📦 团队共享商品极速查询系统")
st.caption(
    "数据实时同步自 WPS 金山在线文档，支持按 SKU、货号、商品名或负责人快速检索"
)

# WPS 金山文档共享链接
WPS_LINK = "https://www.kdocs.cn/l/cgLkQPC7A8Co"


@st.cache_data(ttl=60)
def load_data():
  # 拼接 WPS 导出 Excel 的标准参数
  export_url = f"{WPS_LINK.split('?')[0]}?output=xlsx"

  session = requests.Session()
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": (
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
      ),
  }

  try:
    # 请求文件
    res = session.get(export_url, headers=headers, timeout=15, allow_redirects=True)
    res.raise_for_status()

    # 检查返回的是否为标准 Excel (ZIP 头部标识 PK)
    if not res.content.startswith(b"PK"):
      return (
          None,
          "WPS 拒绝了自动下载，请确认 WPS 文档权限已设置为【所有人可查看】。",
      )

    # 读取 Excel 文件
    excel_file = pd.ExcelFile(io.BytesIO(res.content), engine="openpyxl")

    all_dfs = []
    for sheet_name in excel_file.sheet_names:
      df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
      if not df_sheet.empty:
        df_sheet["来源工作表"] = sheet_name
        all_dfs.append(df_sheet)

    if all_dfs:
      return pd.concat(all_dfs, ignore_index=True), None
    else:
      return None, "表格中没有找到数据。"

  except Exception as e:
    return None, f"加载失败: {str(e)}"


# 加载数据
df, error_msg = load_data()

if error_msg:
  st.error(error_msg)
else:
  search_query = st.text_input(
      "🔍 快速搜索（输入 SKU、货号、商品名称或负责人等）：", ""
  )

  if df is not None:
    if search_query:
      mask = df.astype(str).apply(
          lambda row: row.str.contains(search_query, case=False).any(), axis=1
      )
      filtered_df = df[mask]
      st.success(f"找到 {len(filtered_df)} 条相关数据：")
      st.dataframe(filtered_df, use_container_width=True)
    else:
      st.info(f"当前共有 {len(df)} 条商品数据：")
      st.dataframe(df, use_container_width=True)