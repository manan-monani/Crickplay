"""
Crickplay Live Match Simulator Dashboard

A Streamlit dashboard for controlling the live match simulation.
Allows users to:
- Select teams and players
- Configure match parameters
- Start/stop/pause simulation
- Monitor real-time streaming progress
- View pipeline status

Port: 2424 (as per PORTS registry)

Usage:
    streamlit run src/dashboard/match_control.py --server.port 2424
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.ports import PORTS, get_port, get_service_url, KAFKA_CONFIG
from src.synthetic.team_profiles import ALL_TEAMS, TeamProfile, get_all_team_names

# Constants
DATA_PATH = Path(__file__).parent.parent.parent / "Data"
T20_JSON_PATH = DATA_PATH / "t20s_male_json"
IPL_JSON_PATH = DATA_PATH / "ipl_male_json"
ODI_JSON_PATH = DATA_PATH / "odis_male_json"


# ============================================
# Helper Functions
# ============================================


@st.cache_data(ttl=300)
def load_available_matches(match_type: str = "t20s") -> List[Dict]:
    """Load metadata for all available matches."""
    path_map = {
        "t20s": T20_JSON_PATH,
        "ipl": IPL_JSON_PATH,
        "odis": ODI_JSON_PATH,
    }

    json_path = path_map.get(match_type, T20_JSON_PATH)
    matches = []

    if not json_path.exists():
        return matches

    for f in json_path.glob("*.json"):
        try:
            with open(f, "r") as file:
                data = json.load(file)
                info = data.get("info", {})
                matches.append(
                    {
                        "file": str(f),
                        "filename": f.name,
                        "teams": info.get("teams", []),
                        "date": info.get("dates", ["Unknown"])[0],
                        "venue": info.get("venue", "Unknown"),
                        "match_type": info.get("match_type", "T20"),
                        "outcome": info.get("outcome", {}),
                    }
                )
        except Exception as e:
            continue

    # Sort by date descending
    matches.sort(key=lambda x: x.get("date", ""), reverse=True)
    return matches


@st.cache_data(ttl=300)
def get_unique_teams(match_type: str = "t20s") -> List[str]:
    """Get all unique team names from historical data."""
    matches = load_available_matches(match_type)
    teams = set()
    for match in matches:
        for team in match.get("teams", []):
            teams.add(team)
    return sorted(list(teams))


def filter_matches_by_teams(matches: List[Dict], team1: str, team2: str) -> List[Dict]:
    """Filter matches to only include those between the two selected teams."""
    if not team1 and not team2:
        return matches

    filtered = []
    for match in matches:
        match_teams = set(match.get("teams", []))
        if team1 and team2:
            if {team1, team2} == match_teams:
                filtered.append(match)
        elif team1:
            if team1 in match_teams:
                filtered.append(match)
        elif team2:
            if team2 in match_teams:
                filtered.append(match)

    return filtered


def get_players_from_match(match_file: str) -> Dict[str, List[str]]:
    """Get player lists from a specific match file."""
    try:
        with open(match_file, "r") as f:
            data = json.load(f)
            return data.get("info", {}).get("players", {})
    except Exception:
        return {}


def save_simulation_config(config: Dict) -> str:
    """Save simulation configuration to a temp file."""
    config_path = (
        Path(__file__).parent.parent.parent / "src" / "dashboard" / ".sim_config.json"
    )
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return str(config_path)


def load_simulation_config() -> Optional[Dict]:
    """Load simulation configuration if exists."""
    config_path = (
        Path(__file__).parent.parent.parent / "src" / "dashboard" / ".sim_config.json"
    )
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return None


# ============================================
# Page Configuration
# ============================================

st.set_page_config(
    page_title="Crickplay - Live Match Simulator",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e3a5f;
        text-align: center;
        padding: 1rem;
        border-bottom: 3px solid #1e88e5;
        margin-bottom: 2rem;
    }
    .team-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1rem;
        color: white;
        text-align: center;
    }
    .status-running { color: #4caf50; font-weight: bold; }
    .status-stopped { color: #f44336; font-weight: bold; }
    .status-paused { color: #ff9800; font-weight: bold; }
    .metric-card {
        background: #f5f5f5;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .port-table { font-family: monospace; }
</style>
""",
    unsafe_allow_html=True,
)


# ============================================
# Sidebar - Configuration
# ============================================

st.sidebar.markdown("## 🎛️ Configuration")

# Data source selection
st.sidebar.markdown("### 📊 Data Source")
data_source = st.sidebar.radio(
    "Select data source:",
    ["Historical Matches", "Synthetic Generation"],
    help="Choose between replaying historical matches or generating synthetic data",
)

