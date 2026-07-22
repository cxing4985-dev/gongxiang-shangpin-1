import io
import re
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

WPS_LINK = "https://www.kdocs.cn/l/cgLkQPC7A8Co"


@st.cache_data(ttl=15)
def load_data():
  session = requests.Session()
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  try:
    # 尝试访问导出地址
    export_url = f"{WPS_LINK.split('?')[0]}/export?type=csv"
    res = session.get(export_url, headers=headers, timeout=15)

    # 如果抓下来的是网页代码（包含 window.__PLUGINCONFIG__），说明被重定向到了 HTML
    if "window.__PLUGINCONFIG__" in res.text or "<html" in res.text.lower():
      # 改用直接抓取纯文本/表格接口的方式
      export_url2 = f"{WPS_LINK.split('?')[0]}?output=xlsx"
      res = session.get(export_url2, headers=headers, timeout=15)
      excel_file = pd.ExcelFile(io.BytesIO(res.content), engine="openpyxl")
      df = pd.read_excel(excel_file, sheet_name=0)
    else:
      # 正常读取 CSV
      try:
        df = pd.read_csv(io.BytesIO(res.content), encoding="utf-8-sig")
      except Exception:
        df = pd.read_csv(io.BytesIO(res.content), encoding="gbk")

    # 过滤掉非数据行（比如包含 JavaScript 代码的行）
    if not df.empty:
      first_col_str = df.iloc[:, 0].astype(str)
      df = df[~first_col_str.str.contains("window\.__", na=False)]

    return df, None

  except Exception as e:
    return (
        None,
        (
            "数据解析失败，请检查 WPS 链接或权限。"
            f" 错误信息: {str(e)}"
        ),
    )


# 加载数据
df, error_msg = load_data()

if error_msg:
  st.error(error_msg)
else:
  search_query = st.text_input(
      "🔍 快速搜索（输入 SKU、货号、商品名称或负责人等）：", ""
  )

  if df is not None and not df.empty:
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
  else:
    st.warning("暂未读取到有效商品数据，请检查数据源。")