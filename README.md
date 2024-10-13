# YouTube Playlist Duration Calculator

This is a web application that calculates the total duration of all the videos in a YouTube playlist. The application is built with Python and Flask on the backend, and HTML and CSS on the frontend. It uses the YouTube Data API v3 to fetch video data from the playlist.

## Features
- Input a YouTube playlist URL.
- The app fetches and calculates the total duration of all videos in the playlist.
- Displays the combined duration in hours, minutes, and seconds.

## Technologies Used
### Backend
- **Python**: Used for the main application logic.
- **Flask**: A lightweight web framework to handle API requests and responses.
- **YouTube Data API v3**: To fetch the playlist data including video durations.

### Frontend
- **HTML**: For structuring the web pages.
- **CSS**: For styling the web pages and making the UI user-friendly.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/LordNydorf/YTplaylistCalc.git
    cd YTplaylistCalc
    ```

2. Create a virtual environment and activate it:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Obtain an API key from [Google Cloud Console](https://console.cloud.google.com/) for YouTube Data API v3. Enable the API and copy the key.

5. Set up your environment variables. Create a `.env` file in the root directory with your API key:
    ```bash
    YOUTUBE_API_KEY=your_youtube_api_key
    ```

6. Run the Flask development server:
    ```bash
    flask run
    ```

7. Open your browser and visit `http://127.0.0.1:5000`.

## Usage

1. Paste the URL of a YouTube playlist in the input field.
2. Click on the "Get Total Duaration" button.
3. The app will display the total duration of the playlist in a human-readable format (hours, minutes, seconds).

## Example

- Input: A YouTube playlist URL like `https://www.youtube.com/playlist?list=PLabc123...`
- Output: Total Duration: **5 hours 24 minutes 36 seconds**


## Future Improvements
- Display more detailed statistics such as average video length, total number of videos, etc.
- Support for public and private playlists (with OAuth 2.0 authentication).
- Mobile responsive design for a better user experience on different devices.
