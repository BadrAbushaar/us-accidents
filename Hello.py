import pandas as pd
from datetime import datetime
import numpy as np 
import streamlit as st
import plotly.express as px

df = pd.read_csv("reduced_us_accidents.csv", nrows=500000)

df['Start_Time'] = pd.to_datetime(df['Start_Time'])
df['End_Time'] = pd.to_datetime(df['End_Time'])
df['Weather_Timestamp'] = pd.to_datetime(df['Weather_Timestamp'])

# Dropping useless features
df.drop(['Source', 'ID','Description','Distance(mi)', 'End_Time', 'End_Lat', 'End_Lng', 'Weather_Timestamp', 'Wind_Chill(F)'], axis=1, inplace=True)

# Clean up wind direction feature
df.loc[df['Wind_Direction']=='Calm','Wind_Direction'] = 'CALM'
df.loc[(df['Wind_Direction']=='West')|(df['Wind_Direction']=='WSW')|(df['Wind_Direction']=='WNW'),'Wind_Direction'] = 'W'
df.loc[(df['Wind_Direction']=='South')|(df['Wind_Direction']=='SSW')|(df['Wind_Direction']=='SSE'),'Wind_Direction'] = 'S'
df.loc[(df['Wind_Direction']=='North')|(df['Wind_Direction']=='NNW')|(df['Wind_Direction']=='NNE'),'Wind_Direction'] = 'N'
df.loc[(df['Wind_Direction']=='East')|(df['Wind_Direction']=='ESE')|(df['Wind_Direction']=='ENE'),'Wind_Direction'] = 'E'
df.loc[df['Wind_Direction']=='Variable','Wind_Direction'] = 'VAR'

# Adding new datetime features
df['Year'] = df['Start_Time'].dt.year
df['Month'] = df['Start_Time'].dt.month
df['Weekday'] = df['Start_Time'].dt.weekday
df['Day'] = df['Start_Time'].dt.day
df['Hour'] = df['Start_Time'].dt.hour
df['Minute'] = df['Start_Time'].dt.minute
df = df.dropna(subset=['City','Zipcode','Airport_Code', 'Sunrise_Sunset','Civil_Twilight','Nautical_Twilight','Astronomical_Twilight'])


# Streamlit App
st.set_page_config(layout="wide")
st.title('US Accidents Analysis')
col1, col2 = st.columns(2)
color_map = {
    1: [153, 204, 255],  
    2: [255, 229, 153],  
    3: [255, 178, 102], 
    4: [255, 51, 51]     
}
df['Color'] = df['Severity'].map(color_map)

# User Inputs
with st.sidebar:
    st.title('Filters')
    selected_year = st.slider('Select a range of years', 2016, 2023, (2016, 2023))
    selected_state = st.selectbox('Select a state', ["Select a state"] + sorted(df['State'].unique()))
    selected_time = st.radio('Select a time', ["All", "Day", "Night"])

filtered_df = df

start_year, end_year = selected_year
filtered_df = filtered_df[filtered_df['Year'].between(start_year, end_year)]

if selected_state != "Select a state":
    filtered_df = filtered_df[filtered_df['State'] == selected_state]

if selected_time == "Day":
    filtered_df = filtered_df[filtered_df['Sunrise_Sunset'] == 'Day']
elif selected_time == "Night":
    filtered_df = filtered_df[filtered_df['Sunrise_Sunset'] == 'Night']

# Visualizations

# Accident Density Map
with col1:
    st.subheader('Accident Density Map')
    st.map(filtered_df, latitude='Start_Lat', longitude='Start_Lng', color='Color', use_container_width=True)
    st.caption("Color indicates the severity of the accident")
    st.divider()

# Accident by Weather Condition
    st.subheader('Accident by Weather Condition')
    agg_df = filtered_df.groupby(['Weather_Condition', 'Severity']).size().reset_index(name='Accident Count')
    accidentsByCondition = agg_df.groupby('Weather_Condition')['Accident Count'].sum().reset_index()
    accidentsByCondition = accidentsByCondition.sort_values(by='Accident Count', ascending=False)
    topAccidents = accidentsByCondition.head(15)['Weather_Condition']
    agg_df = agg_df[agg_df['Weather_Condition'].isin(topAccidents)]
    agg_df = agg_df.sort_values(by='Accident Count', ascending=False)
    fig = px.bar(agg_df, x='Weather_Condition', y='Accident Count', color='Severity')
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Top 15 weather conditions with the most accidents")
    st.divider()

# Accident Severity Trend by Year
with col2:
    st.subheader('Accident Severity Trend by Year')
    severity_counts = filtered_df.groupby(['Year', 'Severity']).size().unstack(fill_value=0)
    fig = px.area(severity_counts, labels={'value':'Number of Accidents', 'variable':'Severity Level'})  
    fig.update_layout(
        xaxis=dict(tickmode='array', tickvals=severity_counts.index, ticktext=[str(year) for year in severity_counts.index])
    )
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    st.divider()

    # Accident Heatmap
    st.subheader('Accident Heatmap')
    heatmap_data = filtered_df.groupby(['Weekday', 'Hour']).size().reset_index(name='Accident_Count')

    all_hours = pd.DataFrame(list(range(24)), columns=['Hour'])
    heatmap_data = (heatmap_data.set_index(['Weekday', 'Hour'])
        .reindex(pd.MultiIndex.from_product([heatmap_data['Weekday'].unique(), all_hours['Hour']], names=['Weekday', 'Hour']), fill_value=0).reset_index()
    )

    heatmap_data = heatmap_data.pivot(index='Weekday', columns='Hour', values='Accident_Count').fillna(0)

    fig = px.imshow(heatmap_data,
                    labels=dict(x="Hour of Day", y="Day of Week", color="Accident Count"),
                    x=list(range(24)), 
                    y=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                    aspect="auto",
                    color_continuous_scale='agsunset')
    st.plotly_chart(fig, use_container_width=True)


