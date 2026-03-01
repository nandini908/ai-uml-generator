from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
import asyncio

# Import the parser function
from parser import extract_components

# --- Pydantic Models ---
class SrsText(BaseModel):
    text: str

class UmlComponent(BaseModel):
    name: str
    type: str # e.g., "Class", "Attribute", "Method"
    confidence: float

class UmlRelationship(BaseModel):
    source: str
    target: str
    type: str # e.g., "Association", "Inheritance"
    confidence: float

class GenerationResponse(BaseModel):
    components: list[UmlComponent]
    relationships: list[UmlRelationship]

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI UML Diagram Generator",
    description="Analyzes SRS text to generate UML components.",
    version="0.1.0",
)

# --- CORS Middleware ---
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NLP Model Loading ---
nlp = None

@app.on_event("startup")
async def load_nlp_model():
    """Load the spaCy model on application startup."""
    global nlp
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Downloading spaCy model 'en_core_web_sm'...")
        from spacy.cli import download
        # Using asyncio.to_thread to run the blocking download function in a separate thread
        await asyncio.to_thread(download, "en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    print("spaCy model loaded successfully.")


# --- API Endpoints ---
@app.get("/")
def read_root():
    """A simple endpoint to confirm the server is running."""
    return {"message": "Welcome to the AI UML Generator API"}

@app.post("/generate", response_model=GenerationResponse)
async def generate_uml(srs: SrsText):
    """
    Analyzes the SRS text and returns extracted UML components.
    """
    if not nlp:
        # This case should be rare due to the startup event
        return {"components": [], "relationships": []}

    # Use the actual parser function
    components_data, relationships_data = extract_components(srs.text, nlp)
    
    # Convert dicts to Pydantic models
    components = [UmlComponent(**comp) for comp in components_data]
    relationships = [UmlRelationship(**rel) for rel in relationships_data]

    return {"components": components, "relationships": relationships}
