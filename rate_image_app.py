import streamlit as st
import pandas as pd
import os
import random

# Load participant data from JSON
participant_data = pd.read_json("participant_final_images.json").T


# Function to load or create expert_ratings.csv
def load_or_create_ratings():
    if os.path.exists("expert_ratings.csv"):
        ratings_df = pd.read_csv("expert_ratings.csv")
    else:
        ratings_df = pd.DataFrame(
            columns=[
                "expert_id",
                "final_image_value",
                "final_image_novelty",
                "final_image_feasibility",
                "participant_id",
            ]
        )
        ratings_df.to_csv("expert_ratings.csv", index=False)
    return ratings_df


# Function to save ratings to expert_ratings.csv
def save_ratings(ratings_df):
    ratings_df.to_csv("expert_ratings.csv", index=False)


# Function to load or create the image order CSV for all experts
def load_or_create_image_order_csv(participant_data):
    order_file = "expert_orders.csv"
    if os.path.exists(order_file):
        order_df = pd.read_csv(order_file)
    else:
        # Initialize an empty DataFrame if the file does not exist
        order_df = pd.DataFrame(columns=["expert_id"] + list(participant_data.index))
        order_df.to_csv(order_file, index=False)
    return order_df


# Function to get or create the randomized order for an expert
def get_or_create_image_order(expert_id, participant_data, order_df):
    if expert_id in order_df["expert_id"].values:
        # Load existing order
        expert_order = order_df[order_df["expert_id"] == expert_id].iloc[0, 1:].tolist()
    else:
        # Create a new randomized order
        expert_order = participant_data.index.to_list()
        random.shuffle(expert_order)
        new_row = pd.Series([expert_id] + expert_order, index=order_df.columns)
        order_df = pd.concat([order_df, pd.DataFrame([new_row])], ignore_index=True)
        save_image_order_csv(order_df)
    return expert_order, order_df


# Function to save the image order CSV
def save_image_order_csv(order_df):
    order_df.to_csv("expert_orders.csv", index=False)


# Function to save or update ratings
def save_or_update_ratings(
    ratings_df, expert_id, participant_id, value, novelty, feasibility=0
):
    existing_rating = ratings_df[
        (ratings_df["expert_id"] == expert_id)
        & (ratings_df["participant_id"] == participant_id)
    ]
    if not existing_rating.empty:
        # Update existing rating
        ratings_df.loc[
            existing_rating.index,
            ["final_image_value", "final_image_novelty", "final_image_feasibility"],
        ] = [value, novelty, feasibility]
    else:
        # Append new rating
        new_ratings = pd.DataFrame(
            {
                "expert_id": [expert_id],
                "final_image_value": [value],
                "final_image_novelty": [novelty],
                "final_image_feasibility": [feasibility],
                "participant_id": [participant_id],
            }
        )
        ratings_df = pd.concat([ratings_df, new_ratings], ignore_index=True)
    save_ratings(ratings_df)


# Load or create expert ratings
ratings_df = load_or_create_ratings()

# Load or create the image order CSV
order_df = load_or_create_image_order_csv(participant_data)

st.title("Chair Design Rating Tool")

# Input for Expert ID on the top left
st.sidebar.title("Expert ID")
expert_id = st.sidebar.text_input("Enter your Expert ID (e.g., E1, E2, ...):")

