import os
from flask import Flask, render_template, request, flash
import pandas as pd
import plotly.express as px
import plotly.io as pio
import psycopg2
import google.generativeai as genai
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv() 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "your-secret-key-here"

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_connection():
    try:
        return psycopg2.connect(
            dbname="postgres", user="postgres", password="postgres", host="localhost", port="5432",
        )
    except Exception as e:
        logger.error(f"Error in main route: {e}")
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    avg_chart_html = None
    bar_chart_html = None
    range_chart_html = None
    seasonality_chart_html = None
    recipe_recommendation = None

    try:
        conn = get_connection()
        if not conn:
            flash("Database connection failed", "error")
            return render_template("index.html", error="Database connection failed")

        query = "SELECT * FROM public.kalimati_master"
        df = pd.read_sql(query, conn)
        conn.close()

        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month_name()
        latest_year = df["year"].max()
        all_commodities = sorted(df['name'].unique())

        COMMON_PRODUCE_KEYWORDS = [
            'Potato', 'Tomato', 'Onion', 'Cauliflower', 'Cabbage', 'Ginger', 
            'Garlic', 'Coriander', 'Mustard Green', 'Radish', 'Cucumber', 'Pumpkin', 
            'Brinjal', 'Okra', 'Bitter Gourd', 'Beans', 'Lemon', 'Banana', 
            'Apple', 'Orange', 'Fish'
        ]
        
        common_commodities_in_data = set()
        unique_db_names = df['name'].unique()
        for keyword in COMMON_PRODUCE_KEYWORDS:
            for db_name in unique_db_names:
                if keyword.lower() in db_name.lower():
                    common_commodities_in_data.add(db_name)
        common_commodities_in_data = sorted(list(common_commodities_in_data))

        df_top = df[df["name"].isin(common_commodities_in_data)]
        
        if df_top.empty:
            flash("Could not find any common produce to display. Please check database content.", "error")
        
        # --- Chart 1: Yearly Average Prices ---
        df_yearly = df_top.groupby(["year", "name"], as_index=False).agg(
            {"average": "mean", "maximum": "mean", "minimum": "mean"}
        )
        if not df_yearly.empty:
            fig_avg = px.line(
                df_yearly, x="year", y="average", color="name",
                title="Yearly Price Trends for Common Produce", template="plotly_white",
            )
            fig_avg.update_layout(
                title={"text": "Yearly Price Trends", "x": 0.5, "xanchor": "center", "font": {"size": 24, "color": "#111827"}},
                legend_title_text="Produce", font=dict(family="Inter, sans-serif", size=12),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=60, r=40, t=80, b=60), height=500
            )

            # NEW: Set visibility for Yearly Trends chart
            # This loop makes only the first 3 traces visible by default.
            for i, trace in enumerate(fig_avg.data):
                if i >= 3:
                    trace.visible = 'legendonly'

            avg_chart_html = pio.to_html(fig_avg, full_html=False, include_plotlyjs="cdn")

        # --- Chart 2: Price Volatility ---
        if not df_yearly.empty:
            df_yearly['spread'] = df_yearly['maximum'] - df_yearly['minimum']
            df_volatility = df_yearly.groupby('name')['spread'].mean().reset_index().sort_values('spread', ascending=False)
            fig_range = px.bar(
                df_volatility, x='name', y='spread',
                title="Average Daily Price Spread (Volatility)",
                labels={'spread': 'Average Price Spread (NPR)', 'name': 'Produce'},
                template="plotly_white",
            )
            fig_range.update_layout(
                title={"text": "Price Volatility", "x": 0.5, "xanchor": "center", "font": {"size": 24, "color": "#111827"}},
                font=dict(family="Inter, sans-serif", size=12), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=60, r=40, t=80, b=60), height=500,
            )
            fig_range.update_traces(marker_color='#4f46e5')
            range_chart_html = pio.to_html(fig_range, full_html=False, include_plotlyjs='cdn')

        # --- Chart 3: Monthly Price Seasonality ---
        df_seasonal = df_top[df_top['year'] == latest_year]
        if not df_seasonal.empty:
            df_monthly_avg = df_seasonal.groupby(['month', 'name'], as_index=False)['average'].mean()
            month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
            df_monthly_avg['month'] = pd.Categorical(df_monthly_avg['month'], categories=month_order, ordered=True)
            df_monthly_avg = df_monthly_avg.sort_values('month')
            fig_seasonality = px.line(
                df_monthly_avg, x='month', y='average', color='name',
                title=f"Monthly Price Seasonality in {latest_year}",
                template="plotly_white",
            )
            fig_seasonality.update_layout(
                title={"text": "Monthly Price Seasonality", "x": 0.5, "xanchor": "center", "font": {"size": 24, "color": "#111827"}},
                legend_title_text="Produce", font=dict(family="Inter, sans-serif", size=12),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=60, r=40, t=80, b=60), height=500,
                xaxis_title="Month"
            )

            # NEW: Set visibility for Seasonality chart
            # Same logic: only the first 3 traces are visible initially.
            for i, trace in enumerate(fig_seasonality.data):
                if i >= 3:
                    trace.visible = 'legendonly'
            
            seasonality_chart_html = pio.to_html(fig_seasonality, full_html=False, include_plotlyjs='cdn')

        # --- Individual search ---
        searched_commodity = request.args.get('commodity')
        if searched_commodity:
            df_searched = df[df['name'].str.lower() == searched_commodity.lower()]
            if not df_searched.empty:
                df_searched_yearly = df_searched.groupby('year')['average'].mean().reset_index()
                fig_bar = px.bar(df_searched_yearly, x='year', y='average', title=f'Yearly Average Price for {searched_commodity.title()}', template='plotly_white')
                fig_bar.update_layout(
                    title={"text": f'Price History for {searched_commodity.title()}', "x": 0.5, "xanchor": "center", "font": {"size": 24, "color": "#111827"}},
                    font=dict(family="Inter, sans-serif", size=12), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=60, r=40, t=80, b=60), height=500, xaxis_title="Year", yaxis_title="Average Price (NPR)"
                )
                fig_bar.update_traces(marker_color='#4f46e5')
                bar_chart_html = pio.to_html(fig_bar, full_html=False, include_plotlyjs="cdn")
            else:
                flash(f"Commodity '{searched_commodity}' not found.", "error")

        # --- Recipe recommendation ---
        if request.method == "POST":
            budget = request.form.get("budget")
            if budget:
                recipe_recommendation = get_recipe_recommendation(budget, common_commodities_in_data)
            else:
                flash("Please enter a valid budget", "error")

        return render_template(
            "index.html",
            avg_chart=avg_chart_html, bar_chart_html=bar_chart_html,
            range_chart_html=range_chart_html, seasonality_chart_html=seasonality_chart_html,
            recipe_recommendation=recipe_recommendation, all_commodities=all_commodities,
            searched_commodity=searched_commodity
        )

    except Exception as e:
        logger.error(f"Error in main route: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return render_template("index.html", error=str(e))


def get_recipe_recommendation(budget, commodities):
    # This function remains unchanged
    try:
        commodities_list = ", ".join(commodities)
        prompt = f"""
        As a chef specializing in Nepali cuisine, suggest a delicious and nutritious recipe 
        that can be made with a budget of NPR {budget}. 
        Consider using these local commodities that are currently available: {commodities_list}
        Please provide:
        1. Recipe name, 2. Main ingredients (with approximate costs), 3. Brief cooking instructions, 4. Estimated total cost.
        Keep it practical and authentic to Nepali cuisine.
        """
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.7, max_output_tokens=400,))
        return response.text if response else "Sorry, I couldn't generate a recipe."
    except Exception as e:
        logger.error(f"Error generating recipe: {e}")
        return "Sorry, I couldn't generate a recipe recommendation at the moment."

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)