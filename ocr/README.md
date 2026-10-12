# Backend development

Start the backend from this directory with `uvicorn main:app --reload` or `python run_backend.py`. Keep the server bound to `127.0.0.1`.

The API requires `Authorization: Bearer <token>`. Requests run from the extension background script; arbitrary webpage origins are not granted CORS access.

Uploads are limited to 10 MiB including multipart overhead. Images are limited to 16 million pixels and 8192 pixels per dimension; textbox captures are limited to 1200 pixels per dimension. One inference runs at a time, and overlapping requests receive HTTP 429. The extension times out requests after 60 seconds. Canceling a request prevents results from appearing, but inference already executing on the server may finish before the server is available again.
