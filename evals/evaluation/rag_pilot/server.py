# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import uvicorn
from api.v1.pilot import pilot_app
from api.v1.tuner import tuner_app
from components.adaptor.ecrag import ECRAGAdaptor
from components.pilot.pilot import pilot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


sub_apps = [pilot_app, tuner_app]
for sub_app in sub_apps:
    for route in sub_app.routes:
        app.router.routes.append(route)


@app.on_event("startup")
def startup():
    pilot.add_adaptor(ECRAGAdaptor())


if __name__ == "__main__":
    host = os.getenv("RAG_PILOT_SERVICE_HOST_IP", "0.0.0.0")
    port = int(os.getenv("RAG_PILOT_SERVICE_PORT", 16030))
    uvicorn.run(app, host=host, port=port)
