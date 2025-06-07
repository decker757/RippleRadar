from matplotlib import pyplot as plt
import pandas as pd
import requests

#bar chart to show timeline on like how much he spend per day/week/month



#pie chart showing how much he transacts based on account

#account balance history



#boxplot or histogram to show 25%/50%/75%

#hexbin

#stackplot cumu

#boxplot on time spent




# Replace with your actual address
import requests


url = "http://127.0.0.1:5000/api/trustlines_visualised?address=rw3KBqdUkFY6hkTihgRMjspcyx34Ma5SDj"

response = requests.get(url)
print("Status code:", response.status_code)
print("Response text:", response.text)  # Optional: verify the JSON response

data = response.json()

# Create DataFrame
df = pd.DataFrame(data["Trustlines"])

# Convert numeric fields
df["balance"] = df["balance"].astype(float)
df["limit"] = df["limit"].astype(float)

# Group by currency and sum numeric columns
grouped = df.groupby("currency", as_index=False).sum()

print(grouped)

# Plot the grouped data
ax = grouped.set_index("currency")[["limit", "balance"]].plot(
    kind="bar",
    figsize=(8, 5),
    title="Total Limit and Balance by Currency"
)

ax.set_ylabel("Amount")
ax.set_xlabel("Currency")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()
