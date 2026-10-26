import streamlit as st

st.title("Mi primera aplicación")

st.write("Bienvenido")

nombre = st.text_input("¿Como te llamas?")

st.write("Hola", nombre)
