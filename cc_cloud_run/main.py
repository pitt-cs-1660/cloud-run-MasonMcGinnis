from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import firestore
from typing import Annotated
import datetime

app = FastAPI()

# mount static files
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
templates = Jinja2Templates(directory="/app/template")

# init firestore client
db = firestore.Client()
votes_collection = db.collection("votes")

@app.get("/")
async def read_root(request: Request):

    # Stream all votes
    votes = votes_collection.stream()
    votes_data = []
    for vote in votes:
        votes_data.append(vote.to_dict())
    
    # Variables to store and return the count of votes
    tabs_count = 0
    spaces_count = 0
    recent_votes = []

    # Count all votes and keep a list of recent votes
    for vote in votes_data:
        if vote["team"] == "TABS":
            tabs_count += 1
        else:
            spaces_count += 1
        recent_votes.append(vote)
    
    # Sort recent votes by created_at and get the last 5 votes
    recent_votes = sorted(recent_votes, key=lambda x: x["time_cast"], reverse=True)[:5]

    # Render the index.html template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tabs_count": tabs_count,
        "spaces_count": spaces_count,
        "recent_votes": recent_votes
    })


@app.post("/")
async def create_vote(team: Annotated[str, Form()]):
    if team not in ["TABS", "SPACES"]:
        raise HTTPException(status_code=400, detail="Invalid vote")
    
    # Create a new vote document for Firestore
    vote_data = {
        "team": team, # Tab or Space
        "time_cast": datetime.datetime.utcnow().isoformat() # Timestamp for recent votes sorting
    }

    # Add the vote to the Firestore collection
    votes_collection.add(vote_data)

    # Return a success message
    return {"detail": "Vote created successfully"}