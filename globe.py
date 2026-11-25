import base64, json
from pathlib import Path
import streamlit.components.v1 as components

def globe(welcome=False, points=None, lat=32, lon=34, zoom=1, flat=False):
    root=Path(__file__).resolve().parent
    texture=base64.b64encode((root/'earth_texture.jpg').read_bytes()).decode()
    config=json.dumps(dict(welcome=welcome, points=points or [], lat=lat, lon=lon, zoom=zoom, flat=flat)).replace('<','\\u003c')
    html=(root/('welcome_globe.html' if welcome else 'globe.html')).read_text(encoding='utf8').replace('__CONFIG__',config).replace('__TEXTURE__',texture)
    components.html(html,height=390 if welcome else 540,scrolling=False)
