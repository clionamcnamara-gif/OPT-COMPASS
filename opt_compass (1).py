"""
OPT Compass – Streamlit port of the R Shiny app
Run with:  streamlit run opt_compass.py
Dependencies: streamlit pandas
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import io

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="OPT Compass", page_icon="🧭", layout="wide")

# ── Session-state defaults ──────────────────────────────────────────────────────
if "unemp_log" not in st.session_state:
    st.session_state.unemp_log = pd.DataFrame(
        columns=["Start", "End", "Days"]
    )

if "timeline_generated" not in st.session_state:
    st.session_state.timeline_generated = False

if "timeline_df" not in st.session_state:
    st.session_state.timeline_df = None

if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""


# ── Helper ──────────────────────────────────────────────────────────────────────
def build_timeline(grad_date, opt_start, has_stem_ext):
    opt_end = opt_start + relativedelta(months=12)
    milestones = [
        {"Milestone": "Graduation", "Date": grad_date},
        {"Milestone": "OPT Start",  "Date": opt_start},
        {"Milestone": "OPT End",    "Date": opt_end},
    ]
    if has_stem_ext:
        stem_end = opt_end + relativedelta(months=24)
        milestones.append({"Milestone": "STEM OPT End", "Date": stem_end})
    return pd.DataFrame(milestones)


def unemployment_limit(has_stem_ext):
    return 150 if has_stem_ext else 90


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_timeline, tab_unemp, tab_resources = st.tabs(
    ["📅 Timeline", "⏱ Unemployment Tracker", "🔗 Resources"]
)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 – TIMELINE
# ──────────────────────────────────────────────────────────────────────────────
with tab_timeline:
    st.info(
        "**Disclaimer:** This tool is for informational purposes only and does "
        "not constitute legal or immigration advice."
    )

    with st.sidebar:
        st.header("🧭 OPT Compass")
        grad_date = st.date_input("Graduation date", value=date.today())
        degree     = st.selectbox("Degree level", ["Bachelor's", "Master's", "PhD"])
        stem       = st.selectbox("Major type", ["STEM", "Non-STEM"])

        has_stem_ext = False
        if stem == "STEM":
            has_stem_ext = st.checkbox("Add STEM OPT Extension (24 months)?", value=False)

        opt_start = st.date_input("OPT start date", value=date.today())

        generate = st.button("Generate OPT Info", type="primary", use_container_width=True)

        st.divider()

        # Downloads only visible after generation
        if st.session_state.timeline_generated and st.session_state.timeline_df is not None:
            td = st.session_state.timeline_df

            # CSV download
            csv_bytes = td.to_csv(index=False).encode()
            st.download_button(
                "⬇ Download timeline (CSV)",
                data=csv_bytes,
                file_name=f"opt_compass_timeline_{date.today()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            # HTML download
            html_rows = "".join(
                f"<tr><td>{row.Milestone}</td><td>{row.Date}</td></tr>"
                for row in td.itertuples()
            )
            html_content = f"""<html><head><meta charset='utf-8'>
