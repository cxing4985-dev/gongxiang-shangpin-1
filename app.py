import pandas as pd
import streamlit as st

# 页面基本配置
st.set_page_config(
    page_title="共享商品极速查询系统", page_icon="📦", layout="wide"
)

# 标题与提示
st.title("📦 团队共享商品极速查询系统")
st.caption("实时检索商品库，支持按 SKU、货号、商品名或负责人快速检索")


@st.cache_data(ttl=5)
def load_data():
  try:
    # 读取同级目录下的普通的 Excel 文件
    excel_file = pd.ExcelFile("sku_data.xlsx", engine="openpyxl")
    all_dfs = []
    for sheet_name in excel_file.sheet_names:
      df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
      if not df_sheet.empty:
        df_sheet["来源工作表"] = sheet_name
        all_dfs.append(df_sheet)

    if all_dfs:
      return pd.concat(all_dfs, ignore_index=True), None
    else:
      return None, "表格中没有找到有效数据。"
  except Exception as e:
    return (
        None,
        (
            f"未找到 sku_data.xlsx 文件，请确认是否已将 Excel"
            f" 文件上传到 GitHub 仓库。错误信息: {str(e)}"
        ),
    )


# 加载数据
df, error_msg = load_data()

if error_msg:
  st.error(error_msg)
else:
  # 顶部搜索框
  search_query = st.text_input(
      "🔍 快速搜索（输入 SKU、货号、商品名称或负责人等）：", ""
  )

  if df is not None and not df.empty:
    if search_query:
      # 全局模糊匹配
      mask = df.astype(str).apply(
          lambda row: row.str.contains(search_query, case=False).any(), axis=1
      )
      filtered_df = df[mask]
      st.success(f"找到 {len(filtered_df)} 条相关商品数据：")
      st.dataframe(filtered_df, use_container_width=True)
    else:
      st.info(f"当前共有 {len(df)} 条商品数据：")
      st.dataframe(df, use_container_width=True)