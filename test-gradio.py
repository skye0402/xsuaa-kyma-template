import gradio as gr
from gradio import Blocks
import jwt
import logging, os, json
import sqlite3
from datetime import datetime

DBPATH_LOG = os.getenv("LOGIN_DB", "./db/login_info.db") # User login timestamps
DBPATH_PRF = os.getenv("PREFR_DB", "./db/user_prefr.db") # User preferences]
DATABASES = {}

block_css = """
gradio-app > .gradio-container {
    max-width: 100% !important;
    
}
.contain { display: flex !important; flex-direction: column !important; }
#component-0, #component-3, #component-10, #component-8  { height: 100% !important; }
#chat_window { flex-grow: 1 !important; overflow: auto !important;}
#column_left { height: 96vh !important; }
#buttons button {
    min-width: min(120px,100%);
}
footer {
    display:none !important
}
"""

logo_markdown = """### APJ Architecture & Platform Advisory
![Platform & Integration Labs](file/img/blue.svg)"""

# Custom HTML for the carousel
def get_carousel():
    carousel_html = """
    <!-- MDB JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/4.3.0/mdb.min.js"></script>
    <!-- Carousel wrapper -->
    <div id="carouselMaterialStyle" class="carousel slide carousel-fade" data-mdb-ride="carousel" data-mdb-carousel-init>
    <!-- Indicators -->
    <div class="carousel-indicators">
        <button type="button" data-mdb-target="#carouselMaterialStyle" data-mdb-slide-to="0" class="active" aria-current="true"
        aria-label="Slide 1"></button>
        <button type="button" data-mdb-target="#carouselMaterialStyle" data-mdb-slide-to="1" aria-label="Slide 2"></button>
        <button type="button" data-mdb-target="#carouselMaterialStyle" data-mdb-slide-to="2" aria-label="Slide 3"></button>
    </div>

    <!-- Inner -->
    <div class="carousel-inner rounded-5 shadow-4-strong">
        <!-- Single item -->
        <div class="carousel-item active">
        <img src="file/img/pic1.jpg" class="d-block w-100"
            alt="Sunset Over the City" />
        <div class="carousel-caption d-none d-md-block">
            <h5>First slide label</h5>
            <p>Nulla vitae elit libero, a pharetra augue mollis interdum.</p>
        </div>
        </div>

        <!-- Single item -->
        <div class="carousel-item">
        <img src="file/img/pic2.jpg" class="d-block w-100"
            alt="Canyon at Nigh" />
        <div class="carousel-caption d-none d-md-block">
            <h5>Second slide label</h5>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
        </div>
        </div>

        <!-- Single item -->
        <div class="carousel-item">
        <img src="file/img/pic3.jpg" class="d-block w-100"
            alt="Cliff Above a Stormy Sea" />
        <div class="carousel-caption d-none d-md-block">
            <h5>Third slide label</h5>
            <p>Praesent commodo cursus magna, vel scelerisque nisl consectetur.</p>
        </div>
        </div>
    </div>
    <!-- Inner -->

    <!-- Controls -->
    <button class="carousel-control-prev" type="button" data-mdb-target="#carouselMaterialStyle" data-mdb-slide="prev">
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Previous</span>
    </button>
    <button class="carousel-control-next" type="button" data-mdb-target="#carouselMaterialStyle" data-mdb-slide="next">
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Next</span>
    </button>
    </div>
    <!-- Carousel wrapper -->
    """
    return carousel_html #f"""<iframe style="width: 100%; height: 480px" srcdoc='{carousel_html}'></iframe>"""

def decode_jwt(jwt_str: str)->dict:
    token = jwt_str.split(" ")[1]
    try:
        decoded_payload = jwt.decode(token, options={"verify_signature": False})    
    except jwt.ExpiredSignatureError:
        print("The token has expired")
    except jwt.InvalidTokenError:
        print("The token is invalid")
    return decoded_payload

def set_user_data(state: gr.State, request: gr.Request):
    can_see_stats = False
    jwt_encoded = request.headers.get("authorization", None)
    logging.debug(f'JWT:\n{jwt_encoded}\n')
    # jwt_encoded = "Bearer eyJhbGciOiJSUzI1NiIsImprdSI6Imh0dHBzOi8vZGwtYXBqLmF1dGhlbnRpY2F0aW9uLmFwMjEuaGFuYS5vbmRlbWFuZC5jb20vdG9rZW5fa2V5cyIsImtpZCI6ImRlZmF1bHQtand0LWtleS0tOTE0MTIzNTc0IiwidHlwIjoiSldUIiwiamlkIjogImNFNTFrVjdidSswekVDOFJyeUZTMWZ0ckt5Y29QUXc2NDNmRWxHM2NBUjg9In0.eyJqdGkiOiIzMWUwMzA1NTk4NjM0NzcwOTEzMjIxYmUzMDFhZGVlMiIsImV4dF9hdHRyIjp7ImVuaGFuY2VyIjoiWFNVQUEiLCJzdWJhY2NvdW50aWQiOiJmZjE2Y2U0OS0wYWUxLTQ1ZjMtOWQwMy00ZDkwNThiMDIxNDYiLCJ6ZG4iOiJkbC1hcGoiLCJvaWRjSXNzdWVyIjoiaHR0cHM6Ly9hY2NvdW50cy5zYXAuY29tIn0sInhzLnN5c3RlbS5hdHRyaWJ1dGVzIjp7InhzLnJvbGVjb2xsZWN0aW9ucyI6WyJFbnRlcnByaXNlIE1lc3NhZ2luZyBBZG1pbmlzdHJhdG9yIiwiQXBwcm91dGVya3ltYSIsIkludGVybmFsIEdlbmVyYXRpdmUgQUkgUm9sZSIsIkVudGVycHJpc2UgTWVzc2FnaW5nIERldmVsb3BlciIsIlN1YmFjY291bnQgQWRtaW5pc3RyYXRvciIsIkVudGVycHJpc2UgTWVzc2FnaW5nIFN1YnNjcmlwdGlvbiBBZG1pbmlzdHJhdG9yIiwiQ29ubmVjdGl2aXR5IGFuZCBEZXN0aW5hdGlvbiBBZG1pbmlzdHJhdG9yIiwiRW50ZXJwcmlzZSBNZXNzYWdpbmcgRGlzcGxheSJdfSwiZ2l2ZW5fbmFtZSI6Ikd1bnRlciIsInhzLnVzZXIuYXR0cmlidXRlcyI6eyJGZWF0dXJlcyI6WyJzdGF0aXN0aWNzIl0sIk1vZGVscyI6WyIqIl19LCJmYW1pbHlfbmFtZSI6IkFsYnJlY2h0Iiwic3ViIjoiN2UwODFmMDgtN2UzOC00Mjc5LWIxMGQtZjQwMGU4YjNmZjJmIiwic2NvcGUiOlsiZ3VudGVyLXhzdWFhLWFwcCF0MTYxNC5GdWxsIiwib3BlbmlkIl0sImNsaWVudF9pZCI6InNiLWd1bnRlci14c3VhYS1hcHAhdDE2MTQiLCJjaWQiOiJzYi1ndW50ZXIteHN1YWEtYXBwIXQxNjE0IiwiYXpwIjoic2ItZ3VudGVyLXhzdWFhLWFwcCF0MTYxNCIsImdyYW50X3R5cGUiOiJhdXRob3JpemF0aW9uX2NvZGUiLCJ1c2VyX2lkIjoiN2UwODFmMDgtN2UzOC00Mjc5LWIxMGQtZjQwMGU4YjNmZjJmIiwib3JpZ2luIjoic2FwLmRlZmF1bHQiLCJ1c2VyX25hbWUiOiJndW50ZXIuYWxicmVjaHRAc2FwLmNvbSIsImVtYWlsIjoiZ3VudGVyLmFsYnJlY2h0QHNhcC5jb20iLCJhdXRoX3RpbWUiOjE3MDU4OTgwOTAsInJldl9zaWciOiIyZmE1YzVmNSIsImlhdCI6MTcwNTg5ODA5MSwiZXhwIjoxNzA1OTIxMjc2LCJpc3MiOiJodHRwczovL2RsLWFwai5hdXRoZW50aWNhdGlvbi5hcDIxLmhhbmEub25kZW1hbmQuY29tL29hdXRoL3Rva2VuIiwiemlkIjoiZmYxNmNlNDktMGFlMS00NWYzLTlkMDMtNGQ5MDU4YjAyMTQ2IiwiYXVkIjpbImd1bnRlci14c3VhYS1hcHAhdDE2MTQiLCJvcGVuaWQiLCJzYi1ndW50ZXIteHN1YWEtYXBwIXQxNjE0Il19.jEn6uFPVTpifoehPkpPsbjgCcr3624PGGAuUsTvDYIVpsr2Aumsu3X8RhtThTQk-QqDRNcj_sDx7QljCdI1fdGEtNDyCdAldWrVip_ciWMgUPs8n0wvt9z9hFLywX5erGjmMIyQBdH2K2kIY7pflw9HWbH7UdTdVAJQngGS1X9sLzgP0im_Mxa8yaCee_-F30jUk_nCkouOH-KeAZ1ex8LGt4bL3gr3zMY_H-ZkPJ31AX4vWvVCOl36yL6LJygCoe0mu2uFCQaVa6PsziRI20CGnxQzdURNEBBTa7ScVO2Mq_FafZmtF3OjxSQkRm_pzL7bTJRh_Rp_QhgXkwpsmxA"
    if jwt_encoded == None:
        state["jwt"] = None
        logging.info("Unauthorized call of application at start.")
        return [
            state,
            gr.update(visible=False),
            gr.update(value="Unauthorized."),
            gr.update(visible=can_see_stats)
        ]
    state["jwt"] = decode_jwt(jwt_encoded)
    logging.debug(f'JWT data:\n{state["jwt"]}')
    usr = state["jwt"]
    usr_attr = usr.get("xs.user.attributes", None)
    if usr_attr:
        can_see_stats = has_access(usr_attr, "Features", "statistics")
        logging.info(f'User {usr["user_name"]} has statistics access: {str(can_see_stats)}.')
    log_user_login(DATABASES["log"], usr["user_name"], usr["given_name"],usr["family_name"],usr["email"])
    logging.debug("Login data logged in DB")
    return [
        state,
        gr.update(visible=True),
        gr.update(value=f'Welcome {state["jwt"]["given_name"]} {state["jwt"]["family_name"]}.'),
        gr.update(visible=can_see_stats)
    ]
    
