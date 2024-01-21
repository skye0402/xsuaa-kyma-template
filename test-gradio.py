import gradio as gr
from gradio import Blocks
import jwt

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
        print(decoded_payload)
    except jwt.ExpiredSignatureError:
        print("The token has expired")
    except jwt.InvalidTokenError:
        print("The token is invalid")
    return decoded_payload

# def create_view()->Blocks:
#     """ Build the view with Gradio blocks """
#     with gr.Blocks(
#             title="Architecture & Platform Advisory - Generative AI Chat with S/4HANA Data", 
#             theme=gr.themes.Soft(),
#             css=block_css
#         ) as chat_view:

def predict(text, request: gr.Request):
    headers = request.headers
    host = request.client.host
    user_agent = request.headers["user-agent"]
    jwt_encoded = request.headers.get("authorization", None)
    jwt_data = decode_jwt(jwt_encoded)
    return {
        "ip": host,
        "user_agent": user_agent,
        "name": f'Welcome {jwt_data["given_name"]} {jwt_data["family_name"]}',
        "JWT": jwt_data
    }

def main():
    
    gr.Interface(predict, "text", "json").queue().launch(server_port=80, server_name="0.0.0.0")

if __name__ == "__main__":
    main()