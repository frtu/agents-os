import requests

def main():
    try:
        response=requests.post(
            "http://localhost:8002/ingest_text",
            params={"name":"project_faq", "content":"PS:Payment system"},
            json={}
        )
        # response.raise_for_status()  # Raise an exception for HTTP errors

        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers['Content-Type']}")

        data = response.json()
        print(f"Data: {data}")

    except requests.exceptions.RequestException as e:
        print(f"Status Code: {response.status_code}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
