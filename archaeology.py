import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from urllib.parse import quote
import hashlib

@st.cache_data
def load_evidence(root):
    return pd.read_csv(root / 'archaeology.csv', encoding='utf-8-sig').fillna('')

def filter_evidence(data, books, region, event_ids):
    mask = data.books.map(lambda v: bool(set(v.split(';')) & set(books)))
    if region:
        mask &= data.related_places.map(lambda v: region.casefold() in [x.casefold() for x in v.split(';')])
    if event_ids:
        mask &= data.event_ids.map(lambda v: bool(set(v.split(';')) & set(event_ids)))
    return data[mask]

def add_evidence_layer(fig, data):
    if not data.empty:
        fig.add_trace(go.Scattergeo(lat=data.latitude, lon=data.longitude, text=data.name + ' — findspot: ' + data.findspot, hoverinfo='text', mode='markers', name='Archaeological findspot', marker=dict(symbol='square', size=13, color='#42c58a', line=dict(color='white',width=1))))

def research_panel(data, all_data):
    st.header('🏛️ Archaeological evidence')
    st.caption('Green squares mark approximate discovery sites, not necessarily the places depicted or current museum locations. Archaeological dates are separate from the Bible dataset chronology.')
    st.caption('Photographs are external Wikimedia files, not generated scenes. Follow the photo source if an image does not load.')
    if data.empty:
        st.info('No curated evidence matches these filters. This does not establish that no evidence exists.')
    for _, r in data.iterrows():
        with st.expander(r['name'] + ' — ' + r.findspot, expanded=True):
            a,b=st.columns([1,2])
            with a:
                if r.photo_file:
                    filename=r.photo_file.replace(' ','_')
                    h=hashlib.md5(filename.encode()).hexdigest()
                    url=f'https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{quote(filename)}'
                    st.image(url, caption='Modern copy (not original stone)' if r.id=='a04' else r['name'])
                    st.caption(f'Photo: {r.credit} | {r.license} | displayed at reduced size')
                    st.markdown(f'[Photo source and reuse terms](https://commons.wikimedia.org/wiki/File:{quote(filename)})')
                    if r.license_url: st.markdown(f'[License]({r.license_url})')
                else: st.markdown(f'[View original manuscript at museum]({r.source_url})')
            with b:
                st.write(f'**Scripture:** {r.references}')
                st.write(f'**Dating:** {r.date} | **Discovery:** {r.discovery}')
                st.write(f'**Collection:** {r.repository}')
                st.write(f'**Physical evidence:** {r.evidence}')
                st.write(f'**Limits / interpretation:** {r.limits}')
                st.markdown(f'[Research documentation]({r.source_url})')
    st.subheader('Personal evidence collection')
    ids=st.multiselect('Save evidence records', all_data.id.tolist(), format_func=lambda i: all_data.set_index('id').loc[i,'name'], key='arch_saved')
    notes=st.text_area('Your research notes (download to retain; not permanently stored)')
    saved=all_data[all_data.id.isin(ids)].copy()
    saved['research_notes']=notes
    st.download_button('Download personal evidence CSV',saved.to_csv(index=False).encode('utf-8-sig'),'my_evidence.csv','text/csv')
    st.download_button('Download filtered archaeology CSV',data.to_csv(index=False).encode('utf-8-sig'),'filtered_archaeology.csv','text/csv')


def featured_evidence(data):
    r = data.iloc[0]
    if len(data) > 1:
        choice = st.selectbox("Artifact", data.id.tolist(), format_func=lambda i: data.set_index('id').loc[i,'name'])
        r = data[data.id == choice].iloc[0]
    st.write(f"**{r['name']}**")
    if r.photo_file:
        filename = r.photo_file.replace(' ', '_')
        h = hashlib.md5(filename.encode()).hexdigest()
        st.image(f'https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{quote(filename)}', caption='Modern copy (not original stone)' if r.id=='a04' else r['name'])
        st.caption(f'Photo: {r.credit} | {r.license}')
        st.markdown(f'[Photo source](https://commons.wikimedia.org/wiki/File:{quote(filename)})')
    st.write(f"**Scripture:** {r.references}")
    st.write(f"**Dating:** {r.date}")
    st.write(f"**Physical evidence:** {r.evidence}")
    st.write(f"**Limits:** {r.limits}")
    st.markdown(f'[Research documentation]({r.source_url})')
