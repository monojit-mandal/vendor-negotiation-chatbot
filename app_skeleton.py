import streamlit as st
from streamlit_chat import message
from streamlit_card import card

def login_page():
    st.markdown(
        """
        <style>
        /* Center the login form */
        .login-container {
            width: 700px;
            padding: 30px;
            background-color: #f4f4f4;
            border-radius: 12px;
            text-align: center;
            margin: auto;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            position: relative;
        }
        /* Logo styling inside the container */
        .logo-container {
            position: absolute;
            top: -40px;
            left: 50%;
            transform: translateX(-50%);
            background: #fff;
            padding: 10px;
            border-radius: 50%;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        }
        .login-container h1 {
            font-size: 24px;
            margin-bottom: 20px;
            color: #333;
        }
        /* Style input fields */
        .stTextInput>div>div>input {
            border: 2px solid #BEBEBE !important;
            border-radius: 8px !important;
        }
        /* Style the login button */
        .stButton {
            display: flex;
            justify-content: center;
        }
        /* Style the login button */
        .stButton > button {
            background-color: #A100FF !important; /* Purple */
            color: white !important;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 16px;
            border: none;
        }
        .stButton > button:hover {
            background-color: #9932CC !important; /* Lighter Purple on Hover */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Login container with logo inside
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Company Logo
    st.markdown('<div class="logo-container"><img src="https://i.postimg.cc/zf0KSW8n/Accenture-Logo.png" width="80"></div>', unsafe_allow_html=True)
    
    # Login Title
    st.title("Login")

    # Username & Password Fields
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # Login Button
    if st.button("Login"):
        if username and password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Please enter both username and password.")
    
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="_Guided Chatbot_", layout="wide")

    # Add Custom CSS to Change Button Color to Purple
    st.markdown(
        """
        <style>
        .stButton > button {
            background-color: #A100FF !important; /* Purple */
            color: white !important;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 16px;
            border: none;
        }
        .stButton > button:hover {
            background-color: #9932CC !important; /* Lighter Purple on Hover */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Layout with three columns: Sidebar, Chat, Summary
    col1, col2, col3 = st.columns([1.2, 3, 1.2])  # Sidebar, Chatbot, Summary

    # Left Sidebar - Navigation (Grey)
    with col1:
        st.markdown(
            """
            <div class="sidebar-logo">
                <img src="https://i.postimg.cc/zf0KSW8n/Accenture-Logo.png" style="width: 120px; height: auto;"/>
                <span class="sidebar-logo-text"> </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div style="background-color: #f1f3f4; padding: 15px; border-radius: 8px;">
                <h3 style="color: black;">Navigation</h3>
                <ul style="list-style: none; padding: 0;">
                    <li>🟣✔ <b>Introduction</b></li>
                    <li>🟣✔ Mutual interests</li>
                    <li>🟣✔ Contract Terms Discussion</li>
                    <li>🟣✔ Summary</li>
                    <li><b style="color:rgb(182, 53, 229);">🟣✔ Conclusion</b></li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Chatbot UI
    with col2:
        st.markdown("<h1><em>Guided Chatbot</em></h1>", unsafe_allow_html=True)

        # Step 0: Start Button
        if st.session_state.step == 0:
             with st.expander("📌 Start Chatbot", expanded=True):
                st.markdown(
                    """
                    <div style="font-size: 12px; line-height: 1.2;">
                        **💰 Price/unit:** $100 | **Qty:** 10,000<br>
                        **📦 Bundling:** No<br>
                        **💳 Payment:** NET10 (No NET30)<br>
                        **🚚 Delivery:** 7 days<br>
                        **📆 Contract:** 1 yr (renewable)<br>
                        **💰 Rebate:** 1% on 11K+ units<br>
                        **🛠️ Warranty:** 1 yr std, 3 yrs +$5/unit<br>
                        **🌍 Incoterms:** FOB (Buyer handles customs & delivery)
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button('Click Proceed'):
                    print('Hello')
                # st.markdown(
                #     """ 
                #     <div style="display: flex; justify-content: center;">
                #         <button style="padding: 10px 20px; font-size: 14px; border-radius: 5px; 
                #                         background-color: #007BFF; color: white; border: none; 
                #                         cursor: pointer;" onclick="window.location.reload();">
                #             Click to Proceed
                #         </button>
                #     </div>
                #     """,
                #     unsafe_allow_html=True,
                # )

        # Display chat history
        for msg in st.session_state.messages:
            if msg["is_user"]:
                message(msg["content"], is_user=True)
            else:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="https://i.postimg.cc/zf0KSW8n/Accenture-Logo.png" width="40" style="border-radius: 50%; margin-right: 10px;">
                        <div style="background-color: #F1F3F4; color: black; padding: 12px; border-radius: 12px; max-width: 70%;">
                            {msg["content"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Step 1: Select Topic
        if st.session_state.step == 1:
            options = ["Technology", "Health", "Education", "Finance"]
            topic = st.radio("Choose a topic:", options, key="topic")

            if st.button("Next"):
                st.session_state.messages.append({"content": f"You chose {topic}.", "is_user": True})
                st.session_state.messages.append({"content": "Let's dive deeper.", "is_user": False})
                st.session_state.step += 1

        # Step 2: Select Sub-Topic
        elif st.session_state.step == 2:
            selected_topic = st.session_state.messages[-2]["content"].split("You chose ")[1].strip('.').lower()

            topic_options = {
                "technology": ["AI", "Blockchain", "IoT"],
                "health": ["Mental Health", "Nutrition", "Exercise"],
                "education": ["Online Learning", "Traditional Education", "Skill Development"],
                "finance": ["Investing", "Budgeting", "Saving"]
            }

            sub_topic = st.multiselect("Select one or more sub-topics:", topic_options.get(selected_topic, []), key="sub_topic")

            if st.button("Next"):
                if not sub_topic:
                    st.warning("Please select at least one sub-topic before proceeding.")
                else:
                    st.session_state.messages.append({"content": f"You chose sub-topics: {', '.join(sub_topic)}.", "is_user": True})
                    st.session_state.messages.append({"content": "Thank you for your responses! Here's what we've discussed today:", "is_user": False})
                    st.session_state.step += 1

        # Step 3: Restart Option
        elif st.session_state.step == 3:
            if st.button("Restart Chat"):
                st.session_state.step = 0
                st.session_state.messages = []
    # Right Sidebar - Agreement Summary (Grey)
    with col3:
        st.markdown(
            """
<div style="background-color: #f1f3f4; padding: 15px; border-radius: 8px;">
<h3 style="color: black;">We have agreed:</h3>
<p><b>Contract value:</b> $42,874</p>
<p><b>Contract length:</b> 1 year</p>
<p><b>Discount:</b> 8%</p>
<p><b>Pay terms:</b> <span style="color:rgb(200, 53, 229);"><b>120 days</b></span></p>
<p><b>2 year discount:</b> 9%</p>
<hr>
<h4 style="color: black;">Opportunities</h4>
<p><b>Growth for plants:</b> Austin, Cleveland, Houston, Belleville</p>
<p><b>Relationships Options:</b> Conference Call, Right to Pre-bid, SCF invitations</p>
</div>
            """,
            unsafe_allow_html=True,
        )

if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "step" not in st.session_state:
        st.session_state.step = 0

    if not st.session_state.logged_in:
        login_page()
    else:
        main()