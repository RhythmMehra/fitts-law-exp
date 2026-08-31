import streamlit as st
import random
import math
import time
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Fitts' Law Experiment",
    page_icon="🎯",
    layout="wide"
)


# ============================================================
# EXPERIMENT SETTINGS
# ============================================================

TOTAL_TRIALS = 100
PRACTICE_TRIALS = 10

DISTANCES = [100, 200, 300, 400]
SIZES = [20, 40, 60, 80]

DIRECTIONS = [
    "Left-to-Right",
    "Right-to-Left"
]


# ============================================================
# GOOGLE SHEETS CONNECTION
# ============================================================

@st.cache_resource
def connect_to_google_sheet():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    sheet = client.open(
        st.secrets["spreadsheet_name"]
    ).sheet1

    return sheet


# ============================================================
# INITIALIZE SESSION STATE
# ============================================================

defaults = {

    "started": False,

    "participant_id": "",

    "trial": 0,

    "practice": True,

    "distance": None,

    "size": None,

    "direction": None,

    "target_x": None,

    "target_y": None,

    "start_x": None,

    "start_y": None,

    "trial_start": None,

    "last_x": None,

    "last_y": None,

    "distance_traveled": 0.0,

    "errors": 0,

    "show_target": False,

    "finished": False
}


for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# GENERATE TRIAL
# ============================================================

def generate_trial():

    distance = random.choice(
        DISTANCES
    )

    size = random.choice(
        SIZES
    )

    direction = random.choice(
        DIRECTIONS
    )

    # Browser experiment area
    experiment_width = 900
    experiment_height = 500

    center_y = experiment_height // 2

    # Make sure starting position and target
    # both remain inside the experiment area.

    if direction == "Left-to-Right":

        target_x = random.randint(
            distance + 100,
            experiment_width - 100
        )

        start_x = target_x - distance

    else:

        target_x = random.randint(
            100,
            experiment_width - distance - 100
        )

        start_x = target_x + distance

    target_y = center_y

    return (
        distance,
        size,
        direction,
        target_x,
        target_y,
        start_x,
        target_y
    )


# ============================================================
# START NEW TRIAL
# ============================================================

def start_new_trial():

    (
        distance,
        size,
        direction,
        target_x,
        target_y,
        start_x,
        start_y
    ) = generate_trial()

    st.session_state.distance = distance
    st.session_state.size = size
    st.session_state.direction = direction

    st.session_state.target_x = target_x
    st.session_state.target_y = target_y

    st.session_state.start_x = start_x
    st.session_state.start_y = start_y

    st.session_state.trial_start = time.perf_counter()

    st.session_state.last_x = None
    st.session_state.last_y = None

    st.session_state.distance_traveled = 0.0

    st.session_state.errors = 0

    st.session_state.show_target = True


# ============================================================
# SAVE DATA
# ============================================================

def save_trial():

    sheet = connect_to_google_sheet()

    row = [

        st.session_state.participant_id,

        st.session_state.trial,

        st.session_state.distance,

        st.session_state.size,

        st.session_state.direction,

        round(
            st.session_state.elapsed_time,
            2
        ),

        round(
            st.session_state.distance_traveled,
            2
        ),

        st.session_state.errors

    ]

    sheet.append_row(
        row,
        value_input_option="USER_ENTERED"
    )


# ============================================================
# WELCOME SCREEN
# ============================================================

