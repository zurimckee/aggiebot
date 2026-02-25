
import streamlit as st
from google import genai as genai
from google.genai import types



SUGGESTIONS = {
    ":blue[:material/local_library:] What can AggieBot do?": (
        "What kind of questions can I ask you? "
    ),
    ":green[:material/database:] When does the financial aid office close?": (
        "Can you give me directions to the financial aid office?"
    ),
    ":orange[:material/multiline_chart:] What are some restaurants close to campus?": (
        "What are some good late night eats close to campus?"
    ),
    ":violet[:material/apparel:] When does registration start?": (
        "When does registration start?"
    ),
    ":red[:material/deployed_code:] What are some fun things to do in Greensboro?": (
        "Give me activities for people under 21 in Greensboro."
    ),
}





# Show title and description.
def config_page():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.image("assets/aggielogo.png")

    st.set_page_config(
        page_title="AggieBot",
        page_icon = "assets/favicon.ico",
        layout= "centered",
    )
    # Title row with clear button
    title_row = st.container(horizontal=True, vertical_alignment="bottom")
    with title_row:
        st.title("AggieBot 💬", text_alignment="left", width="stretch")
        st.write("Let's get started! Ask me anything about North Carolina A&T and I'll do my best to answer your question!")
        st.button("Clear",
            key="clear_button",
            icon=":material/refresh:",
            on_click=clear_conversation
        )
            

    
    




def clear_conversation():
    st.session_state.messages = []
    st.session_state.initial_question = None
    st.session_state.selected_suggestion = None



    

def config_api_key():
    """configures api key and basic text interface"""

    # Ask user for their Gemini API key via `st.text_input`.
    # Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
    # via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
    gemini_api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else st.text_input("Enter your Gemini API key", type="password")

    if gemini_api_key:
        #initializes client
        client = genai.Client(api_key = gemini_api_key)
        #makes sure that config is stored in session state so that it doesn't have to be recreated on every rerun.

        if "aggie_config" not in st.session_state:
            st.session_state.aggie_config = types.GenerateContentConfig(
                system_instruction = "You are AggieBot, an AI assistant meant to help students, " \
                "faculty, and staff of North Carolina Agricultural and Technical State University " \
                "with any questions that they may have about the university and its resources. " \
                "You should answer questions to the best of your ability, but if you don't know the answer, " \
                "say you don't know and suggest that the user contact the university directly for more information.",
                temperature=0.7,
                max_output_tokens = 1500,
                #in case of 503 errors retry up to 5 times with exponential backoff
                http_options = types.HttpOptions(
                    retry_options = types.HttpRetryOptions(
                        attempts = 5,
                        http_status_codes = [503]
                    )
                ),
                safety_settings =[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                    )
                ],
            )

        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        just_asked = "initial_question" in st.session_state and st.session_state.initial_question
        just_clicked = "selected_suggestion" in st.session_state and st.session_state.selected_suggestion
        has_history = len(st.session_state.messages) > 0

        # landing page w/o messages
        if not just_asked and not just_clicked and not has_history: 
            st.session_state.messages = []

            with st.container():
                st.chat_input("How can I help?", key="initial_question")

                selected_suggestion = st.pills(
                label="Examples",
                label_visibility="collapsed",
                options=SUGGESTIONS.keys(),
                key="selected_suggestion",
            )
                
            st.stop() #stop rendering here 


        user_message = st.chat_input("Follow up questions?")

        if not user_message:
            if just_asked:
                user_message = st.session_state.initial_question
            if just_clicked:
                user_message = SUGGESTIONS[st.session_state.selected_suggestion]
            
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if user_message:
                st.session_state.messages.append({"role": "user", "content": user_message})
                with st.chat_message("user"):
                    st.markdown(user_message)

              # Generate a response using the Gemini API.
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""

                    with st.spinner("AggieBot is thinking..."):
                        response = client.models.generate_content_stream(
                            model = "gemini-2.5-flash",
                            #switch back to gemini 3 preview when rate limit resets
                            contents = user_message,
                            config = st.session_state.aggie_config
                        )
            
                        for chunk in response:
                            full_response += chunk.text
                            message_placeholder.markdown(full_response)
                            
                        st.session_state.messages.append({"role" : "assistant", "content": full_response})

    else:
        st.warning("Please enter your Gemini API key to use the chatbot. You can get an API key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).")






if __name__ == "__main__":
    
    config_page()
    
    config_api_key()

        