from flask import Flask, render_template
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)

# Database connection
def get_connection():
    return psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost",  # replace if different
        port="5432"
    )

@app.route("/")
def index():
    # Query Kalimati master table
    conn = get_connection()
    query = """
        SELECT * 
        FROM public.kalimati_master
    """
    df = pd.read_sql(query, conn)
    conn.close()

    # Convert date to year
    df['year'] = pd.to_datetime(df['date']).dt.year

    # Select top 10 commodities based on latest year average price
    latest_year = df['year'].max()
    top_commodities = (
        df[df['year'] == latest_year]
        .groupby('name')['average']
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .index
        .tolist()
    )
    df_top = df[df['name'].isin(top_commodities)]

    # Aggregate by year
    df_yearly = df_top.groupby(['year', 'name'], as_index=False).agg({
        'average': 'mean',
        'maximum': 'mean',
        'minimum': 'mean'
    })

    # Line chart: Average price over years
    fig_avg = px.line(
        df_yearly,
        x="year",
        y="average",
        color="name",
        title="Average Prices Over Years (Top 10 Commodities)",
        template="plotly_white",
        height=600,
        width=1000
    )
    fig_avg.update_layout(
        title_font_size=24,
        legend_title_text="Commodity",
        margin=dict(l=60, r=60, t=80, b=60)
    )

    # Scatter chart: Min vs Max prices
    fig_scatter = px.scatter(
        df_yearly,
        x="minimum",
        y="maximum",
        color="name",
        title="Min vs Max Prices (Top 10 Commodities, Yearly Average)",
        template="plotly_white",
        height=600,
        width=1000
    )
    fig_scatter.update_layout(
        title_font_size=24,
        legend_title_text="Commodity",
        margin=dict(l=60, r=60, t=80, b=60)
    )

    # Convert Plotly figures to HTML divs
    avg_chart = pio.to_html(fig_avg, full_html=False)
    scatter_chart = pio.to_html(fig_scatter, full_html=False)

    return render_template("index.html", avg_chart=avg_chart, scatter_chart=scatter_chart)

if __name__ == "__main__":
    app.run(debug=True)
