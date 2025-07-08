"""Netlify Function wrapper for the FastAPI application.

This module is discovered automatically by Netlify when placed in the
`netlify/functions` directory. It exposes a `handler` variable that Netlify
uses as the AWS Lambda entrypoint.

It wraps the existing FastAPI app (defined in app.main) with Mangum so the ASGI
application can run in the Lambda environment.
"""
from mangum import Mangum

# Import FastAPI app
from app.main import app as fastapi_app

# Handler for Netlify/AWS Lambda
handler = Mangum(fastapi_app)
