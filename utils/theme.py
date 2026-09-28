import streamlit as st


# Fitness Analytics visual system

PRIMARY = "#FC5200"
PRIMARY_DARK = "#D93F00"

BACKGROUND = "#090B0E"
BACKGROUND_2 = "#0D1014"

SURFACE = "#15181D"
SURFACE_2 = "#1D2128"

TEXT = "#F7F8FA"
MUTED = "#A6ADB8"

BORDER = "rgba(255,255,255,.09)"


def apply_theme():

    st.markdown(
        f"""
        <style>

        :root {{
            --fitness-orange: {PRIMARY};
            --fitness-orange-dark: {PRIMARY_DARK};

            --fitness-background: {BACKGROUND};
            --fitness-background-2: {BACKGROUND_2};

            --fitness-surface: {SURFACE};
            --fitness-surface-2: {SURFACE_2};

            --fitness-text: {TEXT};
            --fitness-muted: {MUTED};

            --fitness-border: {BORDER};
        }}


        /* Main application */

        .stApp {{
            background:
                radial-gradient(
                    circle at 88% 4%,
                    rgba(252,82,0,.075),
                    transparent 25%
                ),
                linear-gradient(
                    135deg,
                    var(--fitness-background) 0%,
                    var(--fitness-background-2) 55%,
                    #11151A 100%
                );
        }}


        [data-testid="stHeader"] {{
            background: transparent;
        }}


        .block-container {{
            max-width: 1500px;
            padding-top: 1.15rem;
            padding-bottom: 3rem;
        }}


        /* Typography */

        h1,
        h2,
        h3 {{
            letter-spacing: -0.025em;
        }}


        h1 {{
            font-weight: 800;
        }}


        h2 {{
            font-weight: 750;
        }}


        h3 {{
            font-weight: 700;
        }}


        /* Section labels */

        .section-label {{
            color: #8D96A3;
            font-size: .70rem;
            font-weight: 800;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-top: 3px;
            margin-bottom: 8px;
        }}


        .section-heading {{
            font-size: 1.30rem;
            font-weight: 750;
            color: var(--fitness-text);
            margin-top: 1.15rem;
            margin-bottom: .65rem;
            letter-spacing: -.02em;
        }}


        /* KPI cards */

        [data-testid="stMetric"] {{
            background:
                linear-gradient(
                    145deg,
                    rgba(255,255,255,.055),
                    rgba(255,255,255,.022)
                );

            border: 1px solid var(--fitness-border);

            border-radius: 14px;

            padding: .85rem .95rem;

            min-height: 105px;

            box-shadow:
                0 8px 24px rgba(0,0,0,.14);

            transition:
                border-color .2s ease,
                transform .2s ease;
        }}


        [data-testid="stMetric"]:hover {{
            border-color: rgba(252,82,0,.28);
            transform: translateY(-1px);
        }}


        [data-testid="stMetricLabel"] {{
            color: var(--fitness-muted);
            font-size: .78rem;
            font-weight: 600;
        }}


        [data-testid="stMetricValue"] {{
            color: var(--fitness-text);
            font-weight: 800;
            letter-spacing: -.025em;
        }}


        /* Sidebar */

        section[data-testid="stSidebar"] {{
            background:
                linear-gradient(
                    180deg,
                    #16191F 0%,
                    #101318 100%
                );

            border-right:
                1px solid rgba(255,255,255,.07);
        }}


        section[data-testid="stSidebar"] .block-container {{
            padding-top: .85rem;
            padding-bottom: 1.5rem;
        }}


        /* Sidebar brand */

        .brand-card {{
            background:
                linear-gradient(
                    145deg,
                    rgba(252,82,0,.17),
                    rgba(252,82,0,.035)
                );

            border:
                1px solid rgba(252,82,0,.28);

            border-radius: 16px;

            padding: 14px 15px;

            margin-top: 12px;
            margin-bottom: 13px;

            box-shadow:
                0 10px 28px rgba(0,0,0,.16);
        }}


        .brand-row {{
            display: flex;
            align-items: center;
            gap: 11px;
        }}


        .brand-mark {{
            width: 40px;
            height: 40px;

            flex: 0 0 40px;

            border-radius: 12px;

            display: flex;
            align-items: center;
            justify-content: center;

            background:
                linear-gradient(
                    145deg,
                    #FC5200,
                    #D93F00
                );

            color: white;

            font-size: 22px;
            font-weight: 900;

            box-shadow:
                0 8px 22px rgba(252,82,0,.28);
        }}


        .brand-name {{
            font-size: 1.03rem;
            font-weight: 800;
            line-height: 1.05;
            color: white;
        }}


        .brand-kicker {{
            margin-top: 5px;

            font-size: .68rem;

            color: #FFB18E;

            letter-spacing: .10em;

            text-transform: uppercase;

            font-weight: 750;
        }}


        /* Sidebar navigation */

        section[data-testid="stSidebar"]
        [data-testid="stSidebarNav"] {{
            padding-bottom: .25rem;
        }}


        section[data-testid="stSidebar"]
        [data-testid="stSidebarNav"] a {{
            border-radius: 8px;
            margin: 2px 0;
            transition:
                background .15s ease,
                color .15s ease;
        }}


        section[data-testid="stSidebar"]
        [data-testid="stSidebarNav"] a:hover {{
            background: rgba(252,82,0,.09);
        }}


        section[data-testid="stSidebar"]
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background:
                linear-gradient(
                    90deg,
                    rgba(252,82,0,.18),
                    rgba(252,82,0,.07)
                );

            border-left:
                2px solid var(--fitness-orange);
        }}


        /* Sidebar section labels */

        .sidebar-section {{
            font-size: .69rem;

            text-transform: uppercase;

            letter-spacing: .11em;

            color: #858D99;

            font-weight: 800;

            margin: 15px 0 7px;
        }}


        /* Sidebar controls */

        section[data-testid="stSidebar"]
        div[data-baseweb="select"] > div {{
            background:
                rgba(255,255,255,.025);

            border-color:
                rgba(255,255,255,.07);

            border-radius: 9px;
        }}


        section[data-testid="stSidebar"]
        input {{
            background:
                rgba(255,255,255,.025);
        }}


        /* Hero */

        .hero {{
            position: relative;

            overflow: hidden;

            background:
                linear-gradient(
                    115deg,
                    rgba(252,82,0,.16),
                    rgba(255,255,255,.025) 55%,
                    rgba(255,255,255,.015)
                );

            border:
                1px solid rgba(252,82,0,.22);

            border-radius: 20px;

            padding: 24px 25px;

            margin-bottom: 18px;

            box-shadow:
                0 14px 35px rgba(0,0,0,.12);
        }}


        .hero:after {{
            content: "";

            position: absolute;

            width: 240px;
            height: 240px;

            border-radius: 50%;

            right: -105px;
            top: -135px;

            background:
                rgba(252,82,0,.13);

            filter: blur(2px);

            pointer-events: none;
        }}


        .hero-kicker {{
            color: #FF9D73;

            font-size: .70rem;

            font-weight: 800;

            letter-spacing: .12em;

            text-transform: uppercase;

            margin-bottom: 7px;
        }}


        .hero-title {{
            font-size: 2.25rem;

            font-weight: 850;

            line-height: 1.05;

            color: white;

            margin-bottom: 8px;
        }}


        .hero-subtitle {{
            color: #C4CAD2;

            max-width: 900px;

            font-size: .96rem;

            line-height: 1.55;
        }}


        /* Decision cards */

        .decision-card {{
            background:
                linear-gradient(
                    145deg,
                    rgba(255,255,255,.045),
                    rgba(255,255,255,.018)
                );

            border:
                1px solid rgba(255,255,255,.08);

            border-left:
                3px solid var(--fitness-orange);

            border-radius: 12px;

            padding: 13px 15px;

            margin-bottom: 10px;

            min-height: 78px;
        }}


        .decision-title {{
            color: #FF9D73;

            font-size: .76rem;

            font-weight: 800;

            text-transform: uppercase;

            letter-spacing: .07em;

            margin-bottom: 5px;
        }}


        .decision-text {{
            color: #D3D7DE;

            font-size: .90rem;

            line-height: 1.45;
        }}


        /* Data context */

        .data-context {{
            margin-top: 17px;

            padding: 12px 14px;

            border-radius: 10px;

            background: rgba(255,255,255,.025);

            border:
                1px solid rgba(255,255,255,.07);

            color: #929AA6;

            font-size: .78rem;

            line-height: 1.55;
        }}


        /* Charts */

        [data-testid="stPlotlyChart"] {{
            border-radius: 12px;
            overflow: hidden;
        }}


        /* Buttons */

        .stButton > button[kind="primary"] {{
            background: var(--fitness-orange);

            border-color: var(--fitness-orange);

            color: white;
        }}


        .stButton > button[kind="primary"]:hover {{
            background: var(--fitness-orange-dark);

            border-color: var(--fitness-orange-dark);
        }}


        /* Sidebar footer */

        .sidebar-footer {{
            margin-top: 18px;

            padding-top: 13px;

            border-top:
                1px solid rgba(255,255,255,.08);

            color: #7F8793;

            font-size: .70rem;

            line-height: 1.55;
        }}


        .sidebar-footer strong {{
            color: #A8AFBA;
        }}


        /* Divider */

        hr {{
            border-color:
                rgba(255,255,255,.08);
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand():

    st.sidebar.markdown(
        """
        <div class="brand-card">

            <div class="brand-row">

                <div class="brand-mark">
                    ⌁
                </div>

                <div>

                    <div class="brand-name">
                        Fitness Analytics
                    </div>

                    <div class="brand-kicker">
                        Activity Intelligence
                    </div>

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer():

    st.sidebar.markdown(
        """
        <div class="sidebar-footer">

            <strong>Fitness Analytics</strong><br>

            Behavioral intelligence platform<br>

            Fitness & wellness decision support<br><br>

            Independent analytics application<br>

            <strong>Not affiliated with Strava</strong>

        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(
    title,
    subtitle,
    kicker="FITNESS ANALYTICS",
):

    st.markdown(
        f"""
        <div class="hero">

            <div class="hero-kicker">
                {kicker}
            </div>

            <div class="hero-title">
                {title}
            </div>

            <div class="hero-subtitle">
                {subtitle}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )