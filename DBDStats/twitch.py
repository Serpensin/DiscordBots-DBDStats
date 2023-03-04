import requests as r
import json



class TwitchAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = self.get_twitch_app_access_token()
        self.streams = "https://api.twitch.tv/helix/streams"
        self.users = "https://api.twitch.tv/helix/users"
        self.top = "https://api.twitch.tv/helix/games/top"


    def get_twitch_app_access_token(self):
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        response = r.post(url, params=params)

        if response.status_code == 200:
            access_token = response.json()["access_token"]
            return access_token
        else:
            print(f"Failed to get access token. Status code: {response.status_code}")
            return None


    def check_access_token(self):
        headers = {"Authorization": f"OAuth {self.access_token}"}
        url = "https://id.twitch.tv/oauth2/validate"
        response = r.get(url, headers=headers)

        if response.status_code == 200:
            return True
        else:
            return False


    def get_game_id(self, game_name):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Client-ID": self.client_id
        }
        url = f"https://api.twitch.tv/helix/games?name={game_name}"
        response = r.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()["data"]
            if len(data) > 0:
                game_id = data[0]["id"]
                return game_id
            else:
                return f"No game found with name {game_name}"
        else:
            return f"Failed to get game ID for {game_name} with status code {response.status_code}"


    def get_category_stats(self, category_id):
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}
        params = {"game_id": category_id}
    
        total_viewer_count = 0
        total_stream_count = 0
        average_viewer_count = 0
        category_rank = 0
    
        response = r.get(self.streams, headers=headers, params=params)
        if response.status_code != 200:
            return None
        data = json.loads(response.text)
    
        for stream in data["data"]:
            total_viewer_count += stream["viewer_count"]
            total_stream_count += 1
    
        while "cursor" in data.get("pagination", {}):
            params["after"] = data["pagination"]["cursor"]
            response = r.get(self.streams, headers=headers, params=params)
            data = json.loads(response.text)
            for stream in data["data"]:
                total_viewer_count += stream["viewer_count"]
                total_stream_count += 1
    
        if total_stream_count > 0:
            average_viewer_count = total_viewer_count / total_stream_count
    
        response = r.get(self.top, headers=headers, params={"first": "100"})
        if response.status_code != 200:
            return None
        data = json.loads(response.text)
    
        for i, category in enumerate(data["data"]):
            if category["id"] == category_id:
                category_rank = i + 1
                break
    
        response_obj = {
            "viewer_count": total_viewer_count,
            "stream_count": total_stream_count,
            "average_viewer_count": average_viewer_count,
            "category_rank": category_rank
        }
    
        return response_obj


    def get_top_streamers(self, category_id):
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}
        params = {"game_id": category_id, "first": "4"}
        response = r.get(self.streams, headers=headers, params=params)
    
        if response.status_code == 200:
            data = json.loads(response.text)
            top_streamers = {}
            for i, stream in enumerate(data["data"]):
                streamer_name = stream["user_name"]
                viewer_count = stream["viewer_count"]
                follower_count = stream["user_id"]
                stream_title = stream["title"]
                started_at = stream["started_at"]
                language = stream["language"]
                thumbnail_url = stream["thumbnail_url"].format(width="1920", height="1080")
                link = f"https://www.twitch.tv/{streamer_name}"
                top_streamers[i] = {"streamer": streamer_name,
                                      "viewer_count": viewer_count,
                                      "follower_count": follower_count,
                                      "title": stream_title,
                                      "started_at": started_at,
                                      "language": language,
                                      "thumbnail": thumbnail_url,
                                      "link": link}
            return top_streamers
        else:
            return(f"Error {response.status_code}: Could not retrieve top streamers for category {category_id}")


    def get_api_points(self):
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}
        response = r.get(self.users, headers=headers)
        api_points = int(response.headers.get("Ratelimit-Remaining"))
        return api_points


    def get_category_image(self, category_id):
        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.access_token}"}
        params = {"id": category_id}
        url = f"https://api.twitch.tv/helix/games?id={category_id}"
        response = r.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = json.loads(response.text)
            image_url = data["data"][0]["box_art_url"].format(width="320", height="440")
            return image_url
        else:
            return(f"Error {response.status_code}: Could not retrieve image for category {category_id}")
