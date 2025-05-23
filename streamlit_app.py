import streamlit as st
import pandas as pd

# Wide layout for dashboards, data tables, or multi-column forms
st.set_page_config(layout="wide", page_title="Strokes Gained Entry", page_icon="⛳")
st.title("Golf Round Entry - Strokes Gained Logger")

# Session state to preserve inputs
if "round_info_entered" not in st.session_state:
    st.session_state.round_info_entered = False
if "hole_info_entered" not in st.session_state:
    st.session_state.hole_info_entered = False

# Step 1: Round Info
st.header("Step 1: Round Info")
with st.form("round_info_form"):
    # Create columns - adjust widths as needed
    col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1, 1.5, 0.5, 0.5, 1.5, 1])

    # Player Name
    with col1:
        player_name = st.text_input("Player Name")

    # Round Date
    with col2:
        rnd_date = st.date_input("Round Date")

    # Tournament
    with col3:
        tournament = st.text_input("Tournament")

    # Round Number
    with col4:
        rnd_number = st.selectbox("Round", [1, 2, 3, 4])

    # Number of Holes
    with col5:
        num_holes = st.number_input("Holes", min_value=1, max_value=18)

    with col6:
        round_type = st.selectbox("Type", ["Competitive", "Practice"])

    # Submit Button - aligned properly with other fields
    with col7:
        st.markdown("<div style='margin-top: 1.75rem;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Submit Round Info", use_container_width=True)


    # Save values on submit
    if submitted:
        st.session_state.player_name = player_name
        st.session_state.round_date = rnd_date
        st.session_state.tournament_name = tournament
        st.session_state.round_number = rnd_number
        st.session_state.num_holes = num_holes
        st.session_state.round_type = round_type
        st.session_state.round_info_entered = True
        st.success("Round info saved!")

#Additional Notes (Green Speed, Weather, Wind, Temperature) + (Sunny OverCast Rain, High Medium Low, Slow Average Fast)
#Add Bag Club, Shaft

def show_scorecard_summary(hole_table):
    """Render the scorecard summary table"""
    holes = hole_table["Hole"]

    st.markdown("<h4 style='text-align: center; margin-top: 2rem;'>Scorecard Summary</h4>",
                unsafe_allow_html=True)

    # Build HTML table
    html = """
    <style>
        table.custom-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        table.custom-table th, table.custom-table td {
            padding: 6px 10px;
            text-align: center;
            border: 1px solid #ccc;
        }
        .score-box {
            display: inline-block;
            width: 35px;
            height: 35px;
            line-height: 35px;
            text-align: center;
            font-weight: bold;
        }
    </style>
    <table class='custom-table'>
        <thead>
            <tr>"""

    for row in ["Hole", "Par", "Score"]:
        html += f"<tr><th>{row}</th>"
        for i in range(len(holes)):
            if row == "Hole":
                val = holes[i]
                html += f"<td>{val}</td>"
            elif row == "Par":
                val = hole_table["Par"][i]
                html += f"<td>{val}</td>"
            elif row == "Score":
                score = hole_table["Score"][i]
                par = hole_table["Par"][i]

                # Determine styling
                if score <= par - 2:
                    style = "border-radius: 50%; border: 4px double green; background-color: black;"
                elif score == par - 1:
                    style = "border-radius: 50%; border: 2px solid green; background-color: black;"
                elif score == par:
                    style = ""
                elif score == par + 1:
                    style = "border: 2px solid red; background-color: black;"
                elif score >= par + 2:
                    style = "border: 4px solid red; background-color: black;"

                html += f"<td><div class='score-box' style='{style}'>{score}</div></td>"

        html += "</tr>"

    total_score = sum(hole_table["Score"])
    total_par = sum(hole_table["Par"])
    diff = total_score - total_par

    if diff > 0:
        diff_str = f"+{diff}"
    elif diff < 0:
        diff_str = f"{diff}"
    else:
        diff_str = "E"

    total_score = sum(hole_table["Score"])
    total_par = sum(hole_table["Par"])
    diff = total_score - total_par

    if diff > 0:
        diff_str = f"+{diff}"
    elif diff < 0:
        diff_str = f"{diff}"
    else:
        diff_str = "E"

    html += f"""
        <tr>
            <th style='text-align: center; font-weight: bold;'>Total</th>
             <td colspan='{len(holes)}' style='text-align: center; font-weight: bold;'>{total_score}</td>
            <td style='text-align: center; font-weight: bold;'>{total_score} ({diff_str})</td>
        </tr>
    </tbody></table>
    """

    st.markdown(html, unsafe_allow_html=True)

