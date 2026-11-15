"""YouTube video analytics + educational likes prediction Streamlit app."""
import os
from datetime import datetime, timezone
from pathlib import Path
import joblib
import pandas as pd
import streamlit as st
from src.pipeline import ROOT, FEATURES, duration_seconds, predict
from youtube_api import extract_video_id, fetch_video

st.set_page_config(page_title='TubeScope | Video Intelligence', page_icon='▶️', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container{padding-top:1.8rem;max-width:1280px}h1,h2,h3{letter-spacing:-.035em}
.hero{padding:24px 28px;border-radius:20px;background:linear-gradient(115deg,#1b2134,#303d61);color:white;margin-bottom:20px}
.hero h1{color:white;margin:0;font-size:2.2rem}.hero p{color:#d2d8e6;margin:8px 0 0}
[data-testid="stMetric"]{background:rgba(125,125,125,.075);border:1px solid rgba(125,125,125,.15);border-radius:14px;padding:16px}
.small-note{font-size:.85rem;color:#777}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>▶ TubeScope</h1><p>YouTube video analytics · ML likes estimates · Creator insights</p></div>', unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def load_model(path, modified):
    return joblib.load(path)

model_path = ROOT/'models'/'random_forest.joblib'
model = load_model(str(model_path), model_path.stat().st_mtime) if model_path.exists() else None

def api_key():
    try:
        return st.secrets.get('YOUTUBE_API_KEY','') or os.getenv('YOUTUBE_API_KEY','')
    except (FileNotFoundError, KeyError, OSError):
        return os.getenv('YOUTUBE_API_KEY','')

def fmt(n):
    return 'Not available' if n is None else f'{n:,}'

def pct(a,b):
    return 100*a/b if b else None

def render_prediction(views, duration, tags, actual=None):
    if model is None:
        st.error('Trained model not found. Run `python train.py --data data/youtube_sample.csv` first.')
        return
    if duration is None or pd.isna(duration) or duration <= 0:
        st.warning('Cannot estimate likes because the video duration is missing or invalid.')
        return
    try:
        estimated = predict(model,views,duration,tags)
    except Exception as exc:
        st.error(f'Model prediction failed: {exc}')
        return
    c1,c2,c3 = st.columns(3)
    c1.metric('Predicted likes',fmt(estimated))
    c2.metric('Actual likes',fmt(actual))
    c3.metric('Predicted likes / views',f'{pct(estimated,views):.2f}%' if views else 'N/A')
    if actual is not None:
        st.subheader('Predicted vs actual')
        st.bar_chart(pd.DataFrame({'Likes':[estimated,actual]},index=['Model estimate','Actual']), horizontal=True)
        a,b,c=st.columns(3)
        a.metric('Absolute error',fmt(abs(estimated-actual)))
        b.metric('Actual likes / views',f'{pct(actual,views):.2f}%' if views else 'N/A')
        c.metric('Difference',f'{estimated-actual:+,}')
    else:
        st.info('Actual likes were not returned by YouTube; the comparison is unavailable.')
    st.caption('Model trained on synthetic example data. Estimates are demonstrations, not validated forecasts. Views are already observed, so this is not a pre-upload prediction.')

with st.sidebar:
    st.header('Navigation')
    page=st.radio('Choose a workspace',['🔎 Video analyzer','🧮 Manual prediction','📊 Model evaluation','ℹ️ About & setup'],label_visibility='collapsed')
    st.divider()
    st.caption('Source: YouTube Data API v3 · Random Forest Regression')
    if not api_key():
        st.warning('YouTube API key not configured. Manual prediction and model evaluation still work.')
    else:
        st.success('API key configured')
    st.caption('Built with Python + Streamlit')

if page=='🔎 Video analyzer':
    st.subheader('Analyze a public YouTube video')
    st.write('Paste a YouTube watch, Shorts, live, or short link. The app retrieves public metadata and compares its likes with an ML estimate.')
    with st.form('video_form'):
        url=st.text_input('Video URL or 11-character ID',placeholder='https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        submitted=st.form_submit_button('🔎 Analyze video',type='primary',use_container_width=True)
    if submitted:
        if not api_key():
            st.error('Configure YOUTUBE_API_KEY in .streamlit/secrets.toml to analyze URLs.')
        else:
            try:
                vid=extract_video_id(url)
                with st.spinner('Fetching public video details…'):
                    st.session_state['video']=fetch_video(vid,api_key())
            except (ValueError,RuntimeError) as exc:
                st.session_state.pop('video',None)
                st.error(str(exc))
    video=st.session_state.get('video')
    if video:
        left,right=st.columns([1,2],gap='large')
        with left:
            if video.get('thumbnail'):
                st.image(video['thumbnail'],use_container_width=True)
            st.link_button('▶ Open on YouTube',video['url'],use_container_width=True)
        with right:
            st.markdown(f'### {video["title"]}')
            st.write(f'**Channel:** {video["channel"]}')
            st.write(f'**Published:** {video["published"][:10] or "Unknown"}')
            st.write(f'**Video ID:** `{video["id"]}`')
            st.write(f'**Category ID:** {video.get("category_id") or "Unknown"}')
        st.subheader('Video statistics')
        c1,c2,c3,c4=st.columns(4)
        c1.metric('Views',fmt(video['views']))
        c2.metric('Likes',fmt(video['likes']))
        c3.metric('Comments',fmt(video['comments']))
        c4.metric('Tags',len(video['tags']))
        seconds=duration_seconds(video['duration'])
        st.write(f'**Duration:** {int(seconds):,} seconds' if pd.notna(seconds) else '**Duration:** unavailable')
        if video['views'] and video['likes'] is not None:
            st.progress(min(video['likes']/video['views'],1.0),text=f'Like-to-view ratio: {pct(video["likes"],video["views"]):.2f}%')
        if video['views'] and video['likes'] is not None and video['comments'] is not None:
            st.caption(f'Observed (likes + comments) / views: {pct(video["likes"]+video["comments"],video["views"]):.2f}% — not a complete engagement measure.')
        st.subheader('Machine learning estimate')
        render_prediction(video['views'],seconds,len(video['tags']),video['likes'])
        with st.expander('Video tags and metadata'):
            st.write(', '.join(video['tags']) if video['tags'] else 'No public tags')
            st.json({k:v for k,v in video.items() if k not in ('tags','thumbnail')})
        report=pd.DataFrame([{'video_id':video['id'],'title':video['title'],'channel':video['channel'],'views':video['views'],'likes':video['likes'],'comments':video['comments'],'duration_seconds':seconds,'tag_count':len(video['tags']),'analyzed_at_utc':datetime.now(timezone.utc).isoformat()}])
        st.download_button('⬇ Download video analytics CSV',report.to_csv(index=False).encode('utf-8'),file_name=f'youtube_analytics_{video["id"]}.csv',mime='text/csv')
elif page=='🧮 Manual prediction':
    st.subheader('Estimate likes from manual inputs')
    st.write('Try different video statistics without a YouTube API key.')
    with st.form('manual_form'):
        views=st.number_input('Views',min_value=0,max_value=10_000_000_000,value=10000,step=1000)
        duration=st.number_input('Duration in seconds',min_value=1,max_value=86400,value=300)
        tags=st.number_input('Number of tags',min_value=0,max_value=1000,value=5)
        actual=st.number_input('Actual likes (optional, use -1 if unknown)',min_value=-1,value=-1)
        run=st.form_submit_button('✨ Predict likes',type='primary')
    if run:
        render_prediction(views,duration,tags,None if actual<0 else actual)
        st.caption('You can compare results by changing the inputs and predicting again.')
elif page=='📊 Model evaluation':
    st.subheader('Saved model evaluation')
    st.warning('These results were produced using the included synthetic sample dataset; they are not real-world YouTube performance claims.')
    path=ROOT/'outputs'/'metrics.csv'
    if path.exists():
        metrics=pd.read_csv(path)
        st.dataframe(metrics,use_container_width=True,hide_index=True)
    else:
        st.info('No metrics found. Run the training command in the README.')
    predictions=ROOT/'outputs'/'predictions.csv'
    if predictions.exists():
        df=pd.read_csv(predictions)
        if {'actual_likes','predicted_likes'}.issubset(df.columns):
            st.subheader('Holdout predictions')
            st.scatter_chart(df,x='actual_likes',y='predicted_likes')
            st.download_button('Download evaluation predictions',df.to_csv(index=False),file_name='model_predictions.csv',mime='text/csv')
    for name,caption in [('actual_vs_predicted.png','Actual vs predicted'),('feature_importance.png','Feature importance')]:
        path=ROOT/'outputs'/name
        if path.exists():
            st.image(str(path),caption=caption,use_container_width=True)
    st.markdown('**Model features:** '+', '.join(FEATURES))
    st.info('For credible real-world performance, train on actual videos with known duration, avoid duplicate video IDs across splits, and evaluate on later/unseen videos.')
else:
    st.subheader('About TubeScope')
    st.write('TubeScope is an educational analytics tool built on the original YouTube Video Popularity Prediction project.')
    st.markdown('''**What it can do**
- Analyze public YouTube video URLs through the official API
- Display metadata, views, likes, comments, duration and tags
- Estimate likes with the included Random Forest model
- Compare actual and estimated likes, visualize errors, and export CSV
- Work offline in manual mode (after dependencies are installed)

**Limitations**
- API key, network access, and YouTube API quota are required for URL lookup.
- Some videos have hidden or unavailable likes, comments, tags, or metadata.
- The included model was trained on synthetic data and must not be presented as a validated real-world predictor.
- Like-to-view ratios are descriptive and do not imply future performance.

**Security:** Keep API keys in `.streamlit/secrets.toml` or environment variables; never commit them to GitHub.''')
    st.code('python -m streamlit run app.py',language='bash')
