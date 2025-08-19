import os
from flask import Flask, render_template, request, flash
import pandas as pd
import plotly.express as px
import plotly.io as pio
import psycopg2
import google.generativeai as genai
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "your-secret-key-here"  # Change this to a secure secret key

# Configure Google Generative AI
genai.configure(api_key="")


# Database connection
def get_connection():
    try:
        return psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432",
        )
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    try:
        conn = get_connection()
        if not conn:
            flash("Database connection failed", "error")
            return render_template("index.html", error="Database connection failed")

        query = "SELECT * FROM public.kalimati_master"
        df = pd.read_sql(query, conn)
        conn.close()

        # Data processing
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        latest_year = df["year"].max()

        # Get top 10 commodities by average price in latest year
        top_commodities = (
            df[df["year"] == latest_year]
            .groupby("name")["average"]
            .mean()
            .sort_values(ascending=False)
            .head(10)
            .index.tolist()
        )

        df_top = df[df["name"].isin(top_commodities)]
        df_yearly = df_top.groupby(["year", "name"], as_index=False).agg(
            {"average": "mean", "maximum": "mean", "minimum": "mean"}
        )

        # Create modern-looking charts
        fig_avg = px.line(
            df_yearly,
            x="year",
            y="average",
            color="name",
            title="Average Prices Over Years (Top 10 Vegetable)",
            template="plotly_white",
        )

        fig_avg.update_layout(
            title={
                "text": "Average Prices Over Years (Top 10 Vegetable)",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 24, "color": "#2c3e50"},
            },
            legend_title_text="Vegetable",
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=60, r=60, t=80, b=60),
            height=500,
        )

        fig_avg.update_traces(line=dict(width=3))
        fig_avg.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)"
        )
        fig_avg.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)"
        )

        # Min vs Max scatter chart
        fig_scatter = px.scatter(
            df_yearly,
            x="minimum",
            y="maximum",
            color="name",
            size="average",
            title="Min vs Max Prices (Top 10 Vegetable, Yearly Average)",
            template="plotly_white",
        )

        fig_scatter.update_layout(
            title={
                "text": "Min vs Max Prices (Top 10 Vegetable)",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 24, "color": "#2c3e50"},
            },
            legend_title_text="Vegetable",
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=60, r=60, t=80, b=60),
            height=500,
        )

        fig_scatter.update_traces(marker=dict(size=8, opacity=0.7))
        fig_scatter.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)"
        )
        fig_scatter.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)"
        )

        # Convert to HTML
        avg_chart = pio.to_html(fig_avg, full_html=False, include_plotlyjs="cdn")
        scatter_chart = pio.to_html(
            fig_scatter, full_html=False, include_plotlyjs="cdn"
        )

        # Handle recipe recommendation
        recipe_recommendation = None
        if request.method == "POST":
            budget = request.form.get("budget")
            if budget:
                recipe_recommendation = get_recipe_recommendation(
                    budget, top_commodities[:5]
                )
            else:
                flash("Please enter a valid budget", "error")

        return render_template(
            "index.html",
            avg_chart=avg_chart,
            scatter_chart=scatter_chart,
            recipe_recommendation=recipe_recommendation,
            top_commodities=top_commodities[:5],
            latest_year=latest_year,
        )

    except Exception as e:
        logger.error(f"Error in main route: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return render_template("index.html", error=str(e))


def get_recipe_recommendation(budget, commodities):
    try:
        # Create a more specific prompt
        commodities_list = ", ".join(commodities)
        prompt = f"""
        As a chef specializing in Nepali cuisine, suggest a delicious and nutritious recipe 
        that can be made with a budget of NPR {budget}. 
        
        Consider using these local commodities that are currently available: {commodities_list}
        
        Please provide:
        1. Recipe name
        2. Main ingredients (with approximate costs)
        3. Brief cooking instructions
        4. Estimated total cost
        
        Keep it practical and authentic to Nepali cuisine.
        """

        # Use the correct Gemini API
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=400,
            ),
        )

        return response.text

    except Exception as e:
        logger.error(f"Error generating recipe: {e}")
        return f"Sorry, I couldn't generate a recipe recommendation at the moment. Please try again later."


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
