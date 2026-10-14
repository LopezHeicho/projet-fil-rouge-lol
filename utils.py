import streamlit as st
import base64
from streamlit.components.v1 import html

from PATHS import NAVBAR_PATHS, SETTINGS


def inject_custom_css():
    with open('src/assets/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def navbar_component():
    with open("src/assets/images/settings.png", "rb") as image_file:
        image_as_base64 = base64.b64encode(image_file.read())

    with open("src/assets/images/logo_hexforge_navbar.svg") as svg_file:
        logo_svg = " ".join(svg_file.read().split())

    navbar_items = ''
    for key, value in NAVBAR_PATHS.items():
        navbar_items += (f'<li><a class="navitem" target="_self" href="/?nav=%2F{value}"><span class="nav-label">{key}</span></a></li>')

    settings_items = ''
    for key, value in SETTINGS.items():
        settings_items += (
            f'<a href="/?nav={value}" target="_self" class="settingsNav">{key}</a>')

    component = rf'''
            <div class="navbar-wrap">
                <nav class="navbar" id="navbar">
                    <div class="nav-container">
                        <div class="brand">
                            <a href="/?nav=%2Fhome" target="_self" class="brand-link">
                                {logo_svg}
                            </a>
                        </div>
                        <ul class="navlist">
                            {navbar_items}
                        </ul>
                        <div class="dropdown" id="settingsDropDown">
                            <img class="dropbtn" alt="settings" src="data:image/png;base64, {image_as_base64.decode("utf-8")}"/>
                            <div id="myDropdown" class="dropdown-content">
                                {settings_items}
                            </div>
                        </div>
                    </div>
                </nav>
            </div>
            '''
    st.markdown(component, unsafe_allow_html=True)

    # Reste uniquement le toggle du menu déroulant (Paramètres) : le hack
    # JS qui retirait l'attribut target="_blank" des liens n'est plus
    # nécessaire puisqu'on met désormais target="_self" directement dans
    # le HTML ci-dessus (fiable depuis Streamlit >= 1.8.1, contrairement au
    # bricolage precedent qui allait modifier le DOM parent depuis l'iframe
    # du composant, fragile et probablement la cause du bug "ouvre un
    # nouvel onglet").
    js = '''
    <script>
        var dropdown = window.parent.document.getElementById("settingsDropDown");
        dropdown.onclick = function() {
            var dropWindow = window.parent.document.getElementById("myDropdown");
            if (dropWindow.style.opacity == "1"){
                dropWindow.style.opacity = "0";
                dropWindow.style.pointerEvents = "none";
            } else {
                dropWindow.style.opacity = "1";
                dropWindow.style.pointerEvents = "auto";
            }
        };
    </script>
    '''
    html(js)

def sidebar_logo():
    with open("src/assets/images/logo_hexforge_sidebar.svg") as svg_file:
        logo_svg = " ".join(svg_file.read().split())

    st.sidebar.markdown(
        f'''
        <div class="sidebar-logo-wrap">
            {logo_svg}
        </div>
        ''',
        unsafe_allow_html=True,
    )


def footer_disclaimer():
    st.markdown("---")
    st.caption(
        "Ce projet est un exercice de formation à but non commercial, non affilié à "
        "Riot Games. *Riot Games does not endorse or sponsor this project.*"
    )


def patch_to_tuple(p):
    return tuple(int(x) for x in p.split("."))

def valeurs_numeriques(valeur):
    try:
        return [float(v) for v in str(valeur).split(";")]
    except ValueError:
        return None

def patch_oe_vers_majmin(patch_float):
    major = int(patch_float)
    minor = round((patch_float - major) * 100)
    return f"{major}.{minor}"