# Match type selection
if data_source == "Historical Matches":
    match_type = st.sidebar.selectbox(
        "Match Type",
        ["t20s", "ipl", "odis"],
        format_func=lambda x: {
            "t20s": "T20 International",
            "ipl": "IPL",
            "odis": "ODI",
        }[x],
    )
    available_teams = get_unique_teams(match_type)
else:
    available_teams = get_all_team_names()

# Simulation settings
st.sidebar.markdown("### ⚙️ Simulation Settings")

delay_mode = st.sidebar.selectbox(
    "Delivery Delay Mode",
    ["realistic", "fast", "instant", "custom"],
    help="How fast deliveries are published to Kafka",
)

if delay_mode == "custom":
    custom_delay = st.sidebar.slider(
        "Custom delay (seconds)", min_value=0.1, max_value=60.0, value=5.0, step=0.1
    )
else:
    custom_delay = {"realistic": 45.0, "fast": 2.0, "instant": 0.1}[  # Real T20 pace
        delay_mode
    ]

# Wicket delay
wicket_delay_multiplier = st.sidebar.slider(
    "Wicket delay multiplier",
    min_value=1.0,
    max_value=5.0,
    value=2.0,
    help="Extra delay after wickets (multiplied by base delay)",
)

# Kafka settings
st.sidebar.markdown("### 📨 Kafka Settings")
st.sidebar.text_input(
    "Bootstrap Server", value=KAFKA_CONFIG["bootstrap_servers"], disabled=True
)
st.sidebar.text_input("Topic", value=KAFKA_CONFIG["topic_deliveries"], disabled=True)


# ============================================
# Main Content
# ============================================

st.markdown(
    '<h1 class="main-header">🏏 Crickplay Live Match Simulator</h1>',
    unsafe_allow_html=True,
)

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🎯 Match Selection",
        "👥 Players & Teams",
        "🚀 Simulation Control",
        "📊 Port Registry",
    ]
)

