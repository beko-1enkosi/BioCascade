import os
import requests

def download_nhanes_data():
    raw_data_path = "data/raw"
    os.makedirs(raw_data_path, exist_ok=True)

    files_to_download = {
        "P_DEMO.XPT": "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/P_DEMO.XPT",
        "P_BIOPRO.XPT": "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/P_BIOPRO.XPT",
        "P_BPX.XPT": "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/P_BPX.XPT"
    }

    for filename, url in files_to_download.items():
        destination = os.path.join(raw_data_path, filename)

        if not os.path.exists(destination):
            print(f"📥 Downloading {filename}...")
            response = requests.get(url)

            with open(destination, 'wb') as f:
                f.write(response.content)
            print(f"✅ Saved to {destination}")

        else:
            print(f"✔️ {filename} already exists. Skipping.")

if __name__ == "__main__":
    download_nhanes_data()