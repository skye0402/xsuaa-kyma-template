import gradio as gr
from gradio import Blocks
import jwt
import logging, os, json
import sqlite3
from datetime import datetime

DBPATH_LOG = os.getenv("LOGIN_DB", "login_info.db") # User login timestamps
DBPATH_PRF = os.getenv("PREFR_DB", "user_prefr.db") # User preferences]
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
    jwt_encoded = request.headers.get("authorization", None)
    if jwt_encoded == None:
        state["jwt"] = None
        logging.info("Unauthorized call of application at start.")
        return [
            state,
            gr.update(visible=False),
            gr.update(value="Unauthorized.")
        ]
    state["jwt"] = decode_jwt(jwt_encoded)
    logging.debug(f'JWT data:\n{state["jwt"]}')
    usr = state["jwt"]
    log_user_login(DATABASES["log"], usr["user_name"], usr["given_name"],usr["family_name"],usr["email"])
    logging.debug("Login data logged in DB")
    return [
        state,
        gr.update(visible=True),
        gr.update(value=f'Welcome {state["jwt"]["given_name"]} {state["jwt"]["family_name"]}.')
    ]

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
                with gr.Column(scale=3, elem_id="column_right", visible=True) as column_right:
                    msg_box2 = gr.Textbox(
                        elem_id="msg_box",
                        show_label=False,
                        placeholder="Enter text and press ENTER",
                        container=False
                    )
        with gr.Tab(label="User Info", visible=True) as user_info_tab:
            login_count_df = gr.Dataframe(
                headers=["Username", "Full name", "Email", "Login Count"],
                datatype=["str", "str", "str", "number"],
                # row_count=5,
                col_count=(4, "fixed"),
            )
        user_info = gr.Markdown(value="Not logged in.", elem_id="user_info")
        test_view.load(set_user_data, [state], [state, main_screen, user_info])
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
    args["port"] = os.environ.get("HOSTPORT",80)
    
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