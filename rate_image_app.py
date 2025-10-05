import streamlit as st
import pandas as pd
import os
import random

# Set page config
st.set_page_config(layout="wide", page_title="Chair Design Rating Tool")

# Function to load or create expert_ratings.csv
def load_or_create_ratings():
    if os.path.exists("expert_ratings.csv"):
        ratings_df = pd.read_csv("expert_ratings.csv")
    else:
        ratings_df = pd.DataFrame(
            columns=[
                "expert_id",
                "participant_id",
                "photo_position",
                "value",
                "novelty",
            ]
        )
        ratings_df.to_csv("expert_ratings.csv", index=False)
    return ratings_df

# Function to save ratings to expert_ratings.csv
def save_ratings(ratings_df):
    ratings_df.to_csv("expert_ratings.csv", index=False)

# Function to load or create the participant order CSV for all experts
def load_or_create_participant_order_csv():
    order_file = "expert_orders.csv"
    # Get list of participant IDs from directory structure
    participant_ids = [f"P{i}" for i in range(1, 21)]  # Example: P1 to P20
    
    if os.path.exists(order_file):
        order_df = pd.read_csv(order_file)
    else:
        # Initialize an empty DataFrame if the file does not exist
        order_df = pd.DataFrame(columns=["expert_id"] + participant_ids)
        order_df.to_csv(order_file, index=False)
    return order_df, participant_ids

# Function to get or create the randomized order for an expert
def get_or_create_participant_order(expert_id, participant_ids, order_df):
    if expert_id in order_df["expert_id"].values:
        # Load existing order
        expert_order = order_df[order_df["expert_id"] == expert_id].iloc[0, 1:].tolist()
    else:
        # Create a new randomized order
        expert_order = participant_ids.copy()
        random.shuffle(expert_order)
        new_row = pd.Series([expert_id] + expert_order, index=order_df.columns)
        order_df = pd.concat([order_df, pd.DataFrame([new_row])], ignore_index=True)
        save_participant_order_csv(order_df)
    return expert_order, order_df

# Function to save the participant order CSV
def save_participant_order_csv(order_df):
    order_df.to_csv("expert_orders.csv", index=False)

# Function to save or update ratings
def save_or_update_ratings(
    ratings_df, expert_id, participant_id, photo_position, value, novelty
):
    existing_rating = ratings_df[
        (ratings_df["expert_id"] == expert_id) & 
        (ratings_df["participant_id"] == participant_id) & 
        (ratings_df["photo_position"] == photo_position)
    ]
    
    if not existing_rating.empty:
        # Update existing rating
        ratings_df.loc[
            existing_rating.index,
            ["value", "novelty"],
        ] = [value, novelty]
    else:
        # Append new rating
        new_ratings = pd.DataFrame(
            {
                "expert_id": [expert_id],
                "participant_id": [participant_id],
                "photo_position": [photo_position],
                "value": [value],
                "novelty": [novelty],
            }
        )
        ratings_df = pd.concat([ratings_df, new_ratings], ignore_index=True)
    save_ratings(ratings_df)
    return ratings_df

# Load or create expert ratings
ratings_df = load_or_create_ratings()

# Load or create the participant order CSV
order_df, participant_ids = load_or_create_participant_order_csv()

st.title("Chair Design Rating Tool")

# Add rating scale legend at the top
st.markdown("""
    ### Rating Scale
    **1: Strongly Disagree | 2: Disagree | 3: Slightly Disagree | 4: Neutral | 5: Slightly Agree | 6: Agree | 7: Strongly Agree**
""")

# Input for Expert ID on the sidebar
st.sidebar.title("Expert ID")
expert_id = st.sidebar.text_input("Enter your Expert ID (e.g., E1, E2, ...):")

