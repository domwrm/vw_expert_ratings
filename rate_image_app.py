import streamlit as st
import pandas as pd
import os
import random
import glob

# Set page config
st.set_page_config(layout="wide", page_title="Chair Design Rating Tool")

# Function to get participant IDs from the imgs directory
def get_participant_ids():
    if os.path.exists("imgs"):
        # Get all directories in the imgs folder
        participant_ids = [os.path.basename(d) for d in glob.glob("imgs/*") if os.path.isdir(d)]
        return participant_ids
    else:
        return []  # Return empty list if the imgs directory doesn't exist

# Function to load or create expert_ratings.csv
def load_or_create_ratings():
    if os.path.exists("expert_ratings.csv"):
        ratings_df = pd.read_csv("expert_ratings.csv")
        # Ensure required columns exist
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
def load_or_create_participant_order_csv(participant_ids):
    order_file = "expert_orders.csv"
    
    if os.path.exists(order_file):
        order_df = pd.read_csv(order_file)
    else:
        # Initialize an empty DataFrame if the file does not exist
        order_df = pd.DataFrame(columns=["expert_id"] + participant_ids)
        order_df.to_csv(order_file, index=False)
    return order_df

# Function to get or create the randomized order for an expert
def get_or_create_participant_order(expert_id, participant_ids, order_df):
    # Return empty list if no participant IDs are available
    if not participant_ids:
        return [], order_df
        
    if expert_id in order_df["expert_id"].values:
        # Load existing order
        expert_order = order_df[order_df["expert_id"] == expert_id].iloc[0, 1:].tolist()
        # Filter to only include existing participant IDs and remove NaN values
        expert_order = [str(p) for p in expert_order if str(p) != 'nan' and str(p) in participant_ids]
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

# Function to get image paths for a participant and stage
def get_image_paths(participant_id, stage):
    stage_folder = f"phase{stage}"
    image_dir = os.path.join("imgs", participant_id, stage_folder)
    
    if os.path.exists(image_dir):
        # Get all image files in the directory
        image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        image_paths = [os.path.join(image_dir, f) for f in image_files]
        return image_paths
    else:
        return []

# Function to save or update phase rating (one rating per phase)
def save_phase_rating(ratings_df, expert_id, participant_id, stage, value, novelty):
    # Look for existing rating for this expert, participant, and stage
    existing_rating = ratings_df[
        (ratings_df["expert_id"] == expert_id) & 
        (ratings_df["participant_id"] == participant_id) &
        (ratings_df["stage"] == stage)
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
                "stage": [stage],
                "value": [value],
                "novelty": [novelty],
            }
        )
        ratings_df = pd.concat([ratings_df, new_rating], ignore_index=True)
    
    save_ratings(ratings_df)
    return ratings_df

# Get participant IDs from directory
participant_ids = get_participant_ids()
if not participant_ids:
    participant_ids = [
        "15114939", "1523377", "1972680", "2740476", "2774750",
        "3111213", "311213", "3577395", "40384189", "4135402",
        "4573618", "4723488", "5385968", "5450966", "5480107",
        "5595285", "5646401", "6731446", "6903974", "7935248",
        "8080071", "8412880", "8463739", "8506151", "8757727", "8910228"
    ]

# Convert all participant IDs to strings to avoid type issues
participant_ids = [str(pid) for pid in participant_ids]

# Load or create expert ratings
ratings_df = load_or_create_ratings()