if expert_id:
    if not (expert_id.startswith("E") and expert_id[1:].isdigit()):
        st.sidebar.error(
            "Invalid Expert ID format. It should start with 'E' followed by a number (e.g., E1)."
        )
    else:
        # Check if the expert has already completed all ratings
        completed_ratings = ratings_df[ratings_df["expert_id"] == expert_id]
        if len(completed_ratings) == len(participant_data):
            st.success("You have already completed all ratings!")
            st.stop()

        # Get or create image order for the expert
        expert_order, order_df = get_or_create_image_order(
            expert_id, participant_data, order_df
        )

        # Determine the current position in the order
        if "current_index" not in st.session_state:
            st.session_state["current_index"] = len(completed_ratings)

        current_index = st.session_state["current_index"]
        current_participant_id = expert_order[current_index]

        # Calculate progress
        completed_count = len(completed_ratings)
        st.sidebar.info(f"Your progress: {completed_count}/{len(participant_data)}")

        # Retrieve participant information
        image_name = participant_data.loc[current_participant_id, "final_image"]
        participant_id = current_participant_id

        # Layout adjustments for full screen use
        st.markdown(
            """
            <style>
                .main .block-container {
                    max-width: 95%;
                    padding: 2rem;
                }
                .rating-container {
                    display: flex;
                    justify-content: space-between;
                }
                .nav-buttons {
                    display: flex;
                    justify-content: flex-end; /* Move buttons closer to the right */
                    padding-top: 10px;
                }
                .next-button {
                    margin-left: auto;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(
            [1, 1], gap="large"
        )  # Adjust column width for better space allocation

        # Display image on the left with more space
        with col1:
            st.image(
                f"final_images/{image_name}",
                caption=f"Participant ID: {participant_id}",
                use_column_width=True,
            )

        # Display questions and options on the right with more space
        with col2:
            st.markdown("### Please rate the following aspects of the chair design:")
            st.markdown(
                "**1: Strongly Disagree | 2: Disagree | 3: Slightly Disagree | 4: Neutral | 5: Slightly Agree | 6: Agree | 7: Strongly Agree**"
            )

            # Check for existing ratings in CSV for current participant
            existing_rating = ratings_df[
                (ratings_df["expert_id"] == expert_id)
                & (ratings_df["participant_id"] == participant_id)
            ]
            if not existing_rating.empty:
                value = existing_rating["final_image_value"].values[0]
                novelty = existing_rating["final_image_novelty"].values[0]
                feasibility = existing_rating["final_image_feasibility"].values[0]

                # Convert ratings to integers for the radio button index
                value_index = int(value) - 1 if pd.notna(value) else None
                novelty_index = int(novelty) - 1 if pd.notna(novelty) else None
                feasibility_index = (
                    int(feasibility) - 1 if pd.notna(feasibility) else None
                )
            else:
                # Initialize empty indices if no existing rating
                value_index = None
                novelty_index = None
                feasibility_index = None

            # Display radio buttons with existing values pre-selected if available, else empty
            value = (
                st.radio(
                    "Value: How well does this final image meet the client's requirements?",
                    options=[1, 2, 3, 4, 5, 6, 7],
                    index=value_index,
                    key=f"value_{current_participant_id}",
                    horizontal=True,
                )
                if value_index is not None
                else st.radio(
                    "Value: How well does this final image meet the client's requirements?",
                    options=[1, 2, 3, 4, 5, 6, 7],
                    index=None,
                    key=f"value_{current_participant_id}",
                    horizontal=True,
                )
            )

            novelty = (
                st.radio(
                    "Novelty: How innovative is this chair design?",
                    options=[1, 2, 3, 4, 5, 6, 7],
                    index=novelty_index,
                    key=f"novelty_{current_participant_id}",
                    horizontal=True,
                )
                if novelty_index is not None
                else st.radio(
                    "Novelty: How innovative is this chair design?",
                    options=[1, 2, 3, 4, 5, 6, 7],
                    index=None,
                    key=f"novelty_{current_participant_id}",
                    horizontal=True,
                )
            )

            feasibility = 0

            # Buttons directly below the questions
            st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
            left_col, right_col = st.columns([1, 1])
            with left_col:
                if st.button("← Previous"):
                    if value is None or novelty is None or feasibility is None:
                        st.warning(
                            "Please provide ratings for all three categories before proceeding."
                        )
                    elif st.session_state["current_index"] > 0:
                        # Save current ratings before going back
                        save_or_update_ratings(
                            ratings_df,
                            expert_id,
                            participant_id,
                            value,
                            novelty,
                            feasibility,
                        )
                        st.session_state["current_index"] -= 1
                        # No need to update query params, session state is enough

            with right_col:
                if st.button("Next →", key="next_button"):
                    if value is None or novelty is None or feasibility is None:
                        st.warning(
                            "Please provide ratings for all three categories before proceeding."
                        )
                    else:
                        # Save current ratings before moving forward
                        save_or_update_ratings(
                            ratings_df,
                            expert_id,
                            participant_id,
                            value,
                            novelty,
                            feasibility,
                        )

                        if (
                            st.session_state["current_index"]
                            < len(participant_data) - 1
                        ):
                            st.session_state["current_index"] += 1
                        else:
                            st.success("You have completed all ratings!")
                            st.stop()

            st.markdown("</div>", unsafe_allow_html=True)

        # Pop-up to inform about resuming or starting a new session
        if completed_count > 0:
            st.info(
                f"Welcome back, {expert_id}! Resuming your progress from {completed_count}/{len(participant_data)}."
            )
        else:
            st.info(f"New session started for {expert_id}.")

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
        progress_df = (
            ratings_df.groupby("expert_id").size().reset_index(name="images_rated")
        )
        progress_df["images_rated"] = progress_df["images_rated"].astype(
            int
        )  # Ensure the count is an integer
        st.sidebar.dataframe(
            progress_df.set_index("expert_id"), height=200
        )  # Set height for scrollable table
