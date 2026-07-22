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

WPS_LINK = "https://www.kdocs.cn/l/cgLkQPC7A8Co"


@st.cache_data(ttl=10)  # 10秒缓存，确保修改快速同步
def load_data():
  clean_link = WPS_LINK.split("?")[0]

  # 尝试多种 WPS 的下载导出直连节点
  urls_to_try = [
      f"{clean_link}/export?type=csv",
      f"{clean_link}?output=xlsx",
      f"https://www.kdocs.cn/api/v3/office/file/{clean_link.split('/')[-1]}/download",
  ]

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Referer": "https://www.kdocs.cn/",
  }

  session = requests.Session()

  for url in urls_to_try:
    try:
      res = session.get(url, headers=headers, timeout=10)
      if res.status_code == 200 and len(res.content) > 1000:
        # 如果返回的是 Excel 二进制 (PK开头)
        if res.content.startswith(b"PK"):
          excel_file = pd.ExcelFile(io.BytesIO(res.content), engine="openpyxl")
          df = pd.read_excel(excel_file, sheet_name=0)
          return df, None

        # 尝试作为 CSV 解析
        try:
          # 检查是不是 HTML 网页乱码
          if b"<html" not in res.content.lower():
            df = pd.read_csv(
                io.BytesIO(res.content),
                encoding="utf-8-sig",
                on_bad_lines="skip",
            )
            # 过滤掉非正常表格行
            if (
                not df.empty
                and "window.__" not in str(df.columns)
                and len(df.columns) > 1
            ):
              return df, None
        except Exception:
          continue
    except Exception:
      continue

  return (
      None,
      (
          "WPS 官方安全防火墙拦截了数据拉取。如果依然报错，建议将表格复制一份到"
          "【飞书多维表格】或【谷歌表格】，接口100%稳定！"
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