# Load or create the participant order CSV
order_df = load_or_create_participant_order_csv(participant_ids)

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
        
        # Check if expert_order is empty
        if not expert_order:
            st.error("No participants found. Please check your imgs directory structure.")
            st.stop()
        
        # Initialize session state for current participant index
        if "current_participant_index" not in st.session_state:
            # Start at the first participant
            st.session_state["current_participant_index"] = 0
        
        current_index = st.session_state["current_participant_index"]
        
        # Make sure current_index is valid
        if current_index >= len(expert_order):
            current_index = 0
            st.session_state["current_participant_index"] = 0
        
        current_participant_id = expert_order[current_index]
        
        # Calculate progress
        total_participants = len(expert_order)
        
        st.sidebar.info(f"Viewing participant {current_index + 1} of {total_participants}")
        
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
                .small-text {
                    font-size: 0.8rem;
                }
                .stImage {
                    margin-bottom: 0;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        
        st.header(f"Participant ID: {current_participant_id}")
        
        # Display both phases in a single view
        # Phase 1 Section
        st.subheader("Phase 1 Images")
        stage1_images = get_image_paths(current_participant_id, 1)
        
        if not stage1_images:
            st.warning(f"No images found for Participant {current_participant_id} in Phase 1.")
            stage1_images = ["screenshot.png"] * 3
        
        # Make sure we have at least 3 images (or use duplicates if needed)
        while len(stage1_images) < 3:
            stage1_images.append(stage1_images[0] if stage1_images else "screenshot.png")
        
        # Randomly select 3 images if there are more than 3
        if len(stage1_images) > 3:
            if f"stage1_images_{current_participant_id}" not in st.session_state:
                selected_images = random.sample(stage1_images, 3)
                st.session_state[f"stage1_images_{current_participant_id}"] = selected_images
            stage1_images = st.session_state[f"stage1_images_{current_participant_id}"]
        
        # Display Phase 1 images in a 3-column layout
        col1, col2, col3 = st.columns(3)
        for i, (image_path, col) in enumerate(zip(stage1_images[:3], [col1, col2, col3])):
            with col:
                try:
                    st.image(image_path, caption=f"Phase 1 - Image {i+1}", use_container_width=True)
                except:
                    st.error(f"Could not load image {image_path}")
        
        # Phase 1 Ratings (single rating for the entire phase)
        existing_phase1_rating = ratings_df[
            (ratings_df["expert_id"] == expert_id) &
            (ratings_df["participant_id"] == current_participant_id) &
            (ratings_df["stage"] == 1)
        ]
        
        phase1_value = 4 if len(existing_phase1_rating) == 0 else int(existing_phase1_rating["value"].values[0])
        phase1_novelty = 4 if len(existing_phase1_rating) == 0 else int(existing_phase1_rating["novelty"].values[0])
        
        # Value slider spanning full width
        st.markdown('<p class="small-text">Value: How well does this final image meet the client\'s requirements?</p>', unsafe_allow_html=True)
        phase1_value_rating = st.slider(
            "Phase 1 Value",
            min_value=1,
            max_value=7,
            value=phase1_value,
            step=1,
            key=f"value_phase1_{current_participant_id}",
            label_visibility="collapsed"
        )
        
        # Novelty slider spanning full width
        st.markdown('<p class="small-text">Novelty: How innovative is this chair design?</p>', unsafe_allow_html=True)
        phase1_novelty_rating = st.slider(
            "Phase 1 Novelty",
            min_value=1,
            max_value=7,
            value=phase1_novelty,
            step=1,
            key=f"novelty_phase1_{current_participant_id}",
            label_visibility="collapsed"
        )
        
        # Save button
        if st.button("Save Phase 1 Ratings", key=f"save_phase1_{current_participant_id}"):
            ratings_df = save_phase_rating(
                ratings_df,
                expert_id,
                current_participant_id,
                1,
                phase1_value_rating,
                phase1_novelty_rating
            )
            st.success("Phase 1 ratings saved!")
        
        st.markdown("---")
        
        # Phase 2 Section
        st.subheader("Phase 2 Images")
        stage2_images = get_image_paths(current_participant_id, 2)
        
        if not stage2_images:
            st.warning(f"No images found for Participant {current_participant_id} in Phase 2.")
            stage2_images = ["screenshot.png"] * 3
        
        # Make sure we have at least 3 images (or use duplicates if needed)
        while len(stage2_images) < 3:
            stage2_images.append(stage2_images[0] if stage2_images else "screenshot.png")
        
        # Randomly select 3 images if there are more than 3
        if len(stage2_images) > 3:
            if f"stage2_images_{current_participant_id}" not in st.session_state:
                selected_images = random.sample(stage2_images, 3)
                st.session_state[f"stage2_images_{current_participant_id}"] = selected_images
            stage2_images = st.session_state[f"stage2_images_{current_participant_id}"]
        
        # Display Phase 2 images in a 3-column layout
        col1, col2, col3 = st.columns(3)
        for i, (image_path, col) in enumerate(zip(stage2_images[:3], [col1, col2, col3])):
            with col:
                try:
                    st.image(image_path, caption=f"Phase 2 - Image {i+1}", use_container_width=True)
                except:
                    st.error(f"Could not load image {image_path}")
        
        # Phase 2 Ratings (single rating for the entire phase)
        existing_phase2_rating = ratings_df[
            (ratings_df["expert_id"] == expert_id) &
            (ratings_df["participant_id"] == current_participant_id) &
            (ratings_df["stage"] == 2)
        ]
        
        phase2_value = 4 if len(existing_phase2_rating) == 0 else int(existing_phase2_rating["value"].values[0])
        phase2_novelty = 4 if len(existing_phase2_rating) == 0 else int(existing_phase2_rating["novelty"].values[0])
        
        # Value slider spanning full width
        st.markdown('<p class="small-text">Value: How well does this final image meet the client's requirements?</p>', unsafe_allow_html=True)
        phase2_value_rating = st.slider(
            "Phase 2 Value",
            min_value=1,
            max_value=7,
            value=phase2_value,
            step=1,
            key=f"value_phase2_{current_participant_id}",
            label_visibility="collapsed"
        )
        
        # Novelty slider spanning full width
        st.markdown('<p class="small-text">Novelty: How innovative is this chair design?</p>', unsafe_allow_html=True)
        phase2_novelty_rating = st.slider(
            "Phase 2 Novelty",
            min_value=1,
            max_value=7,
            value=phase2_novelty,
            step=1,
            key=f"novelty_phase2_{current_participant_id}",
            label_visibility="collapsed"
        )
        
        # Save button
        if st.button("Save Phase 2 Ratings", key=f"save_phase2_{current_participant_id}"):
            ratings_df = save_phase_rating(
                ratings_df,
                expert_id,
                current_participant_id,
                2,
                phase2_value_rating,
                phase2_novelty_rating
            )
            st.success("Phase 2 ratings saved!")
        
        # Navigation buttons at the bottom
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous Participant"):
                if current_index > 0:
                    st.session_state["current_participant_index"] = current_index - 1
                    st.rerun()
        
        with col2:
            if st.button("Next Participant →"):
                if current_index < len(expert_order) - 1:
                    st.session_state["current_participant_index"] = current_index + 1
                    st.rerun()
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
