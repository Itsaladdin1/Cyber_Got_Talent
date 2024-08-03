import webbrowser
import subprocess

def open_url(url):
    if url == "www.cybergottalent.se":
        # Run vote.py
        subprocess.run(["python", "open.py"])
    elif url == "www.cybersalongen.se":
        # Run app.py
        subprocess.run(["python", "app.py"])
    else:
        print("URL not recognized")

if __name__ == "__main__":
    # Example URLs for testing
    test_urls = ["www.cybergottalent.se", "www.cybersalongen.se", "www.unknownsite.com"]

    for url in test_urls:
        print(f"Opening URL: {url}")
        open_url(url)
