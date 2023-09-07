from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
import skfuzzy as fuzz

app = Flask(__name__)

mood = ""
year = ""
genre = ""

# Define the universe of discourse for each attribute

tempo = np.arange(50, 201)
energy = np.arange(0, 101)
valence = np.arange(0, 101)

tempo_lo = fuzz.trapmf(tempo, [50, 50, 90, 120])
tempo_md = fuzz.trapmf(tempo, [90, 115, 135, 160])
tempo_hi = fuzz.trapmf(tempo, [130, 160, 200, 200])

energy_lo = fuzz.trapmf(energy, [0, 0, 30, 45])
energy_md = fuzz.trapmf(energy, [30, 45, 55, 70])
energy_hi = fuzz.trapmf(energy, [55, 70, 100, 100])

valence_lo = fuzz.trapmf(valence, [0, 0, 30, 45])
valence_md = fuzz.trapmf(valence, [30, 45, 55, 70])
valence_hi = fuzz.trapmf(valence, [55, 70, 100, 100])


@app.route("/", methods=["GET", "POST"])
def get_mood():
    global mood
    if request.method == "POST":
        mood = request.form["mood"]
        return redirect(url_for("get_genre"))
    return render_template("mood.html")

@app.route("/genre", methods=["GET", "POST"])
def get_genre():
    global genre
    if request.method == "POST":
        genre = request.form["genre"]
        return redirect(url_for("get_year"))
    elif request.method == "GET" and mood:
        return render_template("genre.html")
    else:
        return redirect(url_for("get_mood"))

@app.route("/year", methods=["GET", "POST"])
def get_year():
    global year
    if request.method == "POST":
        year = request.form["year"]
        return redirect(url_for("recommend"))
    elif request.method == "GET" and mood and genre:
        return render_template("year.html")
    else:
        return redirect(url_for("get_mood"))

@app.route("/recommend")
def recommend():
    global distances, min_dist_index, df, temp_distances
    # Load the dataset
    df = pd.read_csv('./songs.csv', delimiter=',')

    if genre != "anygenre":
        df = df[df['genre'] == genre]

    # Filter the songs by year.
    if year == "2010s":
        df = df[(df['year'] >= 2010) & (df['year'] < 2020)]
    elif year == "2000s":
        df = df[(df['year'] >= 2000) & (df['year'] < 2010)]
    elif year == "2020s":
        df = df[(df['year'] >= 2020) & (df['year'] < 2030)]


    if mood == 'happy':
        tempo_degrees = [0, 0, 1]
        energy_degrees = [0, 0, 1]
        valence_degrees = [0, 0, 1]
    elif mood == 'neutral':
        tempo_degrees = [0, 1, 0]
        energy_degrees = [0, 1, 0]
        valence_degrees = [0, 1, 0]
    elif mood == 'sad':
        tempo_degrees = [1, 0, 0]
        energy_degrees = [1, 0, 0]
        valence_degrees = [1, 0, 0]

    # Calculate how different each song is from their mood_degrees values.
    distances = []
    temp_distances = []
    for i, row in df.iterrows():
        dist_tempo = abs(tempo_degrees[0] - fuzz.interp_membership(tempo, tempo_lo, row['tempo'])) + \
                     abs(tempo_degrees[1] - fuzz.interp_membership(tempo, tempo_md, row['tempo'])) + \
                     abs(tempo_degrees[2] - fuzz.interp_membership(tempo, tempo_hi, row['tempo']))
        dist_energy = abs(energy_degrees[0] - fuzz.interp_membership(energy, energy_lo, row['energy'])) + \
                      abs(energy_degrees[1] - fuzz.interp_membership(energy, energy_md, row['energy'])) + \
                      abs(energy_degrees[2] - fuzz.interp_membership(energy, energy_hi, row['energy']))
        dist_valence = abs(valence_degrees[0] - fuzz.interp_membership(valence, valence_lo, row['valence'])) + \
                       abs(valence_degrees[1] - fuzz.interp_membership(valence, valence_md, row['valence'])) + \
                       abs(valence_degrees[2] - fuzz.interp_membership(valence, valence_hi, row['valence']))
        dist = dist_tempo + dist_energy + dist_valence
        distances.append(dist)
        temp_distances.append(dist)
    # Find the index of the song with the smallest distance.
    min_dist_index = distances.index(min(distances))

    print("inputs: " + "mood= " + mood + " " + "genre= " + genre + " " + "year= " + year + "\n");
    print("Recommended song: \n")
    print(df.iloc[min_dist_index])
    temp_distances.remove(min(temp_distances)) # To recommend another song.
    return render_template('recommendation.html', recommended_song = df.iloc[min_dist_index]['artist'] + ' - ' + df.iloc[min_dist_index]['title'])


def get_next_recommendation():
    if len(temp_distances) == 0:
        return None
    else:
        temp_distances_sorted = sorted(temp_distances)
        min_dist = temp_distances_sorted[0]
        min_dist_index = distances.index(min_dist)
        temp_distances.remove(min_dist)
        print("Recommended song: \n")
        print(df.iloc[min_dist_index])
        return df.iloc[min_dist_index]['artist'] + ' - ' + df.iloc[min_dist_index]['title']

@app.route('/recommend_another')
def recommend_another():
    new_recommendation = get_next_recommendation()
    if new_recommendation is not None:
        return render_template('recommendation.html', recommended_song = new_recommendation)
    else:
        return render_template('recommendation.html', warning = "There are no more recommendations.")

if __name__ == "__main__":
    app.run(debug=True)



