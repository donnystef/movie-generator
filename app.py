import openai
import requests
import os
import re
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)

#TMDB_API_KEY = 'c8bf776db347aae47be1fb1fb57a5fe9'
#OPENAI_API_KEY = 'sk-ABt0WlS6CODODSvvIucfI6RBK2xy8R0zu3tQuSgzFWT3BlbkFJBfein0lNcwSrXb33FMC3rA3KypTBCTHrf5OYF2Y_kA'
#openai.api_key = OPENAI_API_KEY

TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '').strip()
openai.api_key = os.environ.get('OPENAI_API_KEY', '').strip()

def reset_conversation():
    """Resets conversation context."""
    return [{'role': 'system', 'content': 'You are a helpful movie assistant. Never recommend any movie that contains or is categorized as erotic, pornographic, sexually explicit, or adult in nature. Only recommend safe-for-work, non-sexual content. Ensure all movies are appropriate for a general audience. Your suggestions must avoid NSFW, adult, or inappropriate material.'}]

def format_movie_title_for_url(title):
    """Convert movie title to a format suitable for URLs."""
    formatted_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)  # Remove special characters
    formatted_title = formatted_title.lower().replace(" ", "-")  # Convert spaces to hyphens
    return formatted_title

def generate_movie_titles_and_streaming(user_description):
    """Generate movie titles and predict where they can be streamed."""
    prompt = f"""
    Based on the description: '{user_description}', recommend 5 distinct movies.
    Also, predict where each movie is available for streaming (Netflix, Disney+, Prime Video, Hulu, or HBO Max).
    Provide the response in JSON format like this:
    [
        {{"title": "Movie Title", "platform": "Netflix"}},
        {{"title": "Another Movie", "platform": "Hotstar"}}
    ]
    """
    
    conversation = reset_conversation()
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation + [{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.7
    )
    
    movie_data = response['choices'][0]['message']['content']
    
    # Convert AI response to a list of dictionaries
    import json
    try:
        movies = json.loads(movie_data)
    except json.JSONDecodeError:
        movies = []

    return movies

def get_movie_recommendations(user_description):
    """Fetch movie details from TMDb and generate streaming links."""
    movies = []
    generated_movies = generate_movie_titles_and_streaming(user_description)
    
    for movie in generated_movies:
        title = movie['title']
        platform = movie['platform']

        # Generate YouTube trailer link
        youtube_search_query = f"{title} Official Trailer"
        youtube_trailer_link = f"https://www.youtube.com/results?search_query={youtube_search_query.replace(' ', '+')}"

        # Generate Layarkaca21 link
        layarkaca_link = f"https://www.justwatch.com/id/movie/{format_movie_title_for_url(title)}"

        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
        response = requests.get(search_url)

        if response.ok:
            movie_data = response.json()
            if movie_data['results']:
                best_match = movie_data['results'][0]
                movies.append({
                    'title': best_match['title'],
                    'poster': f"https://image.tmdb.org/t/p/w500{best_match['poster_path']}" if best_match.get('poster_path') else None,
                    'rating': best_match.get('vote_average', 0.0),
                    'description': best_match.get('overview', 'No description available.'),
                    'watch_link': youtube_trailer_link,  # Replaced with YouTube link
                    'platform': platform,
                    'layarkaca_link': layarkaca_link
                })


    return movies

@app.route('/', methods=['GET', 'POST'])
def index():
    recommended_movies = []

    if request.method == 'POST':
        # Get user's movie description
        user_description = request.form['description']

        # Get selected filters from checkboxes (returns a list)
        selected_filters = request.form.getlist('filters')

        # If any filters selected, append them to the prompt
        if selected_filters:
            filter_text = ", ".join(selected_filters)
            user_description = f"I'm looking for a movie recommendation based on this: \"{user_description}\". I’d prefer something with elements of {filter_text}."
        else:
            user_description = f"I'm looking for a movie recommendation based on this: \"{user_description}\"."

        # Call your recommendation function with the tuned prompt
        recommended_movies = get_movie_recommendations(user_description)

    return render_template('index.html', movies=recommended_movies)

def reset():
    session.clear()
    return redirect('/')

#if __name__ == '__main__':
    #app.run(debug=True)

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=10000)

print("DEBUG: OpenAI API key is set?", bool(openai.api_key))