def has_access(user_attributes: dict, key: str, item: str) -> bool:
    """ Check if the user has access to a specific feature or model. """
    if key not in user_attributes:
        return False  # The key does not exist in the user attributes.
    if "*" in user_attributes[key]:
        return True  # The user has access to all items under this key.          
    return item in user_attributes[key]  # Check if the specific item is in the list.

def create_test_view()->Blocks:
    """ Build the view with Gradio blocks """
    with gr.Blocks(
            title="Architecture & Platform Advisory - Gradio Test Application for XSUAA", 
            theme=gr.themes.Soft(),
            css=block_css
        ) as test_view:
        state = gr.State({})
        with gr.Tab(label="Generative AI", visible=True) as genai_tab:
            with gr.Row(elem_id="overall_row", visible=False) as main_screen:
                with gr.Column(scale=10, elem_id="column_left"):
                    msg_box = gr.Textbox(
                        elem_id="msg_box",
                        show_label=False,
                        placeholder="Enter text and press ENTER",
                        container=False
                    )
                    logo_box = gr.Markdown(value=logo_markdown, elem_id="logo_box")
                    #carousel = gr.HTML(get_carousel())             
                with gr.Column(scale=3, elem_id="column_right", visible=True) as column_right:
                    msg_box2 = gr.Textbox(
                        elem_id="msg_box",
                        show_label=False,
                        placeholder="Enter text and press ENTER",
                        container=False
                    )
        with gr.Tab(label="User Info", visible=False) as user_info_tab:
            login_count_df = gr.Dataframe(
                headers=["Username", "Full name", "Email", "Login Count"],
                datatype=["str", "str", "str", "number"],
                # row_count=5,
                col_count=(4, "fixed"),
            )
        user_info = gr.Markdown(value="Not logged in.", elem_id="user_info")
        test_view.load(set_user_data, [state], [state, main_screen, user_info, user_info_tab])
        user_info_tab.select(set_df_data, [state], [login_count_df])
    return test_view
                
