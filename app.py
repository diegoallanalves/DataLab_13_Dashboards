"""DataLab 13: interactive, interview-friendly demonstration of thirteen data disciplines."""
import io
import json
import sqlite3
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from bs4 import BeautifulSoup
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve, precision_score, recall_score, f1_score
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from scraping import SITES, collect
from core import sample_data, quality_report, clean_data, customer_metrics, uplift, persist_sqlite, csv_bytes, read_uploaded

st.set_page_config(page_title='DataLab 13 | Diego Alves', page_icon='🧪', layout='wide', initial_sidebar_state='expanded')
COLORS = ['#695CFF', '#10D5BA', '#3F9AFF', '#FF8C55', '#D857EF', '#FF5579']
px.defaults.template = 'plotly_dark'
px.defaults.color_discrete_sequence = COLORS
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:Inter,system-ui,sans-serif}
.stApp{background:radial-gradient(ellipse at 65% -15%,#1b2850 0%,#0a1429 48%,#080f20 100%);color:#eaf1ff}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0c1b37,#0a1227);border-right:1px solid #263759}
[data-testid="stSidebar"] *{color:#dce7ff}
[data-testid="stSidebar"] [role="radiogroup"] label{font-size:1rem!important;line-height:1.45!important;padding:7px 4px!important}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-size:1rem!important;font-weight:600!important}
[data-testid="stSidebar"]{min-width:285px;max-width:340px}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{line-height:1.6}
[data-testid="stPlotlyChart"]{box-shadow:0 10px 35px #03081844}
[data-testid="stTabs"] button{font-weight:700;font-size:1rem}
[data-testid="stMetric"]{min-height:112px}
[data-testid="stMetricValue"]{font-size:2rem!important}
.block-container{padding-top:2rem;max-width:1550px}
.stSelectbox label,.stSlider label,.stMultiSelect label{font-weight:650!important}

h1,h2,h3{letter-spacing:-.03em;color:#f2f6ff!important}
h1{font-size:2.1rem!important;font-weight:800!important}
[data-testid="stMetric"]{background:linear-gradient(135deg,#14284a,#111d36);border:1px solid #294062;border-radius:15px;padding:18px 20px;box-shadow:0 10px 30px #030a1933}
[data-testid="stMetricLabel"]{color:#b8c7eb}
[data-testid="stMetricValue"]{color:#f5f7ff;font-weight:800}
[data-testid="stPlotlyChart"]{background:#101d34;border:1px solid #273958;border-radius:15px;padding:10px}
.stButton>button[kind="primary"],.stDownloadButton>button{background:linear-gradient(100deg,#6b45f5,#2962ff);border:0;color:white;border-radius:10px;font-weight:700}
div[data-testid="stExpander"]{border:1px solid #293e5b;border-radius:12px}
.hero{padding:24px 28px;border-radius:18px;background:linear-gradient(105deg,#1a2450,#142b45 65%,#103e4c);border:1px solid #304b77;margin-bottom:20px}
.hero small{color:#74e2d0;font-weight:700;letter-spacing:.12em}
.hero h1{margin:.3rem 0!important}.hero p{color:#b8cbe9;margin:0}
.note{padding:12px 16px;background:#142742;border-left:4px solid #10d5ba;border-radius:8px;color:#d7e8ff}
</style>""", unsafe_allow_html=True)
PAGES = [
    '01 · Machine Learning Prediction Studio', '02 · Business Insights Explorer',
    '03 · Data Pipeline Builder', '04 · Database Management Console',
    '05 · KPI Performance Command Center', '06 · Customer Behaviour Analytics',
    '07 · Web Data Collection Platform', '08 · Smart Data Importer',
    '09 · Interactive Visualization Studio', '10 · Data Quality Monitoring Platform',
    '11 · ETL Pipeline Orchestrator', '12 · Data Enrichment & Augmentation Lab',
    '13 · Statistical Experimentation Lab'
]
st.sidebar.markdown('## 💠 DataLab **13**')
st.sidebar.caption('DATA PORTFOLIO FOR INTERVIEWS')
page = st.sidebar.radio('EXPLORE APPLICATIONS', PAGES)
st.sidebar.divider()
st.sidebar.markdown('**Diego Allan Alves**  \nPython · SQL · ML · Data Engineering')
st.sidebar.caption('All default datasets are synthetic. Charts and metrics are computed live.')
if 'dataset' not in st.session_state:
    st.session_state.dataset = sample_data()
df = st.session_state.dataset.copy()
st.markdown(f'<div class="hero"><small>DATA LAB 13  /  INTERACTIVE PORTFOLIO</small><h1>{page.split(" · ",1)[1]}</h1><p>Explore real, executable Python workflows, interactive analytics and interview-ready demonstrations.</p></div>',unsafe_allow_html=True)
DESCRIPTIONS = [
    ('Train and evaluate classification models using a reproducible holdout dataset.', 'Feature engineering, precision, recall, ROC AUC, model explainability and what-if prediction.'),
    ('Investigate business performance across regions and customer groups.', 'Filtering, aggregation, revenue comparisons and data storytelling.'),
    ('Build an extract → transform → load workflow with configurable cleaning.', 'Data preparation, repeatability, data validation and exports.'),
    ('Explore SQL queries on an isolated in-memory SQLite database.', 'SQL grouping, filtering, aggregations and safe read-only analysis.'),
    ('Track commercial KPIs and investigate what drives revenue and conversion.', 'Trends, customer segments, regional performance and actionable insights.'),
    ('Understand how customer activity relates to spend and conversion.', 'Behavioural segmentation, exploratory analysis and correlations.'),
    ('Collect structured information from websites made specifically for scraping practice.', 'HTML parsing, pagination, respectful request rates, export and visual analysis.'),
    ('Import CSV or JSON and inspect the shape and quality of incoming data.', 'Schema exploration, data types, missing values and dataset validation.'),
    ('Choose variables and chart types to explore any numeric dataset.', 'Visual encoding, distribution analysis and interactive chart building.'),
    ('Audit completeness, duplicates and uniqueness before data is used downstream.', 'Data quality profiling, monitoring concepts and validation reports.'),
    ('Run an ETL demonstration that extracts, cleans and persists records.', 'Workflow stages, status reporting and database persistence.'),
    ('Create derived customer features and discover groups using clustering.', 'Feature engineering, K-Means segmentation and enriched exports.'),
    ('Compare test and control conversion rates with transparent calculations.', 'A/B testing, absolute lift, relative lift and experiment interpretation.'),
]
index=int(page[:2])-1
intro,learn=DESCRIPTIONS[index]
st.markdown(f'<div class="note"><b>About this application:</b> {intro}<br><b>What you will learn:</b> {learn}</div>',unsafe_allow_html=True)
st.write('')


if page.startswith('01'):
    st.caption('A complete machine learning workbench · synthetic churn data · reproducible train/test split')
    @st.cache_data(show_spinner=False)
    def churn_data(n=1800, seed=42):
        rng=np.random.default_rng(seed)
        tenure=rng.integers(1,73,n)
        monthly=rng.uniform(20,120,n).round(2)
        contract=rng.choice(['Month-to-month','One year','Two years'],n,p=[.55,.28,.17])
        support=rng.poisson(1.5,n)
        usage=rng.uniform(2,35,n)
        logit=-1.8 + 1.5*(contract=='Month-to-month') - .022*tenure + .012*(monthly-65) + .30*support - .028*usage
        probability=1/(1+np.exp(-logit))
        churn=rng.binomial(1,probability)
        return pd.DataFrame({'tenure_months':tenure,'monthly_charges':monthly,'contract':contract,'support_tickets':support,'weekly_usage_hours':usage.round(1),'churn':churn})
    data=churn_data()
    with st.sidebar:
        st.markdown('### ⚙️ Model settings')
        algo=st.selectbox('Algorithm',['Random Forest','Logistic Regression'])
        test_size=st.slider('Holdout test size',15,40,25,5)
        n_trees=st.slider('Random Forest trees',50,300,150,50,disabled=algo!='Random Forest')
        threshold=st.slider('Decision threshold',.20,.80,.50,.05)
    X=pd.get_dummies(data.drop(columns='churn'),columns=['contract'],dtype=int)
    y=data['churn']
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=test_size/100,random_state=42,stratify=y)
    model=RandomForestClassifier(n_estimators=n_trees,min_samples_leaf=5,random_state=42,n_jobs=-1) if algo=='Random Forest' else make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,random_state=42))
    model.fit(X_train,y_train)
    probs=model.predict_proba(X_test)[:,1]
    pred=(probs>=threshold).astype(int)
    auc=roc_auc_score(y_test,probs)
    k1,k2,k3,k4=st.columns(4)
    k1.metric('Customers',f'{len(data):,}')
    k2.metric('Churn rate',f'{y.mean():.1%}')
    k3.metric('Holdout accuracy',f'{accuracy_score(y_test,pred):.1%}')
    k4.metric('ROC AUC',f'{auc:.3f}')
    left,right=st.columns([1.25,1])
    with left:
        st.subheader('📊 Model performance')
        metrics=pd.DataFrame({'Metric':['Accuracy','Precision','Recall','F1','ROC AUC'],'Score':[accuracy_score(y_test,pred),precision_score(y_test,pred,zero_division=0),recall_score(y_test,pred,zero_division=0),f1_score(y_test,pred,zero_division=0),auc]})
        fig=px.bar(metrics,x='Metric',y='Score',color='Metric',text='Score',range_y=[0,1],title='Holdout evaluation')
        fig.update_traces(texttemplate='%{text:.2f}',textposition='outside')
        fig.update_layout(showlegend=False,height=340)
        st.plotly_chart(fig,width='stretch')
    with right:
        st.subheader('🎯 Confusion matrix')
        cm=confusion_matrix(y_test,pred,labels=[0,1])
        fig=px.imshow(cm,x=['Predicted stay','Predicted churn'],y=['Actual stay','Actual churn'],text_auto=True,color_continuous_scale=[[0,'#182b55'],[.5,'#4a48bc'],[1,'#15d9b5']],title='Classification counts')
        fig.update_layout(height=340,coloraxis_showscale=False)
        st.plotly_chart(fig,width='stretch')
    a,b,c=st.columns(3)
    with a:
        st.subheader('🔍 Feature importance')
        if algo=='Random Forest':
            imp=pd.DataFrame({'Feature':X.columns,'Importance':model.feature_importances_}).sort_values('Importance')
        else:
            imp=pd.DataFrame({'Feature':X.columns,'Importance':abs(model.named_steps['logisticregression'].coef_[0])}).sort_values('Importance')
        fig=px.bar(imp,x='Importance',y='Feature',orientation='h',color='Importance',color_continuous_scale=['#3b7cff','#855bff','#0cd7b1'])
        fig.update_layout(height=360,coloraxis_showscale=False)
        st.plotly_chart(fig,width='stretch')
    with b:
        st.subheader('📈 Probability distribution')
        hist=pd.DataFrame({'Predicted churn probability':probs,'Actual outcome':np.where(y_test.to_numpy()==1,'Churn','Stay')})
        fig=px.histogram(hist,x='Predicted churn probability',color='Actual outcome',nbins=25,barmode='overlay',opacity=.72)
        fig.update_layout(height=360)
        st.plotly_chart(fig,width='stretch')
    with c:
        st.subheader('📉 ROC curve')
        fpr,tpr,_=roc_curve(y_test,probs)
        roc_df=pd.DataFrame({'False positive rate':fpr,'True positive rate':tpr})
        fig=px.area(roc_df,x='False positive rate',y='True positive rate',title=f'AUC = {auc:.3f}')
        fig.add_scatter(x=[0,1],y=[0,1],mode='lines',line=dict(color='#8896b5',dash='dash'),name='Random')
        fig.update_layout(height=360)
        st.plotly_chart(fig,width='stretch')
    low,high=st.columns([1.2,1])
    with low:
        st.subheader('🧭 Customer segments · PCA')
        z=StandardScaler().fit_transform(X)
        xy=PCA(n_components=2,random_state=42).fit_transform(z)
        points=pd.DataFrame({'PC1':xy[:,0],'PC2':xy[:,1],'Outcome':np.where(y==1,'Churn','Stay')})
        fig=px.scatter(points,x='PC1',y='PC2',color='Outcome',opacity=.5,render_mode='webgl')
        fig.update_layout(height=360)
        st.plotly_chart(fig,width='stretch')
    with high:
        st.subheader('🎛️ What-if prediction')
        c1,c2=st.columns(2)
        tenure=c1.slider('Tenure (months)',1,72,12)
        charges=c2.slider('Monthly charges ($)',20,120,70)
        contract=st.selectbox('Contract',['Month-to-month','One year','Two years'])
        tickets=st.slider('Support tickets',0,8,2)
        usage=st.slider('Weekly usage (hours)',2,35,14)
        row=pd.DataFrame([{'tenure_months':tenure,'monthly_charges':charges,'contract':contract,'support_tickets':tickets,'weekly_usage_hours':usage}])
        row=pd.get_dummies(row,columns=['contract'],dtype=int).reindex(columns=X.columns,fill_value=0)
        score=float(model.predict_proba(row)[0,1])
        st.metric('Predicted churn probability',f'{score:.1%}')
        st.progress(score)
        st.caption('Illustrative estimate from a model trained on synthetic data—not a real customer risk score.')
    with st.expander('📋 Dataset, model notes and downloadable predictions'):
        st.dataframe(data.head(30),width='stretch')
        export=X_test.copy();export['actual_churn']=y_test;export['predicted_probability']=probs;export['predicted_churn']=pred
        st.download_button('Download holdout predictions',csv_bytes(export),'churn_predictions.csv','text/csv')
        st.info('Training and test data are separated before fitting. The ROC AUC uses predicted probabilities. Threshold changes classification metrics but not ROC AUC. PCA is for visualization, not model training.')

elif page.startswith('02'):
    st.header('Business Insights Explorer')
    region = st.multiselect('Regions', sorted(df.region.dropna().unique()), default=sorted(df.region.dropna().unique()))
    selected = df[df.region.isin(region)]
    st.dataframe(selected.head(40), width='stretch')
    if len(selected):
        st.plotly_chart(px.bar(selected.groupby('region', as_index=False)['spend'].sum(), x='region', y='spend', title='Revenue by region'), width='stretch')
        st.download_button('Download filtered CSV', csv_bytes(selected), 'business_insights.csv', 'text/csv')

elif page.startswith('03'):
    st.header('Data Pipeline Builder')
    st.write('Configure and run a simple extract → transform → load workflow.')
    dedup = st.checkbox('Remove duplicate rows', value=True)
    strip = st.checkbox('Trim text whitespace', value=True)
    if st.button('Run pipeline'):
        output = clean_data(df, dedup, strip)
        st.success(f'Extracted {len(df)} rows → transformed {len(output)} rows → loaded to in-memory result')
        st.dataframe(output.head(15))
        st.download_button('Download transformed data', csv_bytes(output), 'pipeline_output.csv')

elif page.startswith('04'):
    st.header('Database Management Console')
    st.write('Load synthetic data into an isolated in-memory SQLite database and run a read-only SQL query.')
    with sqlite3.connect(':memory:') as conn:
        df.to_sql('customer_events', conn, index=False)
        query = st.text_area('SQL (SELECT or WITH only)', 'SELECT region, COUNT(*) AS customers, ROUND(SUM(spend), 2) AS revenue FROM customer_events GROUP BY region ORDER BY revenue DESC')
        if st.button('Execute read-only query'):
            if not query.lstrip().lower().startswith(('select ', 'with ')) or ';' in query.strip().rstrip(';'):
                st.error('Only one SELECT/WITH statement is permitted.')
            else:
                try:
                    conn.execute('PRAGMA query_only = ON')
                    st.dataframe(pd.read_sql_query(query, conn), width='stretch')
                except Exception as exc:
                    st.error(f'Query failed: {exc}')
    st.caption('Demo only: not a production SQL sandbox. Do not connect to privileged databases.')

elif page.startswith('05'):
    st.header('KPI Performance Command Center')
    a, b, c = st.columns(3)
    a.metric('Customers', len(df))
    b.metric('Revenue', f'${df.spend.sum():,.0f}')
    c.metric('Conversion rate', f'{df.converted.mean():.1%}')
    left,right=st.columns(2)
    metrics=customer_metrics(df)
    left.plotly_chart(px.bar(metrics,x='segment',y='revenue',color='segment',title='Revenue by segment'),width='stretch')
    right.plotly_chart(px.pie(metrics,names='segment',values='customers',hole=.6,title='Customer mix'),width='stretch')
    timeline=(df.assign(order_date=pd.to_datetime(df['order_date'], errors='coerce')).dropna(subset=['order_date']).set_index('order_date').resample('MS')['spend'].sum().reset_index())
    st.plotly_chart(px.area(timeline,x='order_date',y='spend',title='Monthly revenue trend'),width='stretch')

elif page.startswith('06'):
    st.header('Customer Behaviour Analytics')
    metrics = customer_metrics(df)
    st.dataframe(metrics.style.format({'revenue': '${:,.2f}', 'conversion_rate': '{:.1%}'}), width='stretch')
    st.plotly_chart(px.scatter(df, x='visits', y='spend', color='segment', title='Visits vs. spend'), width='stretch')
    st.caption('Explore segments and behavioural patterns; correlation does not imply causation.')

elif page.startswith('07'):
    st.subheader('🌐 Web Data Collection Platform')
    st.info('Educational use only. These two websites are designed for scraping practice. Check each website’s robots.txt and terms before running requests. No arbitrary URLs are accepted.')
    c1,c2=st.columns([1,1.5])
    with c1:
        st.markdown('#### 1 · Choose a practice website')
        site=st.selectbox('Approved website',list(SITES))
        st.markdown(f"**{SITES[site]['url']}**")
        st.caption(SITES[site]['description'])
        st.markdown('#### 2 · Configure collection')
        pages=st.slider('Pages to request',1,5,2)
        delay=st.slider('Delay between requests (seconds)',0.5,5.0,1.0,0.5)
        run=st.button('▶ Run educational scraper',type='primary',width='stretch')
        st.markdown('#### 📚 Websites to explore')
        for name,details in SITES.items():
            st.markdown(f"**{name}** — [Visit website]({details['url']})")
            st.caption(details['description'])
        st.caption('Other learning resources: [Scrapy tutorial](https://docs.scrapy.org/en/latest/intro/tutorial.html) · [Beautiful Soup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)')
    with c2:
        st.markdown('#### 3 · Extracted records')
        if run:
            try:
                with st.spinner('Requesting approved training pages…'):
                    st.session_state.scrape_result=collect(site,pages,delay)
                    st.session_state.scrape_site=site
            except (requests.RequestException,ValueError) as exc:
                st.error(f'Collection failed: {exc}. Check connectivity or try fewer pages.')
        scraped=st.session_state.get('scrape_result',pd.DataFrame())
        current_site=st.session_state.get('scrape_site','')
        if not scraped.empty:
            st.success(f'{len(scraped)} records extracted from {current_site}.')
            st.dataframe(scraped,width='stretch',height=330)
            st.download_button('⬇ Export collected CSV',csv_bytes(scraped),'web_scraping_results.csv',mime='text/csv')
        else:
            st.markdown('Run the scraper to see live results. The dashboard will not fabricate scraped records.')
    if not scraped.empty:
        st.markdown('### 📊 Explore the collected data')
        if current_site=='Books to Scrape' and 'Price GBP' in scraped:
            m1,m2,m3=st.columns(3)
            m1.metric('Books',len(scraped))
            m2.metric('Average price',f"£{scraped['Price GBP'].mean():.2f}")
            m3.metric('Average rating',f"{scraped['Rating'].mean():.1f} / 5")
            l,r=st.columns(2)
            l.plotly_chart(px.histogram(scraped,x='Price GBP',nbins=16,title='Book price distribution',color_discrete_sequence=['#9b55ff']),width='stretch')
            ratings=scraped.groupby('Rating',as_index=False).agg(Books=('Title','count'),Average_Price=('Price GBP','mean'))
            r.plotly_chart(px.bar(ratings,x='Rating',y='Average_Price',color='Rating',title='Average price by rating',text_auto='.2f'),width='stretch')
            st.plotly_chart(px.bar(ratings,x='Rating',y='Books',title='Books by star rating',color='Rating',text_auto=True),width='stretch')
        elif current_site=='Quotes to Scrape':
            m1,m2=st.columns(2)
            m1.metric('Quotes',len(scraped));m2.metric('Authors',scraped['Author'].nunique())
            counts=scraped['Author'].value_counts().head(12).rename_axis('Author').reset_index(name='Quotes')
            st.plotly_chart(px.bar(counts,x='Quotes',y='Author',orientation='h',color='Quotes',title='Most frequent authors'),width='stretch')
            tags=scraped['Tags'].str.split(', ').explode().value_counts().head(12).rename_axis('Tag').reset_index(name='Count')
            st.plotly_chart(px.bar(tags,x='Tag',y='Count',color='Count',title='Common quote tags'),width='stretch')

elif page.startswith('08'):
    st.header('Smart Data Importer')
    upload = st.file_uploader('Upload CSV or JSON', type=['csv', 'json'])
    if upload:
        try:
            imported = read_uploaded(upload)
            st.session_state.dataset = imported
            st.success(f'Imported {len(imported)} rows and {len(imported.columns)} columns. Dataset stored in session.')
            st.dataframe(imported.head(25))
            st.dataframe(quality_report(imported))
        except Exception as exc:
            st.error(f'Import failed: {exc}')
    else:
        st.dataframe(df.head(10))
    if st.button('Reset to synthetic dataset'):
        st.session_state.dataset = sample_data()
        st.rerun()

elif page.startswith('09'):
    st.header('Interactive Visualization Studio')
    numeric = list(df.select_dtypes(include=np.number).columns)
    if numeric:
        x = st.selectbox('X axis', df.columns, index=0)
        y = st.selectbox('Y axis', numeric, index=min(1, len(numeric)-1))
        kind = st.selectbox('Chart', ['Scatter', 'Bar', 'Histogram', 'Box'])
        if kind == 'Scatter': fig = px.scatter(df, x=x, y=y)
        elif kind == 'Bar': fig = px.bar(df.groupby(x, as_index=False)[y].mean(), x=x, y=y)
        elif kind == 'Histogram': fig = px.histogram(df, x=y)
        else: fig = px.box(df, x=x, y=y)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info('Import a dataset with numeric columns to enable charts.')

elif page.startswith('10'):
    st.header('Data Quality Monitoring Platform')
    report = quality_report(df)
    st.metric('Duplicate rows', int(df.duplicated().sum()))
    st.metric('Missing cells', int(df.isna().sum().sum()))
    st.dataframe(report, width='stretch')
    a,b=st.columns(2)
    a.plotly_chart(px.bar(report,x='column',y='null_pct',color='null_pct',title='Missing values (%)'),width='stretch')
    b.plotly_chart(px.bar(report,x='column',y='distinct',color='distinct',title='Unique values by column'),width='stretch')
    
    if df.isna().any().any():
        st.plotly_chart(px.imshow(df.isna().astype(int).head(70).T, color_continuous_scale=['#1dd7ba','#fb5c83'], aspect='auto', title='Null map · first 70 rows', labels={'color':'Missing'}), width='stretch')
    else:
        st.success('All fields are complete: no missing values detected in this dataset.')
    st.download_button('Export quality report', csv_bytes(report), 'quality_report.csv')
    st.caption('Next production step: PostgreSQL validation history, configurable rules, alerting and scheduled runs.')

elif page.startswith('11'):
    st.header('ETL Pipeline Orchestrator')
    st.write('Demonstrate sequential ETL steps with timings and status; not a scheduler.')
    if st.button('Run ETL'):
        with st.status('Running pipeline', expanded=True) as status:
            st.write(f'Extract: {len(df)} source rows')
            transformed = clean_data(df)
            st.write(f'Transform: {len(transformed)} clean rows')
            with tempfile.TemporaryDirectory() as directory:
                count = persist_sqlite(transformed, str(Path(directory) / 'etl.db'))
                st.write(f'Load: {count} rows persisted to temporary SQLite database')
            status.update(label='Pipeline completed', state='complete')
        st.download_button('Export ETL result', csv_bytes(transformed), 'etl_result.csv')

elif page.startswith('12'):
    st.header('Data Enrichment & Augmentation Lab')
    st.write('Enrich customer records with derived features, then cluster behavioural profiles.')
    required = {'spend', 'visits'}
    if required.issubset(df.columns) and len(df) >= 3:
        enriched = df.copy()
        enriched['spend_per_visit'] = enriched['spend'] / enriched['visits'].replace(0, np.nan)
        features = enriched[['spend', 'visits']].fillna(0)
        clusters = st.slider('K-Means clusters', 2, min(8, len(df)), 3)
        enriched['cluster'] = KMeans(n_clusters=clusters, random_state=42, n_init=10).fit_predict(StandardScaler().fit_transform(features))
        st.dataframe(enriched.head(20))
        st.plotly_chart(px.scatter(enriched, x='visits', y='spend', color=enriched.cluster.astype(str), title='Behavioural clusters'), width='stretch')
        st.download_button('Download enriched data', csv_bytes(enriched), 'enriched.csv')
    else:
        st.info('This module requires spend and visits numeric columns and at least three rows.')

elif page.startswith('13'):
    st.header('Statistical Experimentation Lab')
    st.write('Compare randomized test/control conversion rates. This is a descriptive uplift calculator, not a causal inference engine.')
    c1, c2 = st.columns(2)
    with c1:
        n_test = st.number_input('Test users', min_value=1, value=1000)
        x_test = st.number_input('Test conversions', min_value=0, max_value=int(n_test), value=min(80, int(n_test)))
    with c2:
        n_control = st.number_input('Control users', min_value=1, value=1000)
        x_control = st.number_input('Control conversions', min_value=0, max_value=int(n_control), value=min(50, int(n_control)))
    result = uplift(int(x_test), int(n_test), int(x_control), int(n_control))
    a, b, c = st.columns(3)
    a.metric('Test conversion', f"{result['test_rate']:.2%}")
    b.metric('Control conversion', f"{result['control_rate']:.2%}")
    c.metric('Absolute lift', f"{result['absolute_lift_pp']:.2f} pp")
    st.write('Relative uplift:', f"{result['relative_uplift_pct']:.1f}%" if result['relative_uplift_pct'] is not None else 'Undefined (zero control rate)')
    bars=pd.DataFrame({'Group':['Test','Control'],'Conversion rate':[result['test_rate'],result['control_rate']]})
    st.plotly_chart(px.bar(bars,x='Group',y='Conversion rate',color='Group',text='Conversion rate',title='A/B conversion comparison'),width='stretch')
    st.caption('For causal claims, verify randomization, sample size, confidence intervals, statistical significance and guardrail metrics.')