# Step 2: Hole Info
if st.session_state.round_info_entered:
    st.header("Step 2: Hole Info")

    # Add compact CSS styling
    st.markdown("""
    <style>
        div.stForm {
            margin-top: -1rem;
        }
        input[type="number"], 
        div[data-baseweb="select"] input {
            text-align: center !important;
        }
        .stMarkdown p {
            margin-bottom: 0.5rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Handle change in number of holes
    num_holes = int(st.session_state.num_holes)
    if "last_num_holes" not in st.session_state or st.session_state.last_num_holes != num_holes:
        st.session_state.last_num_holes = num_holes
        st.session_state.hole_page = 0
        st.session_state.all_hole_data = {
            "Hole": list(range(1, num_holes + 1)),
            "Par": [None] * num_holes,
            "Score": [None] * num_holes,
            "Yardage": [None] * num_holes,
            "Pin": [None] * num_holes,
        }

    if "hole_page" not in st.session_state:
        st.session_state.hole_page = 0

    with st.form("hole_info_form"):
        st.markdown("<h3 style='text-align: center; margin-bottom: 1rem;'>Hole Summary Table</h3>",
                    unsafe_allow_html=True)

        holes_per_page = 9
        total_pages = (num_holes - 1) // holes_per_page + 1
        current_page = st.session_state.hole_page

        start = current_page * holes_per_page
        end = min(start + holes_per_page, num_holes)
        holes = list(range(start + 1, end + 1))  # holes for this page

        rows = ["Hole", "Par", "Score", "Yardage", "Pin"]
        table_data = {row: [] for row in rows}

        for row in rows:
            cols = st.columns([1] + [1 for _ in holes])

            cols[0].markdown(
                f"""
                <div style='
                    font-weight: bold;
                    font-size: 20px;
                    text-align: center;
                    line-height: 38px;
                    height: 38px;
                '>
                    {row}
                </div>
                """,
                unsafe_allow_html=True
            )

            for i, hole_number in enumerate(holes):
                key = f"{row.lower().replace(' ', '_')}_{hole_number}"
                idx = hole_number - 1

                if row == "Hole":
                    cols[i + 1].markdown(
                        f"<div style='text-align: center; font-weight: bold; font-size: 20px;'>{hole_number}</div>",
                        unsafe_allow_html=True)
                    table_data[row].append(hole_number)
                elif row == "Par":
                    val = cols[i + 1].number_input("Par", min_value=3, max_value=5,
                                                   value=st.session_state.all_hole_data[row][idx] or 4,
                                                   key=key, label_visibility="collapsed")
                    table_data[row].append(val)
                elif row == "Score":
                    val = cols[i + 1].number_input("Score", min_value=1, max_value=10,
                                                   value=st.session_state.all_hole_data[row][idx] or 4,
                                                   key=key, label_visibility="collapsed")
                    table_data[row].append(val)
                elif row == "Yardage":
                    val = cols[i + 1].number_input("Yardage", min_value=50, max_value=800,
                                                   value=st.session_state.all_hole_data[row][idx] or 400,
                                                   key=key, label_visibility="collapsed")
                    table_data[row].append(val)
                elif row == "Pin":
                    val = cols[i + 1].selectbox("Pin", options=["C", "FL", "FR", "BL", "BR"],
                                                index=0 if st.session_state.all_hole_data[row][idx] is None
                                                else ["C", "FL", "FR", "BL", "BR"].index(st.session_state.all_hole_data[row][idx]),
                                                key=key, label_visibility="collapsed")
                    table_data[row].append(val)

        # Pagination controls (only show if more than one page)
        if total_pages > 1:
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            center_col = st.columns([1, 2, 1])[1]

            with center_col:
                prev_col, next_col = st.columns([1, 1])

                with prev_col:
                    prev_clicked = st.form_submit_button("⛳ First Nine", use_container_width=True)

                with next_col:
                    next_clicked = st.form_submit_button("Second Nine ⛳⛳", use_container_width=True)

                if prev_clicked and current_page > 0:
                    for row in rows:
                        for i, val in enumerate(table_data[row]):
                            st.session_state.all_hole_data[row][start + i] = val
                    st.session_state.hole_page -= 1
                    st.rerun()

                if next_clicked and current_page < total_pages - 1:
                    for row in rows:
                        for i, val in enumerate(table_data[row]):
                            st.session_state.all_hole_data[row][start + i] = val
                    st.session_state.hole_page += 1
                    st.rerun()

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted_holes = st.form_submit_button("Submit Hole Info", use_container_width=True)

        if submitted_holes:
            for row in rows:
                for i, val in enumerate(table_data[row]):
                    st.session_state.all_hole_data[row][start + i] = val

            all_holes_entered = all(
                len(st.session_state.all_hole_data[row]) == num_holes and
                all(val is not None for val in st.session_state.all_hole_data[row])
                for row in rows
            )

            if all_holes_entered:
                st.session_state.hole_info_entered = True
                st.session_state.hole_table = st.session_state.all_hole_data

                for k in ["shot_data", "saved_holes", "save_shots_clicked"]:
                    if k in st.session_state:
                        del st.session_state[k]

                st.session_state.shot_data = {}
                st.session_state.saved_holes = set()
                st.session_state.selected_hole = 1

                st.success("All hole information saved and shot data reset!")

                show_scorecard_summary(st.session_state.hole_table)
            else:
                st.warning(f"Please complete all {num_holes} holes before submitting")

# Step 3: Shot Info
if st.session_state.get("hole_info_entered", False):
    st.header("Step 3: Shot Info")

    if "saved_holes" not in st.session_state:
        st.session_state.saved_holes = set()

    # --- Handle Save Shots if button was clicked ---
    if "save_shots_clicked" in st.session_state and st.session_state.save_shots_clicked:
        selected_hole = st.session_state.get("selected_hole", 1)
        score = st.session_state.hole_table["Score"][selected_hole - 1]

        shot_inputs = []
        for shot in range(1, score + 1):
            shot_dict = {
                "ShotNumber": shot,
                "Club": st.session_state.get(f"club_{selected_hole}_{shot}", ""),
                "Lie": st.session_state.get(f"lie_{selected_hole}_{shot}", ""),
                "PinDistance": st.session_state.get(f"pd_{selected_hole}_{shot}", ""),
                "MissDirection": st.session_state.get(f"md_{selected_hole}_{shot}", "")
            }

            lie = shot_dict["Lie"]
            par = st.session_state.hole_table["Par"][selected_hole - 1]
            if lie == "Tee":
                if par == 3:
                    shot_dict["PinHigh"] = st.session_state.get(f"ph_{selected_hole}_{shot}", "")
                    shot_dict["OnLine"] = st.session_state.get(f"ol_{selected_hole}_{shot}", "")
                else:
                    shot_dict["FoulBall"] = st.session_state.get(f"fb_{selected_hole}_{shot}", "")
            elif lie == "Green":
                shot_dict["PuttBreak"] = st.session_state.get(f"pb_{selected_hole}_{shot}", "")
            else:
                shot_dict["PinHigh"] = st.session_state.get(f"ph_{selected_hole}_{shot}", "")
                shot_dict["OnLine"] = st.session_state.get(f"ol_{selected_hole}_{shot}", "")

            shot_inputs.append(shot_dict)

        st.session_state.shot_data[selected_hole] = shot_inputs
        st.session_state.saved_holes.add(selected_hole)
        del st.session_state.save_shots_clicked  # Reset the flag
        st.rerun()  # Force immediate rerun to update UI

    # --- Hole selection logic with auto-save ---
    st.markdown("### Select a Hole")

    # Define callback function
    def select_hole_callback(hole_num):
        prev_hole = st.session_state.get("selected_hole")
        if prev_hole:
            score = st.session_state.hole_table["Score"][prev_hole - 1]
            shot_inputs = []
            for shot in range(1, score + 1):
                shot_dict = {
                    "ShotNumber": shot,
                    "Club": st.session_state.get(f"club_{prev_hole}_{shot}", ""),
                    "Lie": st.session_state.get(f"lie_{prev_hole}_{shot}", ""),
                    "PinDistance": st.session_state.get(f"pd_{prev_hole}_{shot}", ""),
                    "MissDirection": st.session_state.get(f"md_{prev_hole}_{shot}", "")
                }

                lie = shot_dict["Lie"]
                par = st.session_state.hole_table["Par"][prev_hole - 1]
                if lie == "Tee":
                    if par == 3:
                        shot_dict["PinHigh"] = st.session_state.get(f"ph_{prev_hole}_{shot}", "")
                        shot_dict["OnLine"] = st.session_state.get(f"ol_{prev_hole}_{shot}", "")
                    else:
                        shot_dict["FoulBall"] = st.session_state.get(f"fb_{prev_hole}_{shot}", "")
                elif lie == "Green":
                    shot_dict["PuttBreak"] = st.session_state.get(f"pb_{prev_hole}_{shot}", "")
                else:
                    shot_dict["PinHigh"] = st.session_state.get(f"ph_{prev_hole}_{shot}", "")
                    shot_dict["OnLine"] = st.session_state.get(f"ol_{prev_hole}_{shot}", "")

                shot_inputs.append(shot_dict)

            st.session_state.shot_data[prev_hole] = shot_inputs
            st.session_state.saved_holes.add(prev_hole)

        st.session_state.selected_hole = hole_num

    total_holes = len(st.session_state.hole_table["Hole"])
    cols = st.columns(total_holes)

    for i, col in enumerate(cols):
        hole_num = i + 1
        is_saved = hole_num in st.session_state.saved_holes

        button_label = f"Hole {hole_num}"
        status_text = "✓ Saved" if is_saved else "Not Saved"
        status_bg = "#d4edda" if is_saved else "#f8d7da"
        status_color = "#155724" if is_saved else "#721c24"

        # Use a shared wrapper with fixed width and center alignment
        wrapper_html = f"""
        <div style="width: 100%; text-align: center;">
            <div style="background-color: {status_bg}; color: {status_color};
                        padding: 4px 0; border-radius: 5px;
                        font-size: 12px; margin-bottom: 4px; max-width: 100%;">
                {status_text}
            </div>
        </div>
        """
        col.markdown(wrapper_html, unsafe_allow_html=True)

        # Button — maintain same alignment
        with col:
            col.button(button_label, key=f"select_hole_{hole_num}",
                       on_click=select_hole_callback, args=(hole_num,))

    # --- Show Shot Input UI ---
    selected_hole = st.session_state.get("selected_hole", 1)
    st.subheader(f"Shot Entry for Hole {selected_hole}")
    par = st.session_state.hole_table['Par'][selected_hole - 1]
    yardage = st.session_state.hole_table['Yardage'][selected_hole - 1]
    score = st.session_state.hole_table['Score'][selected_hole - 1]
    pin = st.session_state.hole_table['Pin'][selected_hole - 1]

    # Determine shape and style
    shape_style = ""
    if score <= par - 2:
        shape_style = "border-radius: 50%; border: 3px double green;"
    elif score == par - 1:
        shape_style = "border-radius: 50%; border: 2px solid green;"
    elif score == par + 1:
        shape_style = "border: 2px solid red;"
    elif score >= par + 2:
        shape_style = "border: 3px double red;"

    # Build styled score box
    if shape_style:
        styled_score = f"""
            <span style="
                display: inline-block;
                width: 35px;
                height: 35px;
                line-height: 32px;
                text-align: center;
                font-weight: bold;
                {shape_style}
            ">
                {score}
            </span>
        """
    else:
        styled_score = f"<span style='font-weight: bold;'>{score}</span>"

    # Show the styled header
    st.markdown(
        f"""
        <h3 style="text-align: left;">
            Par {par} – {yardage} yds – {styled_score} Strokes – Pin ({pin})
        </h3>
        """,
        unsafe_allow_html=True
    )

    score = st.session_state.hole_table["Score"][selected_hole - 1]
    yardage = st.session_state.hole_table["Yardage"][selected_hole - 1]
    par = st.session_state.hole_table["Par"][selected_hole - 1]


    # Load saved data if available
    if selected_hole in st.session_state.shot_data:
        saved_shots = st.session_state.shot_data[selected_hole]
    else:
        saved_shots = [{} for _ in range(score)]

    for shot in range(1, score + 1):
        st.markdown(f"#### Shot {shot}")
        cols = st.columns(8)

        # Get saved values or defaults
        saved_shot = saved_shots[shot-1] if shot-1 < len(saved_shots) else {}

        club = cols[0].text_input("Club",
                                 value=saved_shot.get("Club", ""),
                                 key=f"club_{selected_hole}_{shot}")
        lie = cols[1].selectbox("Lie", ["Tee", "Fairway", "Rough", "Sand", "Green", "Other", ""],
                               index=["Tee", "Fairway", "Rough", "Sand", "Green", "Other", ""].index(saved_shot.get("Lie", "Tee")),
                               key=f"lie_{selected_hole}_{shot}")
        pin_distance = cols[2].number_input(
            "Pin Distance", min_value=-1, max_value=1000,
            value=saved_shot.get("PinDistance", int(yardage) if shot == 1 else -1),
            key=f"pd_{selected_hole}_{shot}"
        )
        miss_direction = cols[3].selectbox("Miss Direction", ["", "Left", "Right", "Short", "Long"],
                                         index=["", "Left", "Right", "Short", "Long"].index(saved_shot.get("MissDirection", "")),
                                         key=f"md_{selected_hole}_{shot}")

        # Conditional fields
        if lie == "Tee":
            if par == 3:
                cols[4].selectbox("Pin-High", ["", 1, 0],
                                index=["", 1, 0].index(saved_shot.get("PinHigh", "")),
                                key=f"ph_{selected_hole}_{shot}")
                cols[5].selectbox("On-Line", ["", 1, 0],
                                 index=["", 1, 0].index(saved_shot.get("OnLine", "")),
                                 key=f"ol_{selected_hole}_{shot}")
            else:
                cols[4].selectbox("Foul Ball", ["No", "Yes"],
                                index=["No", "Yes"].index(saved_shot.get("FoulBall", "No")),
                                key=f"fb_{selected_hole}_{shot}")
        elif lie == "Green":
            cols[4].selectbox("Putt Break", ["Straight", "Uphill-L2R", "Uphill-R2L", "Downhill-L2R", "Downhill-R2L", "Tap-In"],
                             index=["Straight", "Uphill-L2R", "Uphill-R2L", "Downhill-L2R", "Downhill-R2L", "Tap-In"].index(
                                 saved_shot.get("PuttBreak", "Straight")),
                             key=f"pb_{selected_hole}_{shot}")
        else:
            cols[4].selectbox("Pin-High", ["", 1, 0],
                            index=["", 1, 0].index(saved_shot.get("PinHigh", "")),
                            key=f"ph_{selected_hole}_{shot}")
            cols[5].selectbox("On-Line", ["", 1, 0],
                            index=["", 1, 0].index(saved_shot.get("OnLine", "")),
                            key=f"ol_{selected_hole}_{shot}")

    # Manual save button with auto-advance
    if st.button("Save Shots & Next Hole", key=f"save_{selected_hole}"):
        # Save current hole's data
        shot_inputs = []
        for shot in range(1, score + 1):
            shot_dict = {
                "ShotNumber": shot,
                "Club": st.session_state.get(f"club_{selected_hole}_{shot}", ""),
                "Lie": st.session_state.get(f"lie_{selected_hole}_{shot}", "Tee"),  # Default to "Tee"
                "PinDistance": st.session_state.get(f"pd_{selected_hole}_{shot}", 0.0),
                "MissDirection": st.session_state.get(f"md_{selected_hole}_{shot}", "")
            }

            # Handle conditional fields based on lie type
            lie = shot_dict["Lie"]
            par = st.session_state.hole_table["Par"][selected_hole - 1]

            if lie == "Tee":
                if par == 3:
                    shot_dict["PinHigh"] = st.session_state.get(f"ph_{selected_hole}_{shot}", "")
                    shot_dict["OnLine"] = st.session_state.get(f"ol_{selected_hole}_{shot}", "")
                else:
                    shot_dict["FoulBall"] = st.session_state.get(f"fb_{selected_hole}_{shot}", "No")
            elif lie == "Green":
                shot_dict["PuttBreak"] = st.session_state.get(f"pb_{selected_hole}_{shot}", "Straight")
            else:
                shot_dict["PinHigh"] = st.session_state.get(f"ph_{selected_hole}_{shot}", "")
                shot_dict["OnLine"] = st.session_state.get(f"ol_{selected_hole}_{shot}", "")

            shot_inputs.append(shot_dict)

        # Update session state
        st.session_state.shot_data[selected_hole] = shot_inputs
        st.session_state.saved_holes.add(selected_hole)

        # Auto-advance to next hole if available
        next_hole = selected_hole + 1
        if next_hole <= len(st.session_state.hole_table["Hole"]):
            st.session_state.selected_hole = next_hole
            st.success(f"Hole {selected_hole} saved. Moving to Hole {next_hole}")
        else:
            st.success(f"Hole {selected_hole} saved (last hole completed)")

        st.rerun()


# --- Final Export Section ---
if st.session_state.get("hole_info_entered", False):
    st.header("Step 4: Export Data")

    saved_holes = st.session_state.saved_holes
    all_hole_numbers = set(st.session_state.hole_table["Hole"])
    unsaved_holes = all_hole_numbers - saved_holes

    if st.button("Generate CSV"):
        import pandas as pd

        # Define all columns with desired names
        all_columns = [
            'Player', 'RndDate', 'Tournament', 'Round', 'Round Type',
            'Hole', 'Par', 'Stroke', 'Club', 'Lie',
            'Pin Distance', 'Pin Location', 'Miss Direction',
            'Pin-High', 'On-Line', 'Putt Break', 'Foul Ball'
        ]

        # Prepare data
        rows = []
        for hole_num in sorted(saved_holes):  # Only process saved holes
            base_data = {
                'Player': st.session_state.get("player_name", ""),
                'RndDate': st.session_state.get("round_date", ""),
                'Tournament': st.session_state.get("tournament_name", ""),
                'Round': st.session_state.get("round_number", ""),
                'Round Type': st.session_state.get("round_type", ""),
                'Hole': hole_num,
                'Par': st.session_state.hole_table['Par'][hole_num - 1]
            }

            if hole_num in st.session_state.shot_data:
                for shot in st.session_state.shot_data[hole_num]:
                    row = base_data.copy()
                    row.update({
                        'Stroke': shot.get('ShotNumber', pd.NA),
                        'Club': shot.get('Club', pd.NA),
                        'Lie': shot.get('Lie', pd.NA),
                        'Pin Distance': shot.get('PinDistance', pd.NA),
                        'Pin Location': st.session_state.hole_table['Pin'][hole_num - 1],
                        'Miss Direction': shot.get('MissDirection', pd.NA),
                        'Pin-High': shot.get('PinHigh', pd.NA),
                        'On-Line': shot.get('OnLine', pd.NA),
                        'Putt Break': shot.get('PuttBreak', pd.NA),
                        'Foul Ball': shot.get('FoulBall', pd.NA)
                    })
                    rows.append(row)
            else:
                # If no shots saved, still record hole info
                row = base_data.copy()
                row.update({
                    'Stroke': pd.NA, 'Club': pd.NA, 'Lie': pd.NA, 'Pin Distance': pd.NA,
                    'Pin Location': st.session_state.hole_table['Pin'][hole_num - 1],
                    'Miss Direction': pd.NA, 'Pin-High': pd.NA, 'On-Line': pd.NA,
                    'Putt Break': pd.NA, 'Foul Ball': pd.NA
                })
                rows.append(row)

        # Create DataFrame and ensure all columns are present
        df = pd.DataFrame(rows)
        for col in all_columns:
            if col not in df.columns:
                df[col] = pd.NA
        df = df[all_columns]

        # Convert to CSV
        csv_data = df.to_csv(index=False)

        # Generate dynamic filename
        file_name = f"{st.session_state.player_name.replace(' ', '_')}_Stroke_Trail.csv"

        # Create download button
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=file_name,
            mime="text/csv"
        )

        # Show preview
        st.write("Data Preview:")
        st.dataframe(df)

        # Show warning if some holes were skipped
        if unsaved_holes:
            st.warning(f"Note: Shots for Holes {', '.join(map(str, sorted(unsaved_holes)))} were not saved and have been excluded.")

#streamlit run StrokesGainedSheet.py

