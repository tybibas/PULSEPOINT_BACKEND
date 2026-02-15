
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def apply_migration():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    sql_file = "pulsepoint_strategic/migrations/11_add_signal_intelligence.sql"
    
    with open(sql_file, 'r') as f:
        sql = f.read()

    # Split by semicolon? Or run as one block?
    # Supabase-py doesn't have direct SQL execution unless RPC is set up.
    # However, we can use the REST API via Requests or a specific tool?
    # Or use `postgres` library if installed.
    # It seems user environment has `psycopg2`? Or we rely on Tool `run_command`?
    # But `run_command` can't interact with remote DB unless `psql` is configured.
    
    # Check if `supabase-py` supports raw sql? No.
    # But we can define a function `exec_sql` in Supabase?
    # Or maybe we just print the SQL and ask user to run it?
    # User said: "Create migrations...".
    
    print(f"Applying migration: {sql_file}")
    
    # Since I cannot execute raw SQL via client without an RPC, 
    # I will assume I CANNOT run it automatically unless I have an `exec_sql` RPC.
    
    # But wait! I can check if `exec_sql` exists.
    try:
        supabase.rpc("exec_sql", {"sql": sql}).execute() # Hypothetical
        print("✅ Migration applied via RPC!")
    except Exception as e:
        print(f"⚠️ Could not apply via RPC: {e}")
        print("Please run the SQL manually in Supabase Dashboard.")

if __name__ == "__main__":
    apply_migration()
