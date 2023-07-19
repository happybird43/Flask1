from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import mysql.connector
import json
from dash import Dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import random
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
# dash_app = Dash(__name__, server=app, url_base_pathname='/final/')

# 匯入股票產業資料
file_path = os.path.join(os.path.dirname(__file__), "台灣上市股票產業代碼.txt")

with open(file_path, "r") as file:
    js = file.read()
all_stock_id = json.loads(js)
file.close()

# 資料庫連接設定
cnx = None
cnx2 = None
cnx3 = None

# 隨機顏色
def generate_random_colors(num_colors):
    colors = []
    for _ in range(num_colors):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        a = random.uniform(0.3, 1.0)  # 隨機生成透明度值
        rgba_color = f'rgba({r}, {g}, {b}, {a})'
        colors.append(rgba_color)
    return colors

# 連結MYSQL data(股票數據)
def get_database_connection():
    global cnx
    if cnx is None:
        cnx = mysql.connector.connect(
            host="127.0.0.1",  # 資料庫伺服器名稱
            user="root",  # 資料庫使用者名稱
            password="aa80604aa",  # 資料庫密碼
            database="data",  # 資料庫名稱
        )
    return cnx

# 連結MYSQL data2(財報數據)
def get_database_connection2():
    global cnx2
    if cnx2 is None:
        cnx2 = mysql.connector.connect(
            host="127.0.0.1",  # 資料庫伺服器名稱
            user="root",  # 資料庫使用者名稱
            password="aa80604aa",  # 資料庫密碼
            database="data2",  # 資料庫名稱
        )
    return cnx2

# 連結MYSQL data3(beta值)
def get_database_connection3():
    global cnx3
    if cnx3 is None:
        cnx3 = mysql.connector.connect(
            host="127.0.0.1",  # 資料庫伺服器名稱
            user="root",  # 資料庫使用者名稱
            password="aa80604aa",  # 資料庫密碼
            database="data3",  # 資料庫名稱
        )
    return cnx3

# 獲取beta值
def get_stock_beta(stockid):
    query = f'select CAST(`beta` AS DECIMAL(10, 5))as Beta from `{stockid}`'
    cnx3 = get_database_connection3()
    df = pd.read_sql(query, cnx3)
    first_row = df.iloc[0]
    beta_value = first_row["Beta"]
    return beta_value

# 獲取股價
def get_stock_price(stockid):
    query = f"""select CAST(`open` AS DECIMAL(10, 2)) as price from `{stockid}`
        WHERE `date`  = (
            SELECT MAX(`date`)
            FROM `{stockid}`
        )"""
    cnx = get_database_connection()
    df = pd.read_sql(query, cnx)
    first_row = df.iloc[0]
    price_value = first_row["price"]
    return price_value

# 連接股票代碼公司

current_directory = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(current_directory, "股票名稱代碼.csv")
stock_df = pd.read_csv(csv_file_path)

def get_stock_name(stockid):
    matched_stock = stock_df.loc[stock_df['有價證券代號'] == stockid, '有價證券名稱']
    if not matched_stock.empty:
        return matched_stock.values[0]
    else:
        return ''

# 網站開啟
@app.route("/")
def index():
    return render_template("index.html")

# 單筆股票網站
@app.route("/stock/<stock>", methods=["GET", "POST"])
def stock(stock):
    if request.method == "GET":
        # 從表單中獲取股票代碼
        stock_code = stock

        # 執行搜尋資料庫的查詢
        # 股價內容
        query = f"""
                SELECT `{stock_code}`.`date` AS 時間, CAST(`Open` AS DECIMAL(10, 2))as 開盤, CAST(`High` AS DECIMAL(10, 2))as 最高, CAST(`Low` AS DECIMAL(10, 2))as 最低, CAST(`Close` AS DECIMAL(10, 2))as 收盤, CAST(`K9` AS DECIMAL(10, 2))as 日K值, CAST(`D9` AS DECIMAL(10, 2))as 日D值
                FROM `{stock_code}`
                order by `date` DESC
                """

        query2 = f"""
                SELECT  `{stock_code}`.`Unnamed: 0` AS 季別,
                    CAST(`流動比` AS DECIMAL(10, 2))as 流動比率,
                    CAST(`負債總額 (%)` AS DECIMAL(10, 2))as 負債比率,
                    CAST(`應收帳款週轉率 (次/年)` AS DECIMAL(10, 2))as 應收帳款週轉率,
                    CAST(`總資產週轉率 (次/年)` AS DECIMAL(10, 2))as 總資產周轉率,
                    CAST(`資產報酬率  (當季)` AS DECIMAL(10, 2))as 總資產報酬率,
                    CAST(`股東權益報酬率  (當季)` AS DECIMAL(10, 2))as 權益報酬率,
                    CAST(`每股稅後盈餘 (元)` AS DECIMAL(10, 2))as 每股稅後盈餘,
                    CAST(`利息保障倍數` AS DECIMAL(10, 2))as 利息保障倍數,
                    CAST(`存貨週轉率 (次/年)` AS DECIMAL(10, 2))as 存貨週轉率

                FROM `{stock_code}`
                """
        stID=stock_code
        stName=get_stock_name(int(stock_code))
        cnx = get_database_connection()
        cnx2 = get_database_connection2()
        df = pd.read_sql(query, cnx)
        df2 = pd.read_sql(query2, cnx2)
        table_html = df.to_html(index=False)
        table2_html = df2.to_html(index=False)
        
        # for i in all_stock_id.keys():
        #     for j in all_stock_id[i]:
        #         if stock_code==j:
        #             file_path = r"D:\\stock\\個股圖表\\" + j + ".html"
                    
        #             with open(file_path, 'r', encoding='utf-8') as file:
        #                 html_content = file.read()
                       



        return render_template(
            "stock.html", stock_code=stock_code, table_html=table_html, table2_html=table2_html,stID=stID,stName=stName
        )
    else:
        return render_template("stock.html")

