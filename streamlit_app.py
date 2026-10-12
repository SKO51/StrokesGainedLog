"""Strokes Gained Logger - refactored. Requires a current streamlit (>= 1.50)."""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide", page_title="Strokes Gained Entry", page_icon="⛳")

# ---------------------------------------------------------------- constants
DRAFT_PATH = Path(".stroke_draft.json")  # NOTE: shared file; key by user if deployed multi-user
PINS = ["C", "FL", "FR", "BL", "BR"]
LIES = ["Tee", "Fairway", "Rough", "Sand", "Green", "Other"]
MISSES = ["Left", "Right", "Short", "Long"]
BREAKS = ["Straight", "Uphill-L2R", "Uphill-R2L", "Downhill-L2R", "Downhill-R2L", "Tap-In"]
STEPS = ["Round Info", "Hole Info", "Shot Info", "Export"]
ROUND_KEYS = ["player_name", "tournament_name", "round_number", "num_holes", "round_type"]
SHOT_COLS = ["Shot", "Club", "Lie", "PinDistance", "MissDirection",
             "PinHigh", "OnLine", "FoulBall", "PuttBreak"]

# ---------------------------------------------------------------- styles
st.markdown("""
<style>
  :root { --primary:#2e856e; --secondary:#3a7ca5; --bg:#000; --card:#121212; --border:#333; --text:#fff; }
  .stApp, .main .block-container { background:var(--bg); color:var(--text); }
  .stButton>button, .stFormSubmitButton>button {
      border:2px solid var(--primary); border-radius:8px; color:#fff;
      background:var(--primary); transition:all .3s; }
  .stButton>button:hover, .stFormSubmitButton>button:hover {
      background:var(--secondary); border-color:var(--secondary); }
  .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color:var(--primary); }
  .stExpander, .stForm { background:var(--card); border-color:var(--border); border-radius:8px; }
  label, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
  [data-testid="stCaptionContainer"], .stMarkdown p, .stMarkdown li,
  [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color:#fff !important; }
  .steps { display:flex; justify-content:space-between; margin:1rem 0 2rem; }
  .step { flex:1; text-align:center; }
  .step .dot { width:30px; height:30px; margin:0 auto 5px; border-radius:20%;
      display:flex; align-items:center; justify-content:center;
      background:#333333; color:#9aa0a6; font-weight:bold; }
  .step small { color:#9aa0a6 !important; }
  .step.done .dot { background:#2e856e; color:#ffffff; }
  .step.done small { color:#2e856e !important; }
  .step.current .dot { background:#2e856e; color:#ffffff; outline:2px solid #f4a261; }
  .step.current small { color:#f4a261 !important; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- state
ss = st.session_state
for k, v in {"round_info_entered": False, "hole_info_entered": False,
             "shot_data": {}, "holes_df": None}.items():
    ss.setdefault(k, v)


# ---------------------------------------------------------------- draft persistence
def _records(df: pd.DataFrame):
    return df.astype(object).where(df.notna(), None).to_dict("records")


def save_draft():
    payload = {k: ss.get(k) for k in ROUND_KEYS}
    payload["round_date"] = str(ss.get("round_date", date.today()))
    payload["round_info_entered"] = ss.round_info_entered
    payload["hole_info_entered"] = ss.hole_info_entered
    payload["holes"] = _records(ss.holes_df) if ss.holes_df is not None else None
    payload["shots"] = {str(h): _records(d) for h, d in ss.shot_data.items()}
    DRAFT_PATH.write_text(json.dumps(payload, default=str))


def load_draft():
    p = json.loads(DRAFT_PATH.read_text())
    for k in ROUND_KEYS:
        ss[k] = p.get(k)
    ss.round_date = date.fromisoformat(p["round_date"])
    ss.round_info_entered = p["round_info_entered"]
    ss.hole_info_entered = p["hole_info_entered"]
    ss.holes_df = pd.DataFrame(p["holes"]) if p.get("holes") else None
    ss.shot_data = {int(h): pd.DataFrame(r, columns=SHOT_COLS) for h, r in p["shots"].items()}


def reset_all():
    for k in list(ss.keys()):
        del ss[k]
    DRAFT_PATH.unlink(missing_ok=True)


# ---------------------------------------------------------------- helpers
def default_holes(n: int) -> pd.DataFrame:
    return pd.DataFrame({"Hole": range(1, n + 1), "Par": 4, "Yardage": 400, "Score": 4, "Pin": "C"})


def default_shots(score: int, yardage: int) -> pd.DataFrame:
    lies = ["Tee"] + ["Fairway"] * (score - 1)
    if score > 1:
        lies[-1] = "Green"
    return pd.DataFrame({
        "Shot": range(1, score + 1), "Club": "", "Lie": lies,
        "PinDistance": [float(yardage)] + [np.nan] * (score - 1),
        "MissDirection": None, "PinHigh": False, "OnLine": False,
        "FoulBall": False, "PuttBreak": None,
    })


def validate_shots(df: pd.DataFrame):
    errors, warnings = [], []
    if df["PinDistance"].isna().any():
        errors.append("Every shot needs a Pin Distance.")
    if df["Lie"].isna().any():
        errors.append("Every shot needs a Lie.")
    if df["Lie"].iloc[-1] != "Green":
        warnings.append("Last shot isn't from the green - holed out? Saving anyway is fine.")
    return errors, warnings


def build_export() -> pd.DataFrame:
    parts = []
    for hole, shots in sorted(ss.shot_data.items()):
        h = ss.holes_df.iloc[hole - 1]
        par = int(h.Par)
        d = shots.copy()
        tee, green = d.Lie.eq("Tee"), d.Lie.eq("Green")
        ph_on = (tee & (par == 3)) | (~tee & ~green)   # pin-high / on-line relevant
        fb_on = tee & (par != 3)                        # foul ball relevant
        for col, mask in (("PinHigh", ph_on), ("OnLine", ph_on), ("FoulBall", fb_on)):
            d[col] = d[col].fillna(False).astype(int).astype(object).where(mask, None)
        d["PuttBreak"] = d["PuttBreak"].where(green, None)
        d["Hole"], d["Par"], d["Pin Location"] = hole, par, h.Pin
        parts.append(d)
    out = pd.concat(parts, ignore_index=True)
    out["Player"], out["RndDate"] = ss.player_name, ss.round_date
    out["Tournament"], out["Round"], out["Round Type"] = ss.tournament_name, ss.round_number, ss.round_type
    out = out.rename(columns={"Shot": "Stroke", "PinDistance": "Pin Distance",
                              "MissDirection": "Miss Direction", "PinHigh": "Pin-High",
                              "OnLine": "On-Line", "PuttBreak": "Putt Break", "FoulBall": "Foul Ball"})
    return out[["Player", "RndDate", "Tournament", "Round", "Round Type", "Hole", "Par", "Stroke",
                "Club", "Lie", "Pin Distance", "Pin Location", "Miss Direction",
                "Pin-High", "On-Line", "Putt Break", "Foul Ball"]]


# ---------------------------------------------------------------- header + progress
st.title("⛳ Golf Round Entry - Strokes Gained Logger")

with st.sidebar:
    if st.button("Start new round"):
        reset_all()
        st.rerun()

if not ss.round_info_entered and DRAFT_PATH.exists():
    c1, c2 = st.columns(2)
    if c1.button("Resume saved draft", width="stretch"):
        load_draft()
        st.rerun()
    if c2.button("Discard draft", width="stretch"):
        DRAFT_PATH.unlink(missing_ok=True)
        st.rerun()

current = 0
if ss.round_info_entered:
    current = 1
if ss.hole_info_entered:
    current = 2
if ss.shot_data:
    current = 3

st.markdown(
    '<div class="steps">' + "".join(
        f'<div class="step {"done" if i < current else "current" if i == current else ""}">'
        f'<div class="dot">{"✓" if i < current else i + 1}</div><small>{s}</small></div>'
        for i, s in enumerate(STEPS)) + "</div>",
    unsafe_allow_html=True)

# ---------------------------------------------------------------- step 1
with st.expander("Step 1: Round Info", expanded=not ss.round_info_entered):
    with st.form("round_info_form"):
        c = st.columns([1.5, 1, 1.5, 0.6, 0.6, 1.5, 1.2])
        player = c[0].text_input("Player Name", ss.get("player_name", ""))
        rdate = c[1].date_input("Round Date", ss.get("round_date", date.today()))
        tourney = c[2].text_input("Tournament", ss.get("tournament_name", ""))
        rnum = c[3].selectbox("Round", [1, 2, 3, 4], index=[1, 2, 3, 4].index(ss.get("round_number") or 1))
        nholes = c[4].number_input("Holes", 1, 18, int(ss.get("num_holes") or 18))
        rtype = c[5].selectbox("Type", ["Competitive", "Practice"],
                               index=["Competitive", "Practice"].index(ss.get("round_type") or "Competitive"))
        c[6].markdown("<div style='margin-top:1.75rem'></div>", unsafe_allow_html=True)
        if c[6].form_submit_button("Submit Round Info", width="stretch"):
            if not player.strip():
                st.error("Player name is required.")
            else:
                if int(nholes) != ss.get("num_holes"):      # hole count changed: reset downstream
                    ss.holes_df = default_holes(int(nholes))
                    ss.shot_data = {}
                    ss.hole_info_entered = False
                ss.update(player_name=player.strip(), round_date=rdate, tournament_name=tourney,
                          round_number=rnum, num_holes=int(nholes), round_type=rtype,
                          round_info_entered=True)
                if ss.holes_df is None:
                    ss.holes_df = default_holes(int(nholes))
                save_draft()
                st.rerun()

# ---------------------------------------------------------------- step 2
if ss.round_info_entered:
    with st.expander("Step 2: Hole Info", expanded=not ss.hole_info_entered):
        with st.form("hole_info_form"):
            edited = st.data_editor(
                ss.holes_df, hide_index=True, disabled=["Hole"], width="stretch",
                key="holes_editor",
                column_config={
                    "Par": st.column_config.NumberColumn(min_value=3, max_value=5, step=1),
                    "Score": st.column_config.NumberColumn(min_value=1, max_value=10, step=1),
                    "Yardage": st.column_config.NumberColumn(min_value=50, max_value=800, step=1),
                    "Pin": st.column_config.SelectboxColumn(options=PINS),
                })
            if st.form_submit_button("Submit Hole Info", width="stretch"):
                if edited.isna().any().any():
                    st.warning("Fill in every cell before submitting.")
                else:
                    edited = edited.astype({"Par": int, "Yardage": int, "Score": int})
                    changed = edited.index[edited["Score"] != ss.holes_df["Score"]] + 1
                    for h in changed:                      # score changed -> old shots invalid
                        ss.shot_data.pop(int(h), None)
                    ss.holes_df = edited
                    ss.hole_info_entered = True
                    save_draft()
                    st.rerun()

# ---------------------------------------------------------------- step 3 (fragment)
@st.fragment
def shot_entry():
    if "pending_hole" in ss:                               # set before widget is created
        ss.selected_hole = ss.pop("pending_hole")
    ss.setdefault("selected_hole", 1)
    ss.setdefault("work", {})                              # unsaved edits survive hole switching

    n = len(ss.holes_df)
    labels = {h: f"{'✓ ' if h in ss.shot_data else ''}{h}" for h in range(1, n + 1)}
    hole = st.segmented_control("Hole", list(labels), format_func=labels.get, key="selected_hole")
    if hole is None:
        st.info("Select a hole.")
        return

    row = ss.holes_df.iloc[hole - 1]
    score, par = int(row.Score), int(row.Par)
    st.markdown(f"### Hole {hole}: Par {par} · {int(row.Yardage)} yds · {score} strokes · Pin {row.Pin}")

    base = ss.work.get(hole)
    if base is None:
        base = ss.shot_data.get(hole)
    if base is None or len(base) != score:
        base = default_shots(score, int(row.Yardage))

    main_cols = ["Shot", "Club", "Lie", "PinDistance", "MissDirection"]
    main = st.data_editor(
        base[main_cols], hide_index=True, disabled=["Shot"], key=f"shots_{hole}",
        width="stretch",
        column_config={
            "Lie": st.column_config.SelectboxColumn(options=LIES, required=True),
            "PinDistance": st.column_config.NumberColumn("Pin Distance", min_value=0, max_value=1000),
            "MissDirection": st.column_config.SelectboxColumn("Miss", options=MISSES),
        })
    d = base.copy()
    d[main_cols] = main[main_cols]

    # which shots each extra field applies to
    tee, green = d.Lie.eq("Tee"), d.Lie.eq("Green")
    approach = (tee & (par == 3)) | (~tee & ~green & d.Lie.notna())
    foul = tee & (par != 3)
    d.loc[~approach, ["PinHigh", "OnLine"]] = False        # clear stale values if Lie changed
    d.loc[~foul, "FoulBall"] = False
    d.loc[~green, "PuttBreak"] = None
    d.loc[green & d.PuttBreak.isna(), "PuttBreak"] = "Straight"

    def extra_editor(title, mask, cols, config, name):
        idx = d.index[mask]
        if len(idx) == 0:
            return
        st.caption(title)
        sig = "-".join(map(str, idx))                       # reset editor when row set changes
        e = st.data_editor(d.loc[idx, ["Shot"] + cols], hide_index=True, disabled=["Shot"],
                           key=f"{name}_{hole}_{sig}", column_config=config, width="stretch")
        d.loc[idx, cols] = e[cols]

    extra_editor("Tee shot", foul, ["FoulBall"],
                 {"FoulBall": st.column_config.CheckboxColumn("Foul Ball")}, "tee")
    extra_editor("Approach shots" + (" (incl. par-3 tee shot)" if par == 3 else ""), approach,
                 ["PinHigh", "OnLine"],
                 {"PinHigh": st.column_config.CheckboxColumn("Pin-High"),
                  "OnLine": st.column_config.CheckboxColumn("On-Line")}, "appr")
    extra_editor("Putts", green, ["PuttBreak"],
                 {"PuttBreak": st.column_config.SelectboxColumn("Putt Break", options=BREAKS,
                                                                required=True)}, "putt")
    edited = d
    ss.work[hole] = edited

    errors, warnings = validate_shots(edited)
    for m in errors:
        st.error(m)
    for m in warnings:
        st.caption(f"⚠️ {m}")

    if st.button("Save & next hole", disabled=bool(errors), key=f"save_{hole}"):
        ss.shot_data[hole] = edited.copy()
        ss.work.pop(hole, None)
        if hole < n:
            ss.pending_hole = hole + 1
        save_draft()
        st.rerun()                                         # full rerun: refresh progress + export


if ss.hole_info_entered:
    with st.expander("Step 3: Shot Info", expanded=True):
        shot_entry()

# ---------------------------------------------------------------- step 4
if ss.hole_info_entered:
    with st.expander("Step 4: Export Data", expanded=bool(ss.shot_data)):
        if not ss.shot_data:
            st.caption("Save at least one hole to export.")
        else:
            out = build_export()
            missing = sorted(set(range(1, len(ss.holes_df) + 1)) - set(ss.shot_data))
            if missing:
                st.warning(f"Holes not saved (excluded from export): {', '.join(map(str, missing))}")
            st.download_button("Download CSV", out.to_csv(index=False),
                               f"{ss.player_name.replace(' ', '_')}_Stroke_Trail.csv", "text/csv")
            st.dataframe(out, width="stretch")
