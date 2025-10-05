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
        # Ensure the stage column exists
        if "stage" not in ratings_df.columns:
            ratings_df["stage"] = 1  # Default value
    else:
        ratings_df = pd.DataFrame(
            columns=[
                "expert_id",
                "participant_id",
                "stage",
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

# Function to save or update ratings for stage 1
def save_stage1_ratings(ratings_df, expert_id, participant_id, value, novelty):
    # Look for existing rating for this expert, participant and stage 1
    existing_rating = ratings_df[
        (ratings_df["expert_id"] == expert_id) & 
        (ratings_df["participant_id"] == participant_id) & 
        (ratings_df["stage"] == 1)
    ]
    
    if len(existing_rating) > 0:
        # Update existing rating
        ratings_df.loc[
            existing_rating.index,
            ["value", "novelty"],
        ] = [value, novelty]
    else:
        # Append new rating
        new_rating = pd.DataFrame(
            {
                "expert_id": [expert_id],
                "participant_id": [participant_id],
                "stage": [1],
                "value": [value],
                "novelty": [novelty],
            }
        )
        ratings_df = pd.concat([ratings_df, new_rating], ignore_index=True)
    
    save_ratings(ratings_df)
    return ratings_df

# Function to save or update ratings for stage 2
def save_stage2_ratings(ratings_df, expert_id, participant_id, value, novelty):
    # Look for existing rating for this expert, participant and stage 2
    existing_rating = ratings_df[
        (ratings_df["expert_id"] == expert_id) & 
        (ratings_df["participant_id"] == participant_id) & 
        (ratings_df["stage"] == 2)
    ]
    
    if len(existing_rating) > 0:
        # Update existing rating
        ratings_df.loc[
            existing_rating.index,
            ["value", "novelty"],
        ] = [value, novelty]
    else:
        # Append new rating
        new_rating = pd.DataFrame(
            {
                "expert_id": [expert_id],
                "participant_id": [participant_id],
                "stage": [2],
                "value": [value],
                "novelty": [novelty],
            }
        )
        ratings_df = pd.concat([ratings_df, new_rating], ignore_index=True)
    
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
            # Find the first participant that hasn't been rated
            for i, participant_id in enumerate(expert_order):
                completed_ratings = ratings_df[
                    (ratings_df["expert_id"] == expert_id) & 
                    (ratings_df["participant_id"] == participant_id)
                ]
                if len(completed_ratings) < 2:  # 2 stages per participant
                    st.session_state["current_participant_index"] = i
                    break
            else:
                st.session_state["current_participant_index"] = 0
        
        current_index = st.session_state["current_participant_index"]
        current_participant_id = expert_order[current_index]
        
        # Calculate progress
        total_ratings_expected = len(participant_ids) * 2  # 2 stages per participant
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
        
        # Display first row of photos (1-3) - Stage 1
        st.subheader("Stage 1")
        for i in range(3):
            photo_position = i + 1
            with row1_cols[i]:
                try:
                    st.image("screenshot.png", caption=f"Photo {photo_position}", use_container_width=True)
                except:
                    st.error(f"Photo {photo_position} not found")
        
        # Check for existing ratings for Stage 1
        stage1_ratings = ratings_df[
            (ratings_df["expert_id"] == expert_id) &
            (ratings_df["participant_id"] == current_participant_id) &
            (ratings_df["stage"] == 1)
        ]
        
        if len(stage1_ratings) > 0:
            stage1_value = stage1_ratings["value"].values[0]
            stage1_novelty = stage1_ratings["novelty"].values[0]
        else:
            stage1_value = 4  # Default to middle value (4)
            stage1_novelty = 4  # Default to middle value (4)
        
        # One value rating for the entire row (Stage 1)
        st.subheader("Value Rating for Stage 1:")
        stage1_value = st.slider(
            "Value",
            min_value=1,
            max_value=7,
            value=int(stage1_value),
            step=1,
            key=f"value_{current_participant_id}_stage1"
        )
        
        # One novelty rating for the entire row (Stage 1)
        st.subheader("Novelty Rating for Stage 1:")
        stage1_novelty = st.slider(
            "Novelty",
            min_value=1,
            max_value=7,
            value=int(stage1_novelty),
            step=1,
            key=f"novelty_{current_participant_id}_stage1"
        )
        
        # Save button for Stage 1
        if st.button("Save Ratings for Stage 1"):
            ratings_df = save_stage1_ratings(
                ratings_df,
                expert_id,
                current_participant_id,
                stage1_value,
                stage1_novelty
            )
            st.success("Ratings saved for Stage 1!")
        
        st.markdown("---")
        
        # Display second row of photos (4-6) - Stage 2
        st.subheader("Stage 2")
        for i in range(3):
            photo_position = i + 4
            with row2_cols[i]:
                try:
                    st.image("screenshot.png", caption=f"Photo {photo_position}", use_container_width=True)
                except:
                    st.error(f"Photo {photo_position} not found")
        
        # Check for existing ratings for Stage 2
        stage2_ratings = ratings_df[
            (ratings_df["expert_id"] == expert_id) &
            (ratings_df["participant_id"] == current_participant_id) &
            (ratings_df["stage"] == 2)
        ]
        
        if len(stage2_ratings) > 0:
            stage2_value = stage2_ratings["value"].values[0]
            stage2_novelty = stage2_ratings["novelty"].values[0]
        else:
            stage2_value = 4  # Default to middle value (4)
            stage2_novelty = 4  # Default to middle value (4)
        
        # One value rating for the entire row (Stage 2)
        st.subheader("Value Rating for Stage 2:")
        stage2_value = st.slider(
            "Value",
            min_value=1,
            max_value=7,
            value=int(stage2_value),
            step=1,
            key=f"value_{current_participant_id}_stage2"
        )
        
        # One novelty rating for the entire row (Stage 2)
        st.subheader("Novelty Rating for Stage 2:")
        stage2_novelty = st.slider(
            "Novelty",
            min_value=1,
            max_value=7,
            value=int(stage2_novelty),
            step=1,
            key=f"novelty_{current_participant_id}_stage2"
        )
        
        # Save button for Stage 2
        if st.button("Save Ratings for Stage 2"):
            ratings_df = save_stage2_ratings(
                ratings_df,
                expert_id,
                current_participant_id,
                stage2_value,
                stage2_novelty
            )
            st.success("Ratings saved for Stage 2!")
        
        # Navigation buttons at the bottom
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous Participant"):
                if current_index > 0:
                    st.session_state["current_participant_index"] = current_index - 1
                    st.experimental_rerun()
        
        with col2:
            if st.button("Next Participant →"):
                # Check if both stages for current participant have been rated
                stage1_rated = len(ratings_df[
                    (ratings_df["expert_id"] == expert_id) &
                    (ratings_df["participant_id"] == current_participant_id) &
                    (ratings_df["stage"] == 1)
                ]) > 0
                
                stage2_rated = len(ratings_df[
                    (ratings_df["expert_id"] == expert_id) &
                    (ratings_df["participant_id"] == current_participant_id) &
                    (ratings_df["stage"] == 2)
                ]) > 0
                
                if not (stage1_rated and stage2_rated):
                    st.warning("Please rate both stages before proceeding to the next participant.")
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