# 股票搜尋
@app.route("/search", methods=["GET", "POST"])
def result():
    if request.method == "POST":
        # 從表單中獲取股票代碼
        stock_code = request.form["stock"]

        # 執行搜尋資料庫的查詢
        # 股價內容
        try:
            query = f"""
                SELECT `{stock_code}`.`date` as 時間, CAST(`Open` AS DECIMAL(10, 2))as 開盤, CAST(`High` AS DECIMAL(10, 2))as 最高, CAST(`Low` AS DECIMAL(10, 2))as 最低, CAST(`Close` AS DECIMAL(10, 2))as 收盤, CAST(`K9` AS DECIMAL(10, 2))as 日K值, CAST(`D9` AS DECIMAL(10, 2))as 日D值
                FROM `{stock_code}`
                order by `date` DESC
                """
            # 財報內容
            query2 = f"""
                SELECT  `{stock_code}`.`Unnamed: 0` AS 季別,
                    CAST(`流動比` AS DECIMAL(10, 2))as 流動比率,
                    CAST(`負債總額 (%)` AS DECIMAL(10, 2))as 負債比率,
                    CAST(`應收帳款週轉率 (次/年)` AS DECIMAL(10, 2))as 應收帳款週轉率,
                    CAST(`總資產週轉率 (次/年)` AS DECIMAL(10, 2))as 總資產周轉率,
                    CAST(`資產報酬率  (當季)` AS DECIMAL(10, 2))as 總資產報酬率,
                    CAST(`股東權益報酬率  (當季)` AS DECIMAL(10, 2))as 權益報酬率,
                    CAST(`每股稅後盈餘 (元)` AS DECIMAL(10, 2))as 每股稅後盈餘,
                    CAST(`利息保障倍數` AS DECIMAL(10, 2))as 利息保障倍數,
                    CAST(`存貨週轉率 (次/年)` AS DECIMAL(10, 2))as 存貨週轉率

                FROM `{stock_code}`
                """

            stID=stock_code
            stName=get_stock_name(int(stock_code))
            cnx = get_database_connection()
            cnx2 = get_database_connection2()
            df = pd.read_sql(query, cnx)
            df2 = pd.read_sql(query2, cnx2)
            table_html = df.to_html(index=False)
            table2_html = df2.to_html(index=False)

            # for i in all_stock_id.keys():
            #     for j in all_stock_id[i]:
            #         if stock_code==j:
            #             file_path = r"D:\\stock\\個股圖表\\" + j + ".html"
                        
            #             with open(file_path, 'r', encoding='utf-8') as file:
            #                 html_content = file.read()
              

            # 將查詢結果傳遞給 HTML 模板顯示
            return render_template(
            "stock.html", stock_code=stock_code, table_html=table_html, table2_html=table2_html,stID=stID,stName=stName
        )
        except Exception as e:
            print(e)
            error_message = f"未有此股票代碼"
            return render_template("index.html", error_message=error_message)
    else:
        return render_template("index.html")