<title>OPT Compass Summary</title></head><body>
<h1>OPT Compass Summary</h1>
<p>{st.session_state.summary_text}</p>
<h2>Timeline</h2>
<table border='1' cellpadding='6' cellspacing='0'>
<tr><th>Milestone</th><th>Date</th></tr>
{html_rows}
</table>
<p style='margin-top:24px;'>Generated on {date.today()}</p>
</body></html>"""
            st.download_button(
                "⬇ Download summary (HTML)",
                data=html_content.encode(),
                file_name=f"opt_compass_summary_{date.today()}.html",
                mime="text/html",
                use_container_width=True,
            )

    # ── Generate on button click ────────────────────────────────────────────
    if generate:
        st.session_state.timeline_df = build_timeline(grad_date, opt_start, has_stem_ext)
        st.session_state.summary_text = (
            f"Graduation: {grad_date} | Degree: {degree} | Major: {stem} | "
            f"OPT start: {opt_start} | STEM extension: {'Yes' if has_stem_ext else 'No'}"
        )
        st.session_state.timeline_generated = True

    # ── Show results ────────────────────────────────────────────────────────
    st.subheader("Overview")

    if st.session_state.timeline_generated and st.session_state.timeline_df is not None:
        td = st.session_state.timeline_df
        st.caption(st.session_state.summary_text)

        # Status banner
        opt_end_row = td[td["Milestone"] == "OPT End"]
        if not opt_end_row.empty:
            opt_end_date = pd.to_datetime(opt_end_row.iloc[0]["Date"]).date()
            days_left = (opt_end_date - date.today()).days
            if days_left < 0:
                st.error("Your OPT End date is in the past (based on the selected OPT start date).")
            elif days_left <= 30:
                st.error(f"Days until OPT End: **{days_left}**")
            elif days_left <= 90:
                st.warning(f"Days until OPT End: **{days_left}**")
            else:
                st.success(f"Days until OPT End: **{days_left}**")

        # Timeline table
        st.subheader("Timeline table")
        display_df = td.copy()
        display_df["Date"] = pd.to_datetime(display_df["Date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Visual timeline (simple horizontal chart using st.bar_chart workaround)
        st.subheader("Visual timeline")
        timeline_chart_df = pd.DataFrame({
            "Date": pd.to_datetime(td["Date"]),
            "Milestone": td["Milestone"],
            "Y": [1] * len(td),
        })

        # Use plotly for a clean horizontal timeline
        try:
            import plotly.express as px
            fig = px.scatter(
                timeline_chart_df,
                x="Date",
                y="Y",
                text="Milestone",
                height=200,
            )
            fig.update_traces(
                marker=dict(size=14, color="#2196F3"),
                textposition="top center",
            )
            fig.update_layout(
                yaxis=dict(visible=False, range=[0.5, 1.8]),
                xaxis_title="Date",
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=40),
                plot_bgcolor="white",
            )
            # Add a horizontal line
            fig.add_shape(
                type="line",
                x0=timeline_chart_df["Date"].min(),
                x1=timeline_chart_df["Date"].max(),
                y0=1, y1=1,
                line=dict(color="#2196F3", width=3),
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            # Fallback if plotly not installed
            st.write(display_df.set_index("Milestone")["Date"])

    else:
        st.info("Fill in the sidebar and click **Generate OPT Info** to see your timeline.")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 – UNEMPLOYMENT TRACKER
# ──────────────────────────────────────────────────────────────────────────────
with tab_unemp:
    st.subheader("Unemployment Tracker")
    st.caption("Add periods when you were not employed while on OPT.")

    col1, col2 = st.columns(2)
    with col1:
        unemp_start = st.date_input("Unemployment start", value=date.today(), key="us")
    with col2:
        unemp_end   = st.date_input("Unemployment end",   value=date.today(), key="ue")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        add_period = st.button("➕ Add period", type="primary", use_container_width=True)
    with btn_col2:
        clear_all  = st.button("🗑 Clear all",  use_container_width=True)

    if add_period:
        if unemp_end < unemp_start:
            st.error("End date must be on or after start date.")
        else:
            days = (unemp_end - unemp_start).days + 1  # inclusive
            new_row = pd.DataFrame([{
                "Start": str(unemp_start),
                "End":   str(unemp_end),
                "Days":  days,
            }])
            st.session_state.unemp_log = pd.concat(
                [st.session_state.unemp_log, new_row], ignore_index=True
            )
            st.success(f"Added {days} day(s).")

    if clear_all:
        st.session_state.unemp_log = pd.DataFrame(columns=["Start", "End", "Days"])

    # Summary
    log = st.session_state.unemp_log
    # Determine limit based on sidebar stem_ext (use session state if available)
    generated = st.session_state.get("timeline_generated", False)
    # We need stem/stem_ext from sidebar – re-read via session-state trick
    # Simpler: expose a widget here too
    limit = unemployment_limit(has_stem_ext if "has_stem_ext" in dir() else False)
    total_used = int(log["Days"].sum()) if not log.empty else 0
    remaining  = limit - total_used
    pct        = min(100, max(0, int(100 * total_used / limit)))

    st.info(
        f"You have used **{total_used}** unemployment days out of **{limit}**. "
        f"Remaining: **{remaining}**"
    )

    # Progress bar colour via markdown trick
    bar_color = "#dc3545" if remaining <= 10 else ("#ffc107" if remaining <= 30 else "#198754")
    st.markdown(
        f"""
        <div style="background:#e9ecef;border-radius:4px;height:24px;width:100%;">
          <div style="background:{bar_color};width:{pct}%;height:24px;border-radius:4px;
                      display:flex;align-items:center;justify-content:center;
                      color:white;font-weight:bold;font-size:13px;">
            {pct}%
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.dataframe(log, use_container_width=True, hide_index=True)

    if not log.empty:
        csv_bytes = log.to_csv(index=False).encode()
        st.download_button(
            "⬇ Download unemployment log (CSV)",
            data=csv_bytes,
            file_name=f"opt_compass_unemployment_{date.today()}.csv",
            mime="text/csv",
        )


# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 – RESOURCES
# ──────────────────────────────────────────────────────────────────────────────
with tab_resources:
    st.subheader("Helpful Resources")
    st.markdown(
        """
        - [USCIS OPT overview](https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt)
        - [Study in the States (DHS)](https://studyinthestates.dhs.gov/students)
        - Add your university's International Student Office OPT page link here.

        **Tip:** You can download the HTML summary from the Timeline tab and print it to PDF if needed.
        """
    )
