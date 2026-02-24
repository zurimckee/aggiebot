
import streamlit as st
from google import genai as genai
from google.genai import types



# Show title and description.
def config_page():
    st.set_page_config(
        page_title="AggieBot",
        page_icon = "assets/favicon.ico",
        layout= "centered",
    )

    with st.container(border=True, width = "stretch"):
        st.space(5)
        st.header("Hey I'm AggieBot! 💬 ", divider= False, text_alignment="center")
        st.space(1)
        st.write("Let's get started! Ask me anything about North Carolina A&T and I'll do my best to answer your question!")


def buttons():
    st.button(
        label = "When does the financial aid office close?",
        type = "primary",
        disabled = False,
        width = "content",
        #on_click = lambda: st.session_state.update(prompt = "When does the financial aid office close?")
    )


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
            
        
        # Create a session state variable to store the chat messages. This ensures that the
        # messages persist across reruns.
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display the existing chat messages via `st.chat_message`.
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Create a chat input field to allow the user to enter a message. This will display
        # automatically at the bottom of the page.
        if prompt := st.chat_input("How can I help?"):

            # Store and display the current prompt.
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate a response using the Gemini API.

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                with st.spinner("Thinking..."):
        
                    response = client.models.generate_content_stream(
                        model = "gemini-3-flash-preview",
                        contents = prompt,
                        config = st.session_state.aggie_config
                    )
    
                for chunk in response:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response)
                
                st.session_state.messages.append({"role" : "assistant", "content": full_response})

    else:
        st.warning("Please enter your Gemini API key to use the chatbot. You can get an API key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).")






if __name__ == "__main__":
    with st.container(border=True, width="stretch"):
        config_page()
        buttons()
        #make_it_pretty()
        config_api_key()