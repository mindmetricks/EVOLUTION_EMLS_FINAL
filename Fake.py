import sqlite3
import random
import numpy as np

# Database name
DATABASE = 'mismatch.db'

# Number of fake entries to generate
NUM_ENTRIES = 10000

# Possible random values for other fields
NAMES = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Hannah', 'Ian', 'Jane']
GENDERS = ['Male', 'Female', 'Other']
COUNTRIES = ['USA', 'UK', 'India', 'Germany', 'France', 'Canada', 'Australia', 'Japan', 'China', 'Brazil']

# Connect to the database
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Function to generate a random score with mean 50 and std deviation 20
def generate_score():
    score = np.random.normal(50, 20)  # Mean of 50, std deviation of 20
    return max(0, min(100, score))  # Clamp scores to the range 0-100

# Generate and insert fake entries
for _ in range(NUM_ENTRIES):
    name = random.choice(NAMES)
    age = random.randint(18, 70)  # Random age between 18 and 70
    gender = random.choice(GENDERS)
    country = random.choice(COUNTRIES)
    
    # Generate group scores and calculate total score as the average
    group1 = generate_score()
    group2 = generate_score()
    group3 = generate_score()
    group4 = generate_score()
    group5 = generate_score()
    group6 = generate_score()
    group7 = generate_score()
    total_score = np.mean([group1, group2, group3, group4, group5, group6, group7])
    
    # Insert the fake entry into the database
    cursor.execute('''
        INSERT INTO participants (
            name, age, gender, country, total_score, 
            group1_score, group2_score, group3_score, 
            group4_score, group5_score, group6_score, group7_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, age, gender, country, total_score, 
          group1, group2, group3, group4, group5, group6, group7))

# Commit changes and close the connection
conn.commit()
conn.close()

print(f"{NUM_ENTRIES} fake entries successfully added to the database!")
