import plotly.graph_objects as go
import streamlit as st


def render_risk_matrix(risk_df):
    if risk_df.empty:
        st.info("No risk data available for this initiative.")
        return

    matrix = (
        risk_df.groupby(["impact", "likelihood"])
        .size()
        .reset_index(name="risk_count")
    )

    x_values = [1, 2, 3, 4, 5]
    y_values = [1, 2, 3, 4, 5]

    z = []

    for impact in y_values:
        row = []

        for likelihood in x_values:
            match = matrix[
                (matrix["impact"] == impact)
                & (matrix["likelihood"] == likelihood)
            ]

            if match.empty:
                row.append(0)
            else:
                row.append(int(match.iloc[0]["risk_count"]))

        z.append(row)

    figure = go.Figure(
        data=go.Heatmap(
            x=x_values,
            y=y_values,
            z=z,
            text=z,
            texttemplate="%{text}",
            hovertemplate=(
                "Likelihood: %{x}<br>"
                "Impact: %{y}<br>"
                "Risk Count: %{z}<extra></extra>"
            ),
            colorbar=dict(
                title="Risk Count"
            ),
        )
    )

    figure.update_layout(
        title="Likelihood × Impact Risk Matrix",
        xaxis_title="Likelihood",
        yaxis_title="Impact",
        xaxis=dict(
            tickmode="array",
            tickvals=x_values,
            ticktext=[
                "1 - Rare",
                "2 - Unlikely",
                "3 - Possible",
                "4 - Likely",
                "5 - Almost Certain",
            ],
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=y_values,
            ticktext=[
                "1 - Minor",
                "2 - Low",
                "3 - Moderate",
                "4 - Major",
                "5 - Severe",
            ],
        ),
        height=550,
    )

    st.plotly_chart(
        figure,
        width="stretch",
    )