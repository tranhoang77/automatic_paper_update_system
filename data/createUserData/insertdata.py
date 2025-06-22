import csv

data = [
    {"Name": "Tran Hoang", "Mail": "tranvanhoangdpe@gmail.com", "Topic": "Computer Vision"},
    {"Name": "Tran Van Hoang", "Mail": "23520542@gm.uit.edu.vn", "Topic": "Object Detection"},
]

with open("../data/user/ouput.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["Name", "Mail", "Topic"])
    writer.writeheader()
    writer.writerows(data)

print("File 'output.csv' đã được tạo.")
