import plotly.express as px
import streamlit as st


def render_decision_chart(df):
    if df.empty:
        st.info("No decision data available.")
        return

    figure = px.bar(
        df,
        x="transformation_decision",
        y="initiatives",
        title="Transformation Decision Distribution",
        text="initiatives",
    )

    figure.update_layout(
        xaxis_title="Decision",
        yaxis_title="Initiatives",
        showlegend=False,
    )

    st.plotly_chart(
        figure,
        width='stretch',
    )


def render_risk_domain_chart(df):
    if df.empty:
        st.info("No risk-domain data available.")
        return

    figure = px.bar(
        df,
        x="risk_domain",
        y="average_residual_risk",
        title="Average Residual Risk by Domain",
        text="average_residual_risk",
    )

    figure.update_layout(
        xaxis_title="Risk Domain",
        yaxis_title="Average Residual Risk",
        showlegend=False,
    )

    st.plotly_chart(
        figure,
        width='stretch',
    )


def render_readiness_chart(df):
    if df.empty:
        st.info("No readiness data available.")
        return

    figure = px.bar(
        df,
        x="readiness_band",
        y="initiatives",
        title="Transformation Readiness Distribution",
        text="initiatives",
    )

    figure.update_layout(
        xaxis_title="Readiness",
        yaxis_title="Initiatives",
        showlegend=False,
    )

    st.plotly_chart(
        figure,
        width='stretch',
    )
