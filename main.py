from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import pandas as pd
import os
from typing import List
import hashlib

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSV file path
CSV_FILE = "/mlcv2/WorkingSpace/Personal/quannh/Project/Project/ohmni/RAG/data/user/ouput.csv"

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TopicCreate(BaseModel):
    email: EmailStr
    topic: str

class TopicDelete(BaseModel):
    email: EmailStr
    topic: str

# Helper functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_csv():
    """Initialize CSV file if it doesn't exist"""
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=['email', 'password', 'topic'])
        df.to_csv(CSV_FILE, index=False)

def read_csv() -> pd.DataFrame:
    """Read CSV file"""
    init_csv()
    return pd.read_csv(CSV_FILE)

def write_csv(df: pd.DataFrame):
    """Write DataFrame to CSV file"""
    df.to_csv(CSV_FILE, index=False)

def user_exists(email: str) -> bool:
    """Check if user exists in CSV"""
    df = read_csv()
    return email in df['email'].values

def verify_password(email: str, password: str) -> bool:
    """Verify user password"""
    df = read_csv()
    user_row = df[df['email'] == email]
    if user_row.empty:
        return False
    stored_password = user_row.iloc[0]['password']
    return stored_password == hash_password(password)

# API endpoints
@app.get("/")
async def root():
    return {"message": "Topic Manager API"}

@app.post("/register")
async def register(user: UserRegister):
    """Register a new user"""
    try:
        if user_exists(user.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        df = read_csv()
        hashed_password = hash_password(user.password)
        
        # Add new user row with empty topic initially
        new_row = pd.DataFrame({
            'email': [user.email],
            'password': [hashed_password],
            'topic': ['']  # Empty topic for initial registration
        })
        
        df = pd.concat([df, new_row], ignore_index=True)
        write_csv(df)
        
        return {"message": "User registered successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/login")
async def login(user: UserLogin):
    """Login user"""
    try:
        if not user_exists(user.email):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not verify_password(user.email, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return {"message": "Login successful", "email": user.email}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/topics/{email}")
async def get_topics(email: str) -> List[str]:
    """Get all topics for a user"""
    try:
        if not user_exists(email):
            raise HTTPException(status_code=404, detail="User not found")
        
        df = read_csv()
        user_topics = df[df['email'] == email]['topic'].tolist()
        
        # Filter out empty topics and None values
        topics = [topic for topic in user_topics if topic and str(topic).strip() and str(topic) != 'nan']
        
        return topics
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topics: {str(e)}")

@app.post("/topics")
async def add_topic(topic_data: TopicCreate):
    """Add a new topic for a user"""
    try:
        if not user_exists(topic_data.email):
            raise HTTPException(status_code=404, detail="User not found")
        
        if not topic_data.topic.strip():
            raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
        df = read_csv()
        
        # Add new row with the topic
        new_row = pd.DataFrame({
            'email': [topic_data.email],
            'password': [df[df['email'] == topic_data.email].iloc[0]['password']],  # Keep existing password
            'topic': [topic_data.topic.strip()]
        })
        
        df = pd.concat([df, new_row], ignore_index=True)
        write_csv(df)
        
        return {"message": "Topic added successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add topic: {str(e)}")

@app.delete("/topics")
async def delete_topic(topic_data: TopicDelete):
    """Delete a topic for a user"""
    try:
        if not user_exists(topic_data.email):
            raise HTTPException(status_code=404, detail="User not found")
        
        df = read_csv()
        
        # Find and remove the specific topic
        condition = (df['email'] == topic_data.email) & (df['topic'] == topic_data.topic)
        
        if not df[condition].empty:
            df = df[~condition]
            write_csv(df)
            return {"message": "Topic deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Topic not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete topic: {str(e)}")

# For development - endpoint to view all data
@app.get("/admin/data")
async def get_all_data():
    """Get all data from CSV (for debugging)"""
    try:
        df = read_csv()
        return df.to_dict('records')
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7705)