def connect_db():
    """ Creates or connects to login and user preference databases """
    # Connect to SQLite3 database for login information (it will be created if it doesn't exist)
    conn_log = sqlite3.connect(DBPATH_LOG, check_same_thread=False)
    cursor_log = conn_log.cursor()
    # Create a table to store user login information
    cursor_log.execute('''
        CREATE TABLE IF NOT EXISTS logins (
            id INTEGER PRIMARY KEY,
            user_name TEXT NOT NULL,
            given_name TEXT NOT NULL,
            family_name TEXT NOT NULL,
            email TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn_log.commit()
    
    # Connect to SQLite3 database for user preferences (it will be created if it doesn't exist)
    conn_userpref = sqlite3.connect(DBPATH_PRF, check_same_thread=False)
    cursor_userpref = conn_userpref.cursor()
    # Create a table to store user preferences
    cursor_userpref.execute('''
        CREATE TABLE IF NOT EXISTS usrpref (
            user_name TEXT PRIMARY KEY,
            preferences TEXT NOT NULL
        )
    ''')
    conn_userpref.commit()
    
    # Return both connections and cursors
    return (conn_log, cursor_log), (conn_userpref, cursor_userpref)

def log_user_login(db: dict, user_name: str, given_name: str, family_name: str, email: str):
    timestamp = datetime.now().isoformat()  # Get the current timestamp
    db["cursor"].execute('''
        INSERT INTO logins (user_name, given_name, family_name, email, timestamp) VALUES (?, ?, ?, ?, ?)
    ''', (user_name, given_name, family_name, email, timestamp))
    db["conn"].commit()
    
def log_user_preference(db: dict, user_name: str, preferences_json: dict):
    preferences = json.dumps(preferences_json)
    db["cursor"].execute('''
        INSERT INTO usrpref (user_name, preferences) VALUES (?, ?)
    ''', (user_name, preferences))
    db["conn"].commit()
    
def get_login_counts(db: dict):
    db["cursor"].execute('''
    SELECT user_name, given_name, family_name, email, COUNT(*) as count
    FROM logins
    GROUP BY user_name
    ORDER BY count DESC
    ''')
    return db["cursor"].fetchall()

def fetch_login_data():
    # Fetch login counts from the database
    login_data = get_login_counts(DATABASES["log"])
    
    # Format the data for the DataFrame
    formatted_data = []
    for user_name, given_name, family_name, email, count in login_data:
        full_name = f"{given_name} {family_name}"
        formatted_data.append([user_name, full_name, email, count])    
    return formatted_data

def set_df_data(state: dict):
    login_data = fetch_login_data()
    return login_data
                
def main():
    logging.basicConfig(level=logging.DEBUG)
    args = {}
    args["host"] = os.environ.get("HOSTNAME","0.0.0.0")
    args["port"] = os.environ.get("HOSTPORT",51010)
    
    # Connect to database
    (conn_log, cursor_log), (conn_userpref, cursor_userpref) = connect_db()
    global DATABASES
    DATABASES["log"] = {"conn": conn_log, "cursor": cursor_log}
    DATABASES["prf"] = {"conn": conn_userpref, "cursor": cursor_userpref}
    test_view = create_test_view()
    test_view.queue()
    test_view.launch(
        debug=True,
        show_api=False,
        server_name=args["host"],
        server_port=args["port"],
        allowed_paths=["./img"]
    )

if __name__ == "__main__":
    main()