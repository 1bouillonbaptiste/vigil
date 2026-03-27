# vigil

Video scene understanding and reporting.

### Prerequisites

Make sure you have a Python environment (>=3.13) set up. This project uses
Poetry for dependency management.

To set up the project, run:

```bash
make setup
```

### Running the Application

Once the environment is installed, you can run both the backend and frontend:

Backend (FastAPI):

```bash
poetry run uvicorn vigil.app.fastapi.main:app --reload --port 8000
```

Frontend (Streamlit):

```bash
poetry run streamlit run vigil/app/streamlit/main.py
```