if not st.session_state.started:

    st.title("🎯 Fitts' Law Experiment")

    st.write(
        """
        This experiment investigates the relationship between
        target size, target distance and movement time.
        """
    )

    st.subheader(
        "Participant Information"
    )

    participant_id = st.text_input(
        "Enter your Participant ID",
        placeholder="Example: P01"
    )

    st.warning(
        "Please use the Participant ID provided to you by the researcher."
    )

    st.subheader(
        "Instructions"
    )

    st.markdown(
        """
        **You will complete:**

        - 10 practice trials
        - 100 experimental trials

        During every trial:

        1. A blue square will appear.
        2. Move your mouse toward it.
        3. Click the square as quickly and accurately as possible.
        4. Clicking outside the square counts as an error.

        Try to move directly toward the target rather than
        making unnecessary movements.

        Your practice trials will **not** be included in the
        final dataset.
        """
    )

    if st.button(
        "Start Experiment",
        type="primary"
    ):

        if participant_id.strip() == "":

            st.error(
                "Please enter a Participant ID."
            )

        else:

            st.session_state.participant_id = (
                participant_id.strip()
            )

            st.session_state.started = True

            st.session_state.practice = True

            st.rerun()


# ============================================================
# EXPERIMENT
# ============================================================

elif (
    st.session_state.started
    and not st.session_state.finished
):

    # --------------------------------------------------------
    # Start first trial
    # --------------------------------------------------------

    if not st.session_state.show_target:

        start_new_trial()

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    if st.session_state.practice:

        st.header("Practice Round")

        trial_text = (
            f"Practice Trial "
            f"{st.session_state.trial + 1}"
            f" / {PRACTICE_TRIALS}"
        )

    else:

        st.header("Experiment")

        trial_text = (
            f"Trial "
            f"{st.session_state.trial + 1}"
            f" / {TOTAL_TRIALS}"
        )

    st.write(trial_text)

    st.write(
        "Click the blue square as quickly and accurately as possible."
    )

    # --------------------------------------------------------
    # Experimental information
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Target Size",
            f"{st.session_state.size}px"
        )

    with col2:

        st.metric(
            "Distance",
            f"{st.session_state.distance}px"
        )

    with col3:

        st.metric(
            "Errors",
            st.session_state.errors
        )

    # --------------------------------------------------------
    # Target
    # --------------------------------------------------------

    target_x = st.session_state.target_x
    target_y = st.session_state.target_y
    size = st.session_state.size

    # Create target using HTML/CSS
    # Position is relative to experiment area.

    target_html = f"""
    <div style="
        position: relative;
        width: 900px;
        height: 500px;
        border: 2px solid #cccccc;
        background-color: #f7f7f7;
        margin: auto;
    ">

        <div style="
            position: absolute;
            left: {target_x - size/2}px;
            top: {target_y - size/2}px;
            width: {size}px;
            height: {size}px;
            background-color: #2864dc;
        ">
        </div>

    </div>
    """

    st.markdown(
        target_html,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Click button
    # --------------------------------------------------------

    st.write("")

    clicked = st.button(
        "CLICK TARGET",
        use_container_width=True
    )

    if clicked:

        elapsed_time = (
            time.perf_counter()
            -
            st.session_state.trial_start
        ) * 1000

        st.session_state.elapsed_time = (
            elapsed_time
        )

        # NOTE:
        # Streamlit's standard button cannot capture
        # the exact browser mouse coordinates.
        #
        # Therefore, the web version needs a small
        # JavaScript component for exact mouse tracking.
        #
        # This basic version is useful for testing,
        # but should NOT be used for final data collection.

        if st.session_state.practice:

            st.session_state.trial += 1

            st.session_state.show_target = False

            if (
                st.session_state.trial
                >= PRACTICE_TRIALS
            ):

                st.session_state.practice = False

                st.session_state.trial = 0

            st.rerun()

        else:

            save_trial()

            st.session_state.trial += 1

            st.session_state.show_target = False

            if (
                st.session_state.trial
                >= TOTAL_TRIALS
            ):

                st.session_state.finished = True

            st.rerun()


# ============================================================
# FINISHED
# ============================================================

else:

    st.success(
        "🎉 Experiment Complete!"
    )

    st.write(
        f"""
        Thank you for participating,
        **{st.session_state.participant_id}**.
        """
    )

    st.write(
        "Your 100 experimental trials have been recorded."
    )

    st.write(
        "You may now close this page."
    )