# ============================================
# Tab 1: Match Selection
# ============================================
with tab1:
    st.markdown("### Select Teams & Match")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏏 Team 1")
        team1 = st.selectbox(
            "Select Team 1", options=[""] + available_teams, key="team1_select"
        )
        if team1 and team1 in ALL_TEAMS:
            profile = ALL_TEAMS[team1]
            st.markdown(
                f"""
            **ICC Ranking:** {profile.icc_ranking}  
            **Batting Style:** {profile.batting_style.value}  
            **Bowling Strength:** {profile.bowling_strength.value}  
            **Base Win Prob:** {profile.base_win_probability:.0%}
            """
            )

    with col2:
        st.markdown("#### 🏏 Team 2")
        # Filter out team1 from options
        team2_options = [""] + [t for t in available_teams if t != team1]
        team2 = st.selectbox("Select Team 2", options=team2_options, key="team2_select")
        if team2 and team2 in ALL_TEAMS:
            profile = ALL_TEAMS[team2]
            st.markdown(
                f"""
            **ICC Ranking:** {profile.icc_ranking}  
            **Batting Style:** {profile.batting_style.value}  
            **Bowling Strength:** {profile.bowling_strength.value}  
            **Base Win Prob:** {profile.base_win_probability:.0%}
            """
            )

    st.markdown("---")

    if data_source == "Historical Matches":
        st.markdown("### 📋 Available Matches")

        # Load and filter matches
        all_matches = load_available_matches(match_type)
        filtered_matches = filter_matches_by_teams(all_matches, team1, team2)

        st.info(
            f"Found **{len(filtered_matches)}** matches"
            + (f" between {team1} and {team2}" if team1 and team2 else "")
        )

        if filtered_matches:
            # Display matches in a table format
            match_data = []
            for m in filtered_matches[:50]:  # Limit display
                outcome = m.get("outcome", {})
                winner = outcome.get("winner", "No result")
                match_data.append(
                    {
                        "Date": m["date"],
                        "Teams": " vs ".join(m["teams"]),
                        "Venue": (
                            m["venue"][:30] + "..."
                            if len(m["venue"]) > 30
                            else m["venue"]
                        ),
                        "Winner": winner,
                        "File": m["filename"],
                    }
                )

            # Allow selection
            selected_idx = st.selectbox(
                "Select a match to simulate:",
                options=range(len(match_data)),
                format_func=lambda i: f"{match_data[i]['Date']} | {match_data[i]['Teams']} @ {match_data[i]['Venue']}",
            )

            if selected_idx is not None:
                selected_match = filtered_matches[selected_idx]
                st.session_state["selected_match"] = selected_match

                # Show match details
                with st.expander("Match Details", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Date", selected_match["date"])
                    with col2:
                        st.metric("Venue", selected_match["venue"][:20])
                    with col3:
                        winner = selected_match["outcome"].get("winner", "No result")
                        st.metric("Winner", winner)
        else:
            if team1 or team2:
                st.warning(
                    "No matches found for the selected team(s). Try different selections."
                )

    else:  # Synthetic Generation
        st.markdown("### 🎲 Synthetic Match Generation")
        st.info(
            "Synthetic data will be generated using Monte Carlo simulation based on team profiles."
        )

        if team1 and team2:
            from src.synthetic.team_profiles import calculate_head_to_head_probability

            if team1 in ALL_TEAMS and team2 in ALL_TEAMS:
                prob = calculate_head_to_head_probability(
                    ALL_TEAMS[team1], ALL_TEAMS[team2]
                )

                st.markdown(
                    f"""
                ### Head-to-Head Prediction
                
                **{team1}** win probability: **{prob:.1%}**  
                **{team2}** win probability: **{1-prob:.1%}**
                """
                )

                # Synthetic match config
                st.markdown("#### Match Configuration")
                venue = st.text_input("Venue", value="Synthetic Stadium")
                num_overs = st.selectbox("Overs", [20, 10, 5], index=0)

                st.session_state["synthetic_config"] = {
                    "team1": team1,
                    "team2": team2,
                    "venue": venue,
                    "overs": num_overs,
                    "type": "synthetic",
                }


# ============================================
# Tab 2: Players & Teams
# ============================================
with tab2:
    st.markdown("### 👥 Player Selection")

    if "selected_match" in st.session_state and data_source == "Historical Matches":
        match = st.session_state["selected_match"]
        players = get_players_from_match(match["file"])

        if players:
            for team_name, player_list in players.items():
                with st.expander(
                    f"🏏 {team_name} ({len(player_list)} players)", expanded=True
                ):
                    # Display as a grid
                    cols = st.columns(3)
                    for i, player in enumerate(player_list):
                        with cols[i % 3]:
                            st.checkbox(
                                player, value=True, key=f"player_{team_name}_{i}"
                            )
        else:
            st.warning("No player data available for this match.")

    elif data_source == "Synthetic Generation":
        st.info(
            "Synthetic matches use simulated player performance based on team profiles."
        )

        if team1 and team2:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"#### {team1}")
                st.markdown(
                    """
                Synthetic players will be generated with:
                - Batting averages based on team profile
                - Bowling economy based on team bowling strength
                - Strike rates following team batting style
                """
                )

            with col2:
                st.markdown(f"#### {team2}")
                st.markdown(
                    """
                Synthetic players will be generated with:
                - Batting averages based on team profile
                - Bowling economy based on team bowling strength
                - Strike rates following team batting style
                """
                )
    else:
        st.info("Select a match in the 'Match Selection' tab to view players.")