# STEP1產業篩選
@app.route("/", methods=["GET", "POST"])
def receive_data():
    global selected_types
    if request.method == "POST":
        selected_types = request.form.getlist("types[]")
        table_html = ""
        rank_value = request.form['rank']
        cnx = get_database_connection()
        cnx2 = get_database_connection2()
        df_combined = pd.DataFrame()  # 用於存儲所有資料的合併資料框
        q = 0  # 計算產業股票數量

        # 股價內容排序(table)
        for name in selected_types:
            for stock_code in all_stock_id[name]:
                q += 1
                name1 = name
                query = f"""
                    SELECT '{stock_code}' AS 股票代碼, '{get_stock_name(int(stock_code))}' AS 股票名稱,'{name}' AS `股票產業`, `{stock_code}`.`date`as 時間, CAST(`Open` AS DECIMAL(10, 2))as 開盤, CAST(`High` AS DECIMAL(10, 2))as 最高, CAST(`Low` AS DECIMAL(10, 2))as 最低, CAST(`Close` AS DECIMAL(10, 2))as 收盤, CAST(`K9` AS DECIMAL(10, 2))as 日K值, CAST(`D9` AS DECIMAL(10, 2))as 日D值
                    FROM `{stock_code}`
                    WHERE date = (
                        SELECT MAX(date)
                        FROM `{stock_code}`
                    );
                    """
                query2 = f"""
                    SELECT '{stock_code}' AS 股票代碼, `{stock_code}`.`Unnamed: 0` AS 季別, CAST(`{rank_value}` AS DECIMAL(10, 2)) AS `{rank_value}`
                    FROM `{stock_code}`
                    WHERE `Unnamed: 0` = (
                        SELECT MAX(`Unnamed: 0`)
                        FROM `{stock_code}`
                    );
                """

                # 避免重複產生欄位
                df = pd.read_sql(query, cnx)
                df2 = pd.read_sql(query2, cnx2)
                merged_df = pd.merge(df, df2, on='股票代碼', how='inner')
                df_combined = pd.concat(
                    [df_combined, merged_df], ignore_index=True)  # 將當前資料添加到合併資料框中
        df_combined["股票代碼"] = df_combined["股票代碼"].apply(
            lambda x: f"<input type=checkbox name='search' value='{x}'><a href='/stock/{x}'>{x}</a>")
        # 在迴圈結束後對合併資料框進行排序
        df_sorted = df_combined.sort_values(by=rank_value, ascending=False)
        stock_avg = round(df_sorted[rank_value].mean(), 4)

        # 確認排序後的資料框不是空的，再生成HTML表格
        if not df_sorted.empty:
            table_html += df_sorted.to_html(header=True,
                                            index=False, escape=False)

        # 將查詢結果傳遞給 HTML 模板顯示
        return render_template(
            "index.html", stock_code=stock_code, table_html=table_html, q=q, name1=name1, stock_avg=stock_avg, rank_value=rank_value)

    else:
        return render_template("index.html")

# 最終頁面(資產配置)
@app.route("/final", methods=["POST"])
def final():
    stockcodes = request.form.getlist("search")  # 获取选定的股票代码列表
    betavalues = []
    stocknames = []
    stockprices = []
    tablekd_html = ""
    cnx = get_database_connection()
    df_combined = pd.DataFrame()  # 用於存儲所有資料的合併資料框

    # 數據蒐集
    for stockid in stockcodes:
        betavalues.append(get_stock_beta(int(stockid)))
        stocknames.append(get_stock_name(int(stockid)))
        stockprices.append(get_stock_price(int(stockid)))
    # KD表格製作
    for code in stockcodes:
        # 黃金交叉
        query = f"""SELECT '{code}' AS ID, '{get_stock_name(int(code))}' AS name, MAX(`date`) as `黃金交叉` FROM `{code}`WHERE `黃金交叉` <> 0;"""
        # 死亡交叉
        query2 = f"""SELECT '{code}' AS ID, MAX(`date`) as `死亡交叉` FROM `{code}`WHERE `死亡交叉` <> 0;"""
        # KD分類
        query3 = f"""SELECT '{code}' AS ID, `KD分類1`as `前一日KD`,`KD分類2`as `最近三日是否鈍化` FROM `{code}` WHERE date = (SELECT MAX(date) FROM `{code}`);"""
        df = pd.read_sql(query, cnx)
        df2 = pd.read_sql(query2, cnx)
        df3 = pd.read_sql(query3, cnx)
        merged_df = pd.merge(df, df2, on='ID', how='inner')
        merged_df = pd.merge(merged_df, df3, on='ID', how='inner')
        df_combined = pd.concat(
            [df_combined, merged_df], ignore_index=True)  # 將當前資料添加到合併資料框中
    mapping1 = {3: '低檔鈍化', 1: '無', 2: '高檔鈍化'}  # 最近三日是否鈍化
    mapping2 = {1: 'KD>80 超買', 2: 'KD<20 超賣', 3: "20≤KD≤80"}  # 前一日KD
    df_combined['前一日KD'] = df_combined['前一日KD'].replace(mapping2)
    df_combined['最近三日是否鈍化'] = df_combined['最近三日是否鈍化'].replace(mapping1)
    # 確認排序後的資料框不是空的，再生成HTML表格
    if not df_combined.empty:
        tablekd_html += df_combined.to_html(header=True,
                                            index=False, escape=False)

    stocks_with_beta = zip(stockcodes, betavalues, stocknames, stockprices)

    return render_template("final.html", stocks_with_beta=stocks_with_beta, tablekd_html=tablekd_html)

#首頁
@app.route("/home", methods=["GET", "POST"])
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5555)
    # threaded=True,
