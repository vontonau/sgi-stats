"""An example using ASGI server."""

from fastapi import FastAPI
from uvicorn import run
from sgistats.destinations import ConsoleMetricsDestination
from sgistats import ASGIMetricsMiddleware, MetricsCollector

# Create a FastAPI app
app = FastAPI()

# Define a simple route
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# Create a console metrics destination
console_destination = ConsoleMetricsDestination()

# Create a metrics collector with the console destination
metrics_collector = MetricsCollector([console_destination])

# Wrap the app with the ASGIMetricsMiddleware
app = ASGIMetricsMiddleware(app, metrics_collector)

if __name__ == "__main__":
    # Run the app with Uvicorn
    run(app, host="0.0.0.0", port=8000)