from tikapi import TikAPI, ValidationException, ResponseException
from datetime import datetime
import csv
import time

def get_tiktok_data_by_hashtag(api_key, hashtag, max_videos=100, country=None):
    api = TikAPI(api_key)
    video_data = []
    cursor = None
    hashtag_id = None

    try:
        # First request to get hashtag ID
        response = api.public.hashtag(name=hashtag, country=country)
        data = response.json()
        
        if data.get('status') != 'success':
            print(f"Error: {data.get('message', 'Unknown error')}")
            return []

        hashtag_id = data['challengeInfo']['challenge']['id']
        
        while len(video_data) < max_videos:
            # Subsequent requests using the hashtag ID
            response = api.public.search(
            category="general",
            query=hashtag,
            country=country,
            )
            data = response.json()
            
            if data.get('status') != 'success':
                print(f"Error: {data.get('message', 'Unknown error')}")
                break

            for item in data.get('itemList', []):
                video_details = {
                    'description': item.get('desc', ''),
                    'hashtags': ', '.join([challenge['title'] for challenge in item.get('challenges', [])]),
                    'date_posted': datetime.fromtimestamp(item.get('createTime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                    'views': item.get('stats', {}).get('playCount', 0),
                    'likes': item.get('stats', {}).get('diggCount', 0),
                    'comments_count': item.get('stats', {}).get('commentCount', 0),
                    'shares': item.get('stats', {}).get('shareCount', 0),
                    'video_url': f"https://www.tiktok.com/@{item.get('author', {}).get('uniqueId', '')}/video/{item.get('id', '')}",
                    'country': item.get('author', {}).get('region', country or 'Unknown')
                }
                
                # Fetch comments separately
                try:
                    comments_response = api.public.commentsList(media_id=item['id'], country=country)
                    comments_data = comments_response.json()
                    comments = [comment['text'] for comment in comments_data.get('comments', [])]
                    video_details['comments'] = '; '.join(comments[:5])  # Joining first 5 comments with semicolon
                except Exception as e:
                    print(f"Error fetching comments: {e}")
                    video_details['comments'] = "Unable to fetch comments"
                
                video_data.append(video_details)
                
                if len(video_data) >= max_videos:
                    break
                
                # Add a small delay to avoid hitting rate limits
                time.sleep(1)
            
            if not data.get('hasMore'):
                break
            
            cursor = data.get('cursor')

        return video_data

    except ValidationException as e:
        print(f"Validation error: {e}, Field: {e.field}")
        return []
    except ResponseException as e:
        print(f"Response error: {e}, Status code: {e.response.status_code}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

def save_to_csv(data, filename):
    if not data:
        print("No data to save.")
        return
    
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

# Usage example
api_key = "uEjS9nBswJKmG7GZGMG9ppSxQCVMk1M6JVKPeAQYdXd6Ona4"
hashtag = "food"
max_videos = 30
country = "gb"  # Specify the country, e.g., "us" for United States
output_filename = f"tiktok_data_{hashtag}_{country}.csv"

print(f"Fetching TikTok data for hashtag: '#{hashtag}' in country: {country}")
video_data = get_tiktok_data_by_hashtag(api_key, hashtag, country)

if video_data:
    print(f"Found {len(video_data)} videos. Saving to {output_filename}")
    save_to_csv(video_data, output_filename)
    print("Data saved successfully!")
else:
    print("No data found or an error occurred.")