import requests

BASE_URL = 'https://firestore.googleapis.com/v1'
PAGE_SIZE = 300


def list_documents(project_id, space_id, table, token, get=requests.get):
    """Every document in spaces/{space_id}/{table}, following nextPageToken until exhausted."""
    url = (f"{BASE_URL}/projects/{project_id}/databases/(default)"
           f"/documents/spaces/{space_id}/{table}")
    headers = {'Authorization': f"Bearer {token}"}
    documents = []
    page_token = None

    while True:
        params = {'pageSize': PAGE_SIZE}
        if page_token:
            params['pageToken'] = page_token
        response = get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        body = response.json()
        documents.extend(body.get('documents', []))
        page_token = body.get('nextPageToken')
        if not page_token:
            return documents
