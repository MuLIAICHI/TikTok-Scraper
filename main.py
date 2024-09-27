import streamlit as st
from tikapi import TikAPI, ValidationException, ResponseException
from datetime import datetime
import csv
import time
import io
import pandas as pd

# Initialize TikAPI with the API key from secrets
api = TikAPI(st.secrets["tiktok_api_key"])

def get_tiktok_data_by_hashtag(hashtag, max_videos, country):
    video_data = []
    cursor = None
    hashtag_id = None

    try:
        # First request to get hashtag ID
        st.write(f"Attempting to fetch hashtag ID for: {hashtag}")
        response = api.public.hashtag(name=hashtag, country=country)
        data = response.json()
        
        # st.write("Full API response:", data)  # This will show the full API response
        
        if data.get('status') != 'success':
            st.error(f"Error: {data.get('message', 'Unknown error')}")
            st.error(f"Full error response: {data}")
            return []

        hashtag_id = data.get('challengeInfo', {}).get('challenge', {}).get('id')
        if not hashtag_id:
            st.error("Failed to retrieve hashtag ID")
            st.error(f"challengeInfo structure: {data.get('challengeInfo', {})}")
            return []

        st.write(f"Successfully retrieved hashtag ID: {hashtag_id}")
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        while len(video_data) < max_videos:
            # Subsequent requests using the hashtag ID
            st.write(f"Fetching videos for hashtag ID: {hashtag_id}, Cursor: {cursor}")
            response = api.public.hashtag(id=hashtag_id, cursor=cursor, country=country, count=30)
            data = response.json()
            
            # st.write("Video fetch response:", data)
            
            if data.get('status') != 'success':
                st.error(f"Error fetching videos: {data.get('message', 'Unknown error')}")
                break

            for item in data.get('itemList', []):
                video_details = {
                    'post_id': item.get('id', ''),
                    'post_content': item.get('desc', ''),
                    'source_post_id': item.get('id', ''),
                    'post_url': f"https://www.tiktok.com/@{item.get('author', {}).get('uniqueId', '')}/video/{item.get('id', '')}",
                    'post_description': item.get('desc', ''),
                    'source': 'TikTok',
                    'likes_count': item.get('stats', {}).get('diggCount', 0),
                    'shares_count': item.get('stats', {}).get('shareCount', 0),
                    'plays_count': item.get('stats', {}).get('playCount', 0),
                    'comments_count': item.get('stats', {}).get('commentCount', 0),
                    'post_created': datetime.fromtimestamp(item.get('createTime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                    'username': item.get('author', {}).get('uniqueId', ''),
                    'profile_url': f"https://www.tiktok.com/@{item.get('author', {}).get('uniqueId', '')}",
                    'play_url': item.get('video', {}).get('playAddr', ''),
                    'is_visible': 'true'
                }
                
                video_data.append(video_details)
                
                progress = len(video_data) / max_videos
                progress_bar.progress(progress)
                status_text.text(f"Fetched {len(video_data)} out of {max_videos} videos")
                
                if len(video_data) >= max_videos:
                    break
                
                # Add a small delay to avoid hitting rate limits
                time.sleep(1)
            
            if not data.get('hasMore'):
                st.write("No more videos to fetch")
                break
            
            cursor = data.get('cursor')
            st.write(f"Next cursor: {cursor}")

        return video_data

    except ValidationException as e:
        st.error(f"Validation error: {e}, Field: {e.field}")
        return []
    except ResponseException as e:
        st.error(f"Response content: {e.response.content}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.error(f"Error type: {type(e)}")
        return []

def main():
    st.title("TikTok Scraper")

    # User inputs
    hashtags = st.text_input("Enter hashtags (comma-separated):", "food")
    country = st.text_input("Enter country code (e.g., gb, us):", "gb")
    max_videos = st.number_input("Number of videos per hashtag:", min_value=1, max_value=100, value=30)

    if st.button("Start Scraping"):
        hashtag_list = [tag.strip() for tag in hashtags.split(',')]
        
        for hashtag in hashtag_list:
            st.subheader(f"Scraping data for {hashtag}")
            video_data = get_tiktok_data_by_hashtag(hashtag, max_videos, country)
            
            if video_data:
                df = pd.DataFrame(video_data)
                st.dataframe(df)

                # Provide download link
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"Download data for {hashtag}",
                    data=csv,
                    file_name=f"tiktok_data_{hashtag}_{country}.csv",
                    mime="text/csv"
                )
            else:
                st.warning(f"No data found for {hashtag}")

        st.success("Scraping completed!")

if __name__ == "__main__":
    main()