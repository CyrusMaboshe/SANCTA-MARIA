
import os
from dotenv import load_dotenv
import supabase

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = "https://frxvrxfyvubhgghnvocu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZyeHZyeGZ5dnViaGdnaG52b2N1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk2MjI4MzEsImV4cCI6MjA1NTE5ODgzMX0.nriTOgOwVNkT63-kpPBwwgZFNHZD-wAQjY8rT3PvXaY"

# Initialize Supabase client
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client():
    return supabase_client
