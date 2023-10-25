import pandas as pd
import numpy as np

# Given data and parameters, should be imported from CSV, but this makes it easier to share.
data = {
    "Round": list(range(1, 24)),
    "Race": [
        "Bahrain Grand Prix", "Saudi Arabian Grand Prix", "Australian Grand Prix", "Azerbaijan Grand Prix",
        "Miami Grand Prix", "Imola Grand Prix", "Monaco Grand Prix", "Spanish Grand Prix",
        "Canadian Grand Prix", "Austrian Grand Prix", "British Grand Prix", "Hungarian Grand Prix",
        "Belgian Grand Prix", "Dutch Grand Prix", "Italian Grand Prix", "Singapore Grand Prix",
        "Japanese Grand Prix", "Qatar Grand Prix", "United States Grand Prix", "Mexico City Grand Prix",
        "São Paulo Grand Prix", "Las Vegas Grand Prix", "Abu Dhabi Grand Prix"
    ],
    "Laptime (s)": [95.47, 91.8, 81.69, 106.4, 91.46, 79.33, 76.15, 85.61, 75.9, 67.81, 91, 82.1, 110.6, 73.68, 84.45, 106.46, 105, 85.04, 99.67, 81.87, 74.21, 94.5, 89.07],
    "Lap Distance (m)": [5356, 6098, 5229, 5948, 5337, 4870, 3281, 4635, 4312, 4289, 5812, 4343, 6933, 4236, 5757, 5004, 5810, 5384, 5444, 4244, 4250, 6201, 5222],
    "Number of Race Laps": [57, 50, 58, 51, 57, 63, 79, 66, 71, 71, 52, 70, 44, 72, 53, 61, 52, 57, 56, 72, 72, 49, 58],
    "Race Laptime Sensitivity (ms/kW per lap)": [22, 29, 29, 29, 21, 19, 10, 15, 18, 16, 30, 13, 33, 18, 33, 12, 28, 21, 25, 13, 19, 27, 24]
}

df = pd.DataFrame(data)

# Creating the "Lap Sensitivity" column, these values can be optimized
conditions = [
    df["Race Laptime Sensitivity (ms/kW per lap)"] > 25,
    df["Race Laptime Sensitivity (ms/kW per lap)"] < 15,
    (df["Race Laptime Sensitivity (ms/kW per lap)"] >= 15) & (df["Race Laptime Sensitivity (ms/kW per lap)"] <= 25)
]
choices = ["HIGH", "LOW", "NORMAL"]
df["Lap Sensitivity"] = np.select(conditions, choices, default='NORMAL')

# Parameters
PU_LIFE_LIMIT = 4750  # Life minus 1 race so that it is available for a race
RACE_DISTANCE = 750  # race weekend distance
PU_DEGRADATION = 5 / 1000  # kW/km
PUs_PER_SEASON = 4

# Initializing engine details, here you can add or recall engines, as well as define when they are available.
engines = {
    1: {"available_race": 1, "current_km": 0, "degradation": 0},
    2: {"available_race": 1, "current_km": 0, "degradation": 0},
    3: {"available_race": 11, "current_km": 0, "degradation": 0},
    4: {"available_race": 13, "current_km": 0, "degradation": 0}
}


# Function to find the best engine for a given race
def find_best_engine(round_number, lap_sensitivity):
    suitable_engines = [key for key, value in engines.items() if value["available_race"] <= round_number and value[
        "current_km"] + RACE_DISTANCE <= PU_LIFE_LIMIT]

    # TODO Should probably add an exception or error if PU_LIFE_LIMIT is exceeded and no engine is available.

    # If high sensitivity, prioritize freshest engine
    if lap_sensitivity == "HIGH":
        suitable_engines = sorted(suitable_engines, key=lambda x: engines[x]["current_km"])
    elif lap_sensitivity == "NORMAL":
        suitable_engines = sorted(suitable_engines, key=lambda x: engines[x]["degradation"])
    else:  # LOW sensitivity
        suitable_engines = sorted(suitable_engines, key=lambda x: engines[x]["current_km"], reverse=True)

    return suitable_engines[0] if suitable_engines else None


# Allocating engines to races
for index, row in df.iterrows():
    engine_choice = find_best_engine(row["Round"], row["Lap Sensitivity"])
    if engine_choice:
        df.at[index, "PU Chosen"] = engine_choice
        engines[engine_choice]["current_km"] += RACE_DISTANCE
        engines[engine_choice]["degradation"] += PU_DEGRADATION * RACE_DISTANCE
        df.at[index, "Engine Km"] = engines[engine_choice]["current_km"]
        delta = row["Race Laptime Sensitivity (ms/kW per lap)"] * engines[engine_choice]["degradation"] * row[
            "Number of Race Laps"]
        df.at[index, "Race Delta (Ms)"] = delta

print(df)
df.to_csv("lap_sensitivity_race_strategy_scenario1.csv", index=False)
