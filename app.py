from flask import Flask, render_template, request, redirect, url_for
import plotly.graph_objs as go
import sqlite3
import numpy as np
import json
import plotly.utils


app = Flask(__name__)

# Initialize SQLite Database
DATABASE = 'mismatch.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            country TEXT,
            total_score INTEGER,
            group1_score INTEGER,
            group2_score INTEGER,
            group3_score INTEGER,
            group4_score INTEGER,
            group5_score INTEGER,
            group6_score INTEGER,
            group7_score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Collect form data
    name = request.form['name']
    age = int(request.form['age'])
    gender = request.form['gender']
    country = request.form['country']
    question_order = json.loads(request.form['question_order'])
    scores = [int(item['score']) for item in question_order]
    #scores = [int(request.form[f'score{i}']) for i in range(1, 37)]  # Adjust range for all questions
    reverse_indices = [5, 11, 29]  # Corresponds to questions 6, 12, 30
    for idx in reverse_indices:
        scores[idx] = 8 - scores[idx]

    print(f"Received data: Name: {name}, Age: {age}, Gender: {gender}, Country: {country}")
    print(f"Scores: {scores}")

    # Define group indices
    group_indices = {
        'group1': [0, 1, 9, 10, 11],
        'group2': [6, 8, 5, 4],
        'group3': [25, 26, 27, 28, 29],
        'group4': [31, 32, 33],
        'group5': [7, 15, 16, 17, 18, 30],
        'group6': [19, 20, 21, 22, 3, 34],
        'group7': [2, 12, 13, 14, 23, 24,  35]
    }


    # Calculate group scores with the required formula
    group_scores = {}
    for group, indices in group_indices.items():
        group_sum = sum(scores[i] for i in indices)
        group_length = len(indices)
        group_scores[group] = (group_sum * 100) / (7 * group_length)

    # Calculate total score as the average of group scores
    total_score = sum(group_scores.values()) / len(group_scores)

    # Insert data into database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO participants (
            name, age, gender, country, total_score, 
            group1_score, group2_score, group3_score, 
            group4_score, group5_score, group6_score, group7_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, age, gender, country, total_score, 
          group_scores['group1'], group_scores['group2'], group_scores['group3'], 
          group_scores['group4'], group_scores['group5'], group_scores['group6'], group_scores['group7']))
    conn.commit()
    conn.close()

    return redirect(url_for('result', score=total_score))

@app.route('/result')
def result():
    score = float(request.args.get('score'))

    # Retrieve the latest participant's group scores and total score
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT group1_score, group2_score, group3_score, group4_score, group5_score, group6_score, group7_score FROM participants ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()

    group_scores = {
        'group1': row[0], 'group2': row[1], 'group3': row[2],
        'group4': row[3], 'group5': row[4], 'group6': row[5],
        'group7': row[6]
    }

    # Retrieve all scores for population statistics
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT group1_score, group2_score, group3_score, group4_score, group5_score, group6_score, group7_score, total_score FROM participants')
    all_rows = cursor.fetchall()
    conn.close()

    # Calculate means for each group and total
    means = {
        'group1': np.mean([row[0] for row in all_rows]),
        'group2': np.mean([row[1] for row in all_rows]),
        'group3': np.mean([row[2] for row in all_rows]),
        'group4': np.mean([row[3] for row in all_rows]),
        'group5': np.mean([row[4] for row in all_rows]),
        'group6': np.mean([row[5] for row in all_rows]),
        'group7': np.mean([row[6] for row in all_rows]),
        'total': np.mean([row[7] for row in all_rows]),
    }

    # Calculate percentiles for each group and total score
    percentiles = {}
    for group, idx in zip(group_scores.keys(), range(7)):
        sorted_scores = sorted([row[idx] for row in all_rows])
        count_less_equal = sum(1 for s in sorted_scores if s <= group_scores[group])
        percentiles[group] = (count_less_equal / len(sorted_scores)) * 100 if sorted_scores else 0

    sorted_total_scores = sorted([row[7] for row in all_rows])
    count_total_less_equal = sum(1 for s in sorted_total_scores if s <= score)
    percentiles['total'] = (count_total_less_equal / len(sorted_total_scores)) * 100 if sorted_total_scores else 0

    # Generate population curve
    hist_data = [go.Histogram(x=[row[7] for row in all_rows], nbinsx=30)]


    layout = go.Layout(
        title='Population Mismatch Curve',
        xaxis=dict(title='Total Mismatch Scores'),
        yaxis=dict(title='Frequency'),
        shapes=[
            dict(type='line', x0=score, x1=score, y0=0, y1=max(np.histogram([row[7] for row in all_rows], bins=30)[0]), line=dict(color='red'))
        ],
        annotations=[
            dict(
                x=score,  # x-coordinate for the annotation (the score value)
                y=max(np.histogram([row[7] for row in all_rows], bins=30)[0]) / 2,  # y-coordinate, adjust for placement
                text="You lie here!",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-70,
                font=dict(color='red', size=14)
            )
        ]
    )


    fig = go.Figure(data=hist_data, layout=layout)
    #graphJSON = fig.to_json()
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template(
        'result.html',
        score=score,
        graphJSON=graphJSON,
        percentile=percentiles['total'],
        group_scores=group_scores,
        means=means,
        percentiles=percentiles
    )



if __name__ == '__main__':
    app.run(debug=True)
