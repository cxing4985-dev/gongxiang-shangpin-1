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
WPS_LINK = "https://www.kdocs.cn/l/cgLkQPC7A8Co?output=xlsx"


# 动态加载数据并做清理
@st.cache_data(ttl=60)  # 60秒自动更新缓存
def load_data(url):
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  try:
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    # 读取 Excel 文件，明确使用 openpyxl 引擎
    excel_file = pd.ExcelFile(
        io.BytesIO(response.content), engine="openpyxl"
    )

    # 汇总所有 Sheet 表格数据
    all_dfs = []
    for sheet_name in excel_file.sheet_names:
      df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
      if not df_sheet.empty:
        df_sheet["来源工作表"] = sheet_name
        all_dfs.append(df_sheet)

    if all_dfs:
      combined_df = pd.concat(all_dfs, ignore_index=True)
      return combined_df, None
    else:
      return None, "WPS 表格中没有找到数据。"

  except Exception as e:
    return (
        None,
        f"数据加载失败，请检查网络或WPS链接权限。错误信息: {str(e)}",
    )


# 加载数据
df, error_msg = load_data(WPS_LINK)

if error_msg:
  st.error(error_msg)
else:
  # 搜索框
  search_query = st.text_input(
      "🔍 快速搜索（输入 SKU、货号、商品名称或负责人等）：", ""
  )

  if df is not None:
    if search_query:
      # 全局模糊搜索
      mask = df.astype(str).apply(
          lambda row: row.str.contains(search_query, case=False).any(), axis=1
      )
      filtered_df = df[mask]
      st.success(f"找到 {len(filtered_df)} 条相关数据：")
      st.dataframe(filtered_df, use_container_width=True)
    else:
      st.info(f"当前共有 {len(df)} 条商品数据：")
      st.dataframe(df, use_container_width=True)