# ============================================
# Tab 3: Simulation Control
# ============================================
with tab3:
    st.markdown("### 🚀 Simulation Control")

    # Status display
    col1, col2, col3, col4 = st.columns(4)

    # Check simulation status from session state
    sim_status = st.session_state.get("simulation_status", "stopped")

    with col1:
        status_class = {
            "running": "status-running",
            "stopped": "status-stopped",
            "paused": "status-paused",
        }.get(sim_status, "status-stopped")
        st.markdown(
            f"**Status:** <span class='{status_class}'>{sim_status.upper()}</span>",
            unsafe_allow_html=True,
        )

    with col2:
        st.metric("Deliveries Sent", st.session_state.get("deliveries_sent", 0))

    with col3:
        st.metric("Current Over", st.session_state.get("current_over", "-"))

    with col4:
        st.metric("Delay (sec)", f"{custom_delay:.1f}")

    st.markdown("---")

    # Control buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        start_btn = st.button(
            "▶️ Start Simulation", type="primary", use_container_width=True
        )

    with col2:
        pause_btn = st.button("⏸️ Pause", use_container_width=True)

    with col3:
        stop_btn = st.button("⏹️ Stop", use_container_width=True)

    with col4:
        reset_btn = st.button("🔄 Reset", use_container_width=True)

    # Handle button clicks
    if start_btn:
        # Build configuration
        config = {
            "data_source": data_source,
            "delay": custom_delay,
            "wicket_delay_multiplier": wicket_delay_multiplier,
            "kafka": KAFKA_CONFIG,
            "timestamp": datetime.now().isoformat(),
        }

        if data_source == "Historical Matches" and "selected_match" in st.session_state:
            config["match_file"] = st.session_state["selected_match"]["file"]
            config["teams"] = st.session_state["selected_match"]["teams"]
        elif (
            data_source == "Synthetic Generation"
            and "synthetic_config" in st.session_state
        ):
            config.update(st.session_state["synthetic_config"])

        # Save config
        config_path = save_simulation_config(config)
        st.session_state["simulation_status"] = "running"
        st.session_state["simulation_config"] = config

        st.success(f"✅ Simulation configuration saved! Config file: `{config_path}`")
        st.info(
            """
        **To start the simulation, run:**
        ```bash
        python -m src.producer.simulator --config-file src/dashboard/.sim_config.json
        ```
        
        Or use the auto-pipeline orchestrator (when implemented).
        """
        )

    if stop_btn:
        st.session_state["simulation_status"] = "stopped"
        st.warning("Simulation stopped.")

    if pause_btn:
        if st.session_state.get("simulation_status") == "running":
            st.session_state["simulation_status"] = "paused"
            st.info("Simulation paused.")

    if reset_btn:
        for key in [
            "simulation_status",
            "deliveries_sent",
            "current_over",
            "selected_match",
            "synthetic_config",
            "simulation_config",
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun() if hasattr(st, "experimental_rerun") else st.rerun()

    # Pipeline Status
    st.markdown("---")
    st.markdown("### 📡 Pipeline Status")

    pipeline_info = """
    | Stage | Service | Port | Status |
    |-------|---------|------|--------|
    | 1. Producer | Kafka Producer | - | Ready |
    | 2. Broker | Apache Kafka | 29092 | Check Docker |
    | 3. Bronze | Kafka Sink | 8010 | Ready |
    | 4. Silver | Transformer | 8011 | Ready |
    | 5. Gold | Star Schema Builder | 8012 | Ready |
    | 6. API | FastAPI SSE | 8000 | Ready |
    """
    st.markdown(pipeline_info)

    st.markdown(
        """
    **Pipeline Flow:**
    ```
    Producer → Kafka → Bronze Layer → Silver Layer → Gold Layer
                          ↓
                     FastAPI SSE → Frontend
    ```
    """
    )


# ============================================
# Tab 4: Port Registry
# ============================================
with tab4:
    st.markdown("### 📊 Port Registry")
    st.markdown("All services and their assigned ports in the Crickplay project.")

    # Group ports by category
    categories = {
        "🔧 Infrastructure": [
            "ZOOKEEPER",
            "KAFKA_EXTERNAL",
            "KAFKA_INTERNAL",
            "POSTGRES",
            "REDIS",
            "KAFKA_UI",
        ],
        "🚀 Application": [
            "FASTAPI_MAIN",
            "FASTAPI_LIVE_MATCH",
            "STREAMLIT_DASHBOARD",
            "MLFLOW_UI",
            "RAY_SERVE",
        ],
        "📈 Monitoring": ["PROMETHEUS", "GRAFANA", "DBT_DOCS"],
        "🔄 Pipeline": ["BRONZE_SINK", "SILVER_TRANSFORMER", "GOLD_BUILDER"],
        "🖥️ Frontend": ["NEXTJS_FRONTEND"],
    }

    for category, services in categories.items():
        st.markdown(f"#### {category}")

        data = []
        for svc in services:
            if svc in PORTS:
                p = PORTS[svc]
                data.append(
                    {
                        "Service": svc,
                        "Port": p.port,
                        "Container Port": p.container_port or "-",
                        "Description": p.description,
                    }
                )

        if data:
            st.dataframe(data, use_container_width=True, hide_index=True)

        st.markdown("")

    # Quick port lookup
    st.markdown("---")
    st.markdown("#### 🔍 Quick Port Lookup")

    search_term = st.text_input("Search service name...")
    if search_term:
        results = {k: v for k, v in PORTS.items() if search_term.lower() in k.lower()}
        if results:
            for name, port_info in results.items():
                st.markdown(
                    f"**{name}**: Port `{port_info.port}` - {port_info.description}"
                )
        else:
            st.warning("No matching services found.")


# ============================================
# Footer
# ============================================
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: #666;'>
    <p>🏏 Crickplay - Cricket Analytics SaaS Platform | 
    Dashboard Port: 2424 | 
    <a href='http://localhost:8000/docs'>API Docs</a>
    </p>
</div>
""",
    unsafe_allow_html=True,
)


def run_dashboard():
    """Entry point for running the dashboard."""
    import subprocess

    subprocess.run(
        [
            "streamlit",
            "run",
            str(Path(__file__)),
            "--server.port",
            str(get_port("STREAMLIT_DASHBOARD")),
            "--server.headless",
            "true",
        ]
    )


if __name__ == "__main__":
    # When run directly, show instructions
    pass  # Streamlit handles this automatically