if expert_id:
    if not (expert_id.startswith("E") and expert_id[1:].isdigit()):
        st.sidebar.error(
            "Invalid Expert ID format. It should start with 'E' followed by a number (e.g., E1)."
        )
    else:
        # Get or create participant order for the expert
        expert_order, order_df = get_or_create_participant_order(
            expert_id, participant_ids, order_df
        )
        
        # Initialize session state for current participant index
        if "current_participant_index" not in st.session_state:
            # Find the first participant that doesn't have all 6 photos rated
            for i, participant_id in enumerate(expert_order):
                completed_ratings = ratings_df[
                    (ratings_df["expert_id"] == expert_id) & 
                    (ratings_df["participant_id"] == participant_id)
                ]
                if len(completed_ratings) < 6:  # 6 photos per participant
                    st.session_state["current_participant_index"] = i
                    break
            else:
                st.session_state["current_participant_index"] = 0
        
        current_index = st.session_state["current_participant_index"]
        current_participant_id = expert_order[current_index]
        
        # Calculate progress
        total_ratings_expected = len(participant_ids) * 6  # 6 photos per participant
        completed_ratings = ratings_df[ratings_df["expert_id"] == expert_id]
        completed_count = len(completed_ratings)
        
        st.sidebar.info(f"Your progress: {completed_count}/{total_ratings_expected}")
        
        # Style for layout
        st.markdown(
            """
            <style>
                .main .block-container {
                    max-width: 95%;
                    padding: 1rem;
                }
                .stButton > button {
                    width: 100%;
                }
                .rating-header {
                    text-align: center;
                    font-weight: bold;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        
        st.header(f"Participant ID: {current_participant_id}")
        
        # Create a 3x2 grid for photos - 3 on top, 3 on bottom
        row1_cols = st.columns(3)
        row2_cols = st.columns(3)
        
        # Display first row of photos (1-3)
        for i in range(3):
            photo_position = i + 1
            with row1_cols[i]:
                try:
                    st.image("screenshot.png", caption=f"Photo {photo_position}", use_column_width=True)
                except:
                    st.error(f"Photo {photo_position} not found")
        
        # Value ratings for all photos in row 1
        st.subheader("Value Ratings for Photos 1-3:")
        
        # Get existing values for photos 1-3
        existing_values = []
        for i in range(3):
            photo_position = i + 1
            existing_rating = ratings_df[
                (ratings_df["expert_id"] == expert_id) &
                (ratings_df["participant_id"] == current_participant_id) &
                (ratings_df["photo_position"] == photo_position)
            ]
            if not existing_rating.empty:
                existing_values.append(existing_rating["value"].values[0])
            else:
                existing_values.append(4)  # Default to middle value (4)
        
        # Create columns for value ratings
        value_cols = st.columns(3)
        value_ratings = []
        
        for i in range(3):
            with value_cols[i]:
                value = st.select_slider(
                    f"Photo {i+1} Value",
                    options=[1, 2, 3, 4, 5, 6, 7],
                    value=existing_values[i],
                    key=f"value_{current_participant_id}_{i+1}"
                )
                value_ratings.append(value)
        
        # Novelty ratings for all photos in row 1
        st.subheader("Novelty Ratings for Photos 1-3:")
        
        # Get existing novelty values for photos 1-3
        existing_novelties = []
        for i in range(3):
            photo_position = i + 1
            existing_rating = ratings_df[
                (ratings_df["expert_id"] == expert_id) &
                (ratings_df["participant_id"] == current_participant_id) &
                (ratings_df["photo_position"] == photo_position)
            ]
            if not existing_rating.empty:
                existing_novelties.append(existing_rating["novelty"].values[0])
            else:
                existing_novelties.append(4)  # Default to middle value (4)
        
        # Create columns for novelty ratings
        novelty_cols = st.columns(3)
        novelty_ratings = []
        
        for i in range(3):
            with novelty_cols[i]:
                novelty = st.select_slider(
                    f"Photo {i+1} Novelty",
                    options=[1, 2, 3, 4, 5, 6, 7],
                    value=existing_novelties[i],
                    key=f"novelty_{current_participant_id}_{i+1}"
                )
                novelty_ratings.append(novelty)
        
        # Save button for first row photos
        if st.button("Save Ratings for Photos 1-3"):
            all_rated = all(v is not None and n is not None for v, n in zip(value_ratings, novelty_ratings))
            if all_rated:
                for i in range(3):
                    ratings_df = save_or_update_ratings(
                        ratings_df,
                        expert_id,
                        current_participant_id,
                        i+1,
                        value_ratings[i],
                        novelty_ratings[i]
                    )
                st.success("Ratings saved for Photos 1-3!")
            else:
                st.warning("Please provide all ratings for Photos 1-3.")
        
        # Display second row of photos (4-6)
        for i in range(3):
            photo_position = i + 4
            with row2_cols[i]:
                try:
                    st.image("screenshot.png", caption=f"Photo {photo_position}", use_column_width=True)
                except:
                    st.error(f"Photo {photo_position} not found")
        
        # Value ratings for all photos in row 2
        st.subheader("Value Ratings for Photos 4-6:")
        
        # Get existing values for photos 4-6
        existing_values = []
        for i in range(3):
            photo_position = i + 4
            existing_rating = ratings_df[
                (ratings_df["expert_id"] == expert_id) &
                (ratings_df["participant_id"] == current_participant_id) &
                (ratings_df["photo_position"] == photo_position)
            ]
            if not existing_rating.empty:
                existing_values.append(existing_rating["value"].values[0])
            else:
                existing_values.append(4)  # Default to middle value (4)
        
        # Create columns for value ratings
        value_cols_row2 = st.columns(3)
        value_ratings_row2 = []
        
        for i in range(3):
            with value_cols_row2[i]:
                value = st.select_slider(
                    f"Photo {i+4} Value",
                    options=[1, 2, 3, 4, 5, 6, 7],
                    value=existing_values[i],
                    key=f"value_{current_participant_id}_{i+4}"
                )
                value_ratings_row2.append(value)
        
        # Novelty ratings for all photos in row 2
        st.subheader("Novelty Ratings for Photos 4-6:")
        
        # Get existing novelty values for photos 4-6
        existing_novelties = []
        for i in range(3):
            photo_position = i + 4
            existing_rating = ratings_df[
                (ratings_df["expert_id"] == expert_id) &
                (ratings_df["participant_id"] == current_participant_id) &
                (ratings_df["photo_position"] == photo_position)
            ]
            if not existing_rating.empty:
                existing_novelties.append(existing_rating["novelty"].values[0])
            else:
                existing_novelties.append(4)  # Default to middle value (4)
        
        # Create columns for novelty ratings
        novelty_cols_row2 = st.columns(3)
        novelty_ratings_row2 = []
        
        for i in range(3):
            with novelty_cols_row2[i]:
                novelty = st.select_slider(
                    f"Photo {i+4} Novelty",
                    options=[1, 2, 3, 4, 5, 6, 7],
                    value=existing_novelties[i],
                    key=f"novelty_{current_participant_id}_{i+4}"
                )
                novelty_ratings_row2.append(novelty)
        
        # Save button for second row photos
        if st.button("Save Ratings for Photos 4-6"):
            all_rated = all(v is not None and n is not None for v, n in zip(value_ratings_row2, novelty_ratings_row2))
            if all_rated:
                for i in range(3):
                    ratings_df = save_or_update_ratings(
                        ratings_df,
                        expert_id,
                        current_participant_id,
                        i+4,
                        value_ratings_row2[i],
                        novelty_ratings_row2[i]
                    )
                st.success("Ratings saved for Photos 4-6!")
            else:
                st.warning("Please provide all ratings for Photos 4-6.")
        
        # Navigation buttons at the bottom
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous Participant"):
                # Check if all ratings for current participant have been completed
                all_ratings_provided = True
                for photo_position in range(1, 7):
                    if len(ratings_df[
                        (ratings_df["expert_id"] == expert_id) &
                        (ratings_df["participant_id"] == current_participant_id) &
                        (ratings_df["photo_position"] == photo_position)
                    ]) == 0:
                        all_ratings_provided = False
                        break
                
                if all_ratings_provided or st.session_state["current_participant_index"] > 0:
                    st.session_state["current_participant_index"] = max(0, current_index - 1)
                    st.experimental_rerun()
        
        with col2:
            if st.button("Next Participant →"):
                # Check if all ratings for current participant have been completed
                all_ratings_provided = True
                for photo_position in range(1, 7):
                    if len(ratings_df[
                        (ratings_df["expert_id"] == expert_id) &
                        (ratings_df["participant_id"] == current_participant_id) &
                        (ratings_df["photo_position"] == photo_position)
                    ]) == 0:
                        all_ratings_provided = False
                        break
                
                if not all_ratings_provided:
                    st.warning("Please rate all 6 photos before proceeding to the next participant.")
                else:
                    if current_index < len(expert_order) - 1:
                        st.session_state["current_participant_index"] = current_index + 1
                        st.experimental_rerun()
                    else:
                        st.success("You have completed ratings for all participants!")
        
        # Add a download button for the CSV file at the bottom of the sidebar
        st.sidebar.markdown("---")
        if not ratings_df.empty:
            csv = ratings_df.to_csv(index=False).encode("utf-8")
            st.sidebar.download_button(
                label="Download Expert Ratings CSV",
                data=csv,
                file_name="expert_ratings.csv",
                mime="text/csv",
            )
        else:
            st.sidebar.write("No data to download yet.")
        
        # Display a scrollable table showing expert progress
        st.sidebar.markdown("### Expert Progress")
        progress_df = ratings_df.groupby("expert_id").size().reset_index(name="photos_rated")
        progress_df["photos_rated"] = progress_df["photos_rated"].astype(int)
        st.sidebar.dataframe(progress_df.set_index("expert_id"), height=200)
