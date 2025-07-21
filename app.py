import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import math

# # Title
st.title("⚾ CatsStats Baseball Hit Visualization")
# Manual theme toggle
# theme = st.radio("Theme", ["light", "dark"], horizontal=True)
# if theme == "dark":
#     logo_path = "pfp.png"  # White logo for dark mode
# else:
#     logo_path = "Cats-Stats-logo-black.svg"  # Black logo for light mode

# # Logo and title in one row
# col1, col2 = st.columns([1, 8])
# with col1:
#     st.image(logo_path, width=60)
# with col2:
#     st.markdown("""
#         <div style="display: flex; align-items: center; height: 60px;">
#             <h1 style="margin: 0 0 0 10px; font-size: 2.8rem;">Baseball Hit Visualization</h1>
#         </div>
#         """, unsafe_allow_html=True)

# Upload file(s)
uploaded_files = st.file_uploader("Upload Trackman CSV File(s)", type=["csv"], accept_multiple_files=True)
if uploaded_files:
    # Read and concatenate all uploaded CSVs
    df_list = [pd.read_csv(f) for f in uploaded_files]
    df = pd.concat(df_list, ignore_index=True)

    # Show available batters
    batters = df["Batter"].dropna().unique()
    batter_name = st.selectbox("Select Batter", options=sorted(batters))

    # Filter in-play events for batter
    batter_df = df[(df["Batter"] == batter_name) & (df["PitchCall"] == "InPlay")].copy()

    st.subheader("📍 Hit Map (Ball in Play)")
    if not batter_df.empty:
        # Calculate hit locations
        batter_df.loc[:, "Direction"] = pd.to_numeric(batter_df["Direction"], errors='coerce')
        batter_df.loc[:, "Distance"] = pd.to_numeric(batter_df["Distance"], errors='coerce')
        batter_df.dropna(subset=["Direction", "Distance"], inplace=True)
        batter_df["y"] = batter_df["Distance"] * np.cos(np.radians(batter_df["Direction"]))
        batter_df["x"] = batter_df["Distance"] * np.sin(np.radians(batter_df["Direction"]))

        # Assign colors to PlayResult
        color_map = {
            "Single": "green",
            "Double": "blue",
            "Triple": "purple",
            "HomeRun": "red",
            "Out": "orange"
        }
        batter_df["Color"] = batter_df["PlayResult"].map(color_map).fillna("gray")

        # Create base scatter plot
        fig = go.Figure()


                # --- Accurate A-10 Ballpark Outline with ±45° foul lines ---
        # Hide default zero-lines
        fig.update_xaxes(zeroline=False, showline=False)
        fig.update_yaxes(zeroline=False, showline=False)

        # 1) Foul lines at ±45°
        foul_dist = 330  # extend past fence so poles are visible
        for theta in [45, -45]:
            fx = foul_dist * math.sin(math.radians(theta))
            fy = foul_dist * math.cos(math.radians(theta))
            fig.add_trace(go.Scatter(
                x=[0, fx], y=[0, fy],
                mode='lines',
                line=dict(color='red', width=1),
                showlegend=False
            ))

         # 2) Outfield fence (accurate A-10 specs at multiple angles)
        fence_distances = {
            # -90: 330,   # RF line
            -45: 330,   # just inside foul pole
            -30: 380,   # right power alley
              0: 400,   # dead center
             30: 380,   # left power alley
             45: 330,   # just inside foul pole
            #  90: 330    # LF line
        }
        # sample every degree from -90° to +90°
        angles = np.linspace(-45, 45, 91)
        radii  = np.interp(angles,
                           list(fence_distances.keys()),
                           list(fence_distances.values()))
        of_x = radii * np.sin(np.radians(angles))
        of_y = radii * np.cos(np.radians(angles))
        # plot a single smooth arc
        fig.add_trace(go.Scatter(
            x=of_x, y=of_y,
            mode='lines',
            line=dict(color='red', width=2),
            name='Outfield Fence'
        ))

        # 3) Infield grass arc (~95 ft) only between foul lines
        grass_ang = np.linspace(-70, 70, 91)
        grass_rad = 95
        # mound center in your coordinate system:
        mound_y = 60.5  # 60.5 feet from home plate
        gi_x = grass_rad * np.sin(np.radians(grass_ang))
        gi_y = mound_y+grass_rad * np.cos(np.radians(grass_ang))
        fig.add_trace(go.Scatter(
            x=gi_x, y=gi_y,
            mode='lines',
            line=dict(color='green', width=1, dash='dot'),
            name='Grass Line'
        ))

        # 4) Diamond rotated to align 1B/3B on foul lines
        # baseline = 90 ft, so 1B sits at 45°
        d = 90 / np.sqrt(2)
        diamond = [
            (0, 0),
            ( d, d),   # 1B (45°)
            (0, 2*d),  # 2B (90° from home)
            (-d, d),   # 3B (135°)
            (0, 0)
        ]
        dx, dy = zip(*diamond)
        fig.add_trace(go.Scatter(
            x=dx, y=dy,
            mode='lines',
            line=dict(color='red', width=1),
            showlegend=False
        ))


        # Add hit points
        for result in batter_df["PlayResult"].unique():
            sub_df = batter_df[batter_df["PlayResult"] == result]
            fig.add_trace(go.Scatter(
                x=sub_df["x"], y=sub_df["y"],
                mode="markers",
                marker=dict(
                    size=8,
                    color=color_map.get(result, "gray"),
                    line=dict(width=1, color="black")
                ),
                name=result,
                hovertext=sub_df[["ExitSpeed", "Angle", "Distance", "PlayResult"]].apply(
                    lambda row: f"Exit Speed: {row.ExitSpeed} mph<br>"
                                f"Angle: {row.Angle}°<br>"
                                f"Distance: {row.Distance} ft<br>"
                                f"Result: {row.PlayResult}",
                    axis=1
                ),
                hoverinfo="text"
            ))

        # Layout setup
        fig.update_layout(
            title=f"Batted Ball Locations for {batter_name}",
            height=600,
            width=600,
            xaxis_title="Feet (x)",
            yaxis_title="Feet (y)",
            showlegend=True
        )
        fig.update_yaxes(scaleanchor="x", scaleratio=1)
        st.plotly_chart(fig)

    else:
        st.warning("No in-play data available for this batter.")

    # Pie chart of pitch types
    st.subheader("🥧 Pitch Type Distribution")
    pitch_df = df[df["Batter"] == batter_name]
    if "TaggedPitchType" in pitch_df.columns:
        pitch_counts = pitch_df["TaggedPitchType"].value_counts()
        fig_pie = px.pie(pitch_counts, names=pitch_counts.index, values=pitch_counts.values, title="Pitch Types Faced")
        st.plotly_chart(fig_pie)
    else:
        st.error("❌ Column 'TaggedPitchType' not found in uploaded file.")

    # Table of in-play events
    st.subheader("📋 In-Play Event Table")
    table_columns = ["Date", "TaggedPitchType", "PlayResult", "ExitSpeed", "Angle", "Distance"]
    missing_columns = [col for col in table_columns if col not in batter_df.columns]
    if not missing_columns:
        table_df = batter_df[table_columns].rename(columns={"TaggedPitchType": "TaggedPitch"})
        st.dataframe(table_df, height=300, use_container_width=True)
    else:
        st.error(f"❌ Missing columns in uploaded file: {', '.join(missing_columns)}")

    # Step 4 – Trackman-based Summary Stats (no TruMedia)
    st.subheader("📊 Summary Statistics")

    batter_all = df[df["Batter"] == batter_name].copy()

    # Convert columns if needed
    batter_all["ExitSpeed"] = pd.to_numeric(batter_all["ExitSpeed"], errors='coerce')

    # Hits: Based on PlayResult only
    hits = batter_all["PlayResult"].isin(["Single", "Double", "Triple", "HomeRun"]).sum()

    # Walks and Strikeouts: Based on KorBB column
    walks = (batter_all["KorBB"] == "Walk").sum()
    strikeouts = (batter_all["KorBB"] == "Strikeout").sum()



    # Summary DataFrame
    summary_df = pd.DataFrame([{
        "Hits": hits,
        "Walks": walks,
        "Strikeouts": strikeouts
    }])

    st.dataframe(summary_df, use_container_width=True)
    st.caption("🎯 Goals: HardHitPct > 45%, BA > .300, OBP > .375")




else:
    st.info("👈 Please upload a Trackman .csv file to get started.")
