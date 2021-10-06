import uvicorn
from fastapi import FastAPI, Request, Form
from starlette.responses import RedirectResponse


app = FastAPI(title="Labeling Task API",
              description="For helping AS department to labeling the data")


@app.get("/")
async def redirect():
    response = RedirectResponse(url='/create_task')
    return response


@app.post('/create_task/')







