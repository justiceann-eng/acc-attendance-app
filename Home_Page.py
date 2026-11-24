import streamlit as st

# Title of App
st.title("Web Development Labs 03 & 04")

# Assignment Data
st.header("CS 1301")
st.subheader("Team 37, Web Development - Section C")  
st.subheader("Elizabeth Healy, Justice Pennington")

# Introduction
st.write("""
Welcome to our app about ACC college football attendance! You can navigate between the pages using the sidebar to the left. The following pages are:

1. **Attendance**: This page allows you to look up home attendance for any ACC team by season, see trend charts, and helps you estimate a future game's attendance and how full the stadium would be.
2. **Attendance Chatbot**: You can chat with our GameDay Helper, an assistant that talks about what affects attendance and how athletic departments plan for game days.
""")
st.image("images/bobby_dodd.webp", caption="The creator's favorite stadium in the ACC!!! Beautiful Bobby Dodd!")