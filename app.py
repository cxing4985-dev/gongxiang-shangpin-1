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


@st.cache_data(ttl=15)  # 15秒缓存，保证组员修改后网页快速同步
def load_data():
  # 拼接 WPS 导出 CSV 的直链（CSV 格式不会触发 WPS 的 Excel 防火墙拦截）
  clean_link = WPS_LINK.split("?")[0]
  export_url = f"{clean_link}/export?type=csv"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  try:
    response = requests.get(export_url, headers=headers, timeout=15)
    response.raise_for_status()

    # 尝试自动识别编码读取 CSV 文本流
    try:
      df = pd.read_csv(io.BytesIO(response.content), encoding="utf-8")
    except UnicodeDecodeError:
      df = pd.read_csv(io.BytesIO(response.content), encoding="gbk")

    return df, None
  except Exception as e:
    return (
        None,
        (
            "数据加载失败，请检查网络或 WPS 链接权限。"
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