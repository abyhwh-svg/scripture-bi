from pathlib import Path
import re
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Scripture Globe", page_icon="🌍", layout="wide")

@st.cache_data
def load():
    books = pd.read_csv(ROOT / "bible_books_combined.csv", encoding="utf-8-sig").fillna("")
    places = pd.read_csv(ROOT / "places.csv").fillna("")
    events = pd.read_csv(ROOT / "events.csv").fillna("")
    return books, places, events

books, places, events = load()
places_by_id = places.set_index("place_id")

def find_writing_place(raw):
    s = str(raw).lower()
    # Approximate location resolution; do not geocode broad regions as exact sites.
    rules = [
        ("plains of moab", "moab"), ("shushan", "shushan"),
        ("syrian antioch", "antioch"), ("caesarea", "caesarea"),
        ("jerusalem", "jerusalem"), ("near jerusalem", "jerusalem"),
        ("ephesus", "ephesus"), ("corinth", "corinth"),
        ("patmos", "patmos"), ("rome", "rome"),
        ("babylon", "babylon"), ("macedonia", "macedonia"),
        ("samaria", "samaria"), ("egypt", "egypt"),
        ("judah", "judah"), ("israel", "israel"),
        ("canaan", "canaan"),
    ]
    for label, key in rules:
        if label in s:
            return key
    return ""  # Wilderness/unknown location: don't invent a precise point.

books["writer_place_id"] = books["Place Written"].map(find_writing_place)
books["testament"] = books["Scripture Division"].map({"Hebrew Scriptures":"Old Testament / Hebrew Scriptures", "Greek Scriptures":"New Testament / Greek Scriptures"})

st.title("Scripture BI | The living atlas")
st.caption("Interactive orthographic globe • orange = writing locations • blue = event locations • illustrative historical coordinates")

with st.sidebar:
    st.header("Research filters")
    divisions = st.multiselect("Scripture division", books["testament"].dropna().unique().tolist(), default=books["testament"].dropna().unique().tolist())
    selected_books = books.loc[books["testament"].isin(divisions), "Book Name"].tolist()
    book_choices = st.multiselect("Books", selected_books, default=[])
    writers = sorted({w.strip() for raw in books.loc[books["Book Name"].isin(book_choices or selected_books), "Writer(s)"] for w in re.split(r";| and ", str(raw)) if w.strip()})
    chosen_writers = st.multiselect("Writers", writers, default=[])
    show_writing = st.checkbox("Where books were written", value=True)
    show_events = st.checkbox("Where events occurred", value=True)
    focus = st.selectbox("Focus location", ["Eastern Mediterranean (overview)"] + places["name"].tolist())
    zoom = st.slider("Globe zoom", 0.7, 5.0, 2.2, 0.1)

selected = books[books["Book Name"].isin(book_choices or selected_books)].copy()
selected = selected[selected["Writer(s)"].apply(lambda x: not chosen_writers or any(w in str(x) for w in chosen_writers))]
selected_events = events[events["book"].isin(selected["Book Name"])].copy()

if focus == "Eastern Mediterranean (overview)":
    center_lat, center_lon = 32, 34
else:
    row = places[places["name"] == focus].iloc[0]
    center_lat, center_lon = float(row["latitude"]), float(row["longitude"])

fig = go.Figure()
if show_writing:
    plotted = selected[selected["writer_place_id"].isin(places_by_id.index)].copy()
    if not plotted.empty:
        plotted["latitude"] = plotted["writer_place_id"].map(places_by_id["latitude"])
        plotted["longitude"] = plotted["writer_place_id"].map(places_by_id["longitude"])
        plotted["details"] = plotted.apply(lambda r: f"<b>{r['Book Name']}</b><br>Writer(s): {r['Writer(s)']}<br>Written: {r['Place Written']}<br>Completed: {r['Writing Completed (BCE/CE by division)']} ({'BCE' if r['Scripture Division']=='Hebrew Scriptures' else 'CE'})", axis=1)
        fig.add_trace(go.Scattergeo(lat=plotted["latitude"], lon=plotted["longitude"], text=plotted["details"], hoverinfo="text", mode="markers", name="Writing location", marker=dict(size=9, color="#ef9c3d", opacity=.8, line=dict(width=1, color="white"))))
if show_events and not selected_events.empty:
    mapped = selected_events[selected_events["place_id"].isin(places_by_id.index)].copy()
    mapped["latitude"] = mapped["place_id"].map(places_by_id["latitude"])
    mapped["longitude"] = mapped["place_id"].map(places_by_id["longitude"])
    mapped["details"] = mapped.apply(lambda r: f"<b>{r['event_name']}</b><br>{r['reference']}<br>{r['period_label']}<br>{r['summary']}", axis=1)
    fig.add_trace(go.Scattergeo(lat=mapped["latitude"], lon=mapped["longitude"], text=mapped["details"], hoverinfo="text", mode="markers", name="Event location", marker=dict(size=12, color="#3cbbe6", opacity=.85, symbol="diamond", line=dict(width=1, color="white"))))
fig.update_geos(projection_type="orthographic", projection_rotation=dict(lon=center_lon, lat=center_lat), projection_scale=zoom, showland=True, landcolor="#c7d6b3", showocean=True, oceancolor="#0d3556", showlakes=True, lakecolor="#0d3556", showcountries=True, countrycolor="#627b6c", coastlinecolor="#657d74", bgcolor="#071c31")
fig.update_layout(height=650, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor="#071c31", font_color="white", legend=dict(x=.01,y=.99,bgcolor="rgba(0,0,0,.4)"))
fig.add_trace(go.Scattergeo(lat=[center_lat], lon=[center_lon], mode="markers", marker=dict(symbol="star",size=17,color="#f5ce72"),name="Selected focus"))
st.plotly_chart(fig, use_container_width=True)
st.caption("Use the focus selector to rotate the globe; drag to explore.")
st.info("A marker for a broad region is only illustrative, not an exact historical coordinate. Rotate focus using the location dropdown; change zoom with the slider.")

left, right = st.columns(2)
with left:
    st.subheader("📖 Book / writer details")
    if selected.empty:
        st.warning("No books match these filters.")
    else:
        detail_book = st.selectbox("Inspect a book", selected["Book Name"].tolist())
        row = selected[selected["Book Name"] == detail_book].iloc[0]
        st.write(f"**Writer(s):** {row['Writer(s)']}")
        st.write(f"**Writing location:** {row['Place Written'] or 'Not specified'}")
        st.write(f"**Writing completed:** {row['Writing Completed (BCE/CE by division)']}")
        st.write(f"**Time covered:** {row['Time Covered'] or 'Not specified'}")
        if detail_book == "Hebrews":
            st.caption("The supplied JW.org table attributes Hebrews to Paul; authorship is disputed in broader scholarship.")
with right:
    st.subheader("🎬 Event detail / video")
    if selected_events.empty:
        st.write("No event records for the current selection. Add more rows to events.csv.")
    else:
        local_events = selected_events[selected_events["place_id"] == places.loc[places["name"] == focus, "place_id"].iloc[0]] if focus in places["name"].values else selected_events
        event_options = local_events if not local_events.empty else selected_events
        event_name = st.selectbox("Choose an event", event_options["event_name"].tolist())
        event = selected_events[selected_events["event_name"] == event_name].iloc[0]
        st.write(f"**Scripture:** {event['reference']}")
        st.write(f"**When:** {event['period_label']}")
        st.write(f"**What happened:** {event['summary']}")
        st.write(f"**Location confidence:** {event['location_confidence']}")
        if str(event["video_url"]).strip().startswith(("https://", "http://")):
            st.video(event["video_url"])
        elif str(event["video_url"]).strip() and (ROOT / str(event["video_url"])).is_file():
            st.video(str(ROOT / event["video_url"]))
            st.caption("Animated study presentation, not photorealistic reenactment. Use the player fullscreen control.")
        else:
            st.caption("No video attached.")

st.subheader("Historical timeline")
if not selected_events.empty:
    st.dataframe(selected_events.sort_values("year_sort")[["period_label","event_name","reference"]],hide_index=True)
st.subheader("📊 Research tables")
with st.expander("Bible books — filterable data", expanded=False):
    st.dataframe(selected.drop(columns=["writer_place_id", "testament"]), use_container_width=True, hide_index=True)
with st.expander("Events — editable in events.csv", expanded=False):
    st.dataframe(selected_events, use_container_width=True, hide_index=True)
st.download_button("Download filtered books CSV", selected.drop(columns=["writer_place_id", "testament"]).to_csv(index=False).encode("utf-8-sig"), "filtered_bible_books.csv", "text/csv")
st.caption("Starter project: the source book table has 66 records, but the event layer currently has only 9 examples. Dates follow the supplied source's chronology and are not independent historical verification.")
