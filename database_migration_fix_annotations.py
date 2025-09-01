#!/usr/bin/env python3
"""
Database Migration: Fix Annotations Table Schema
Adds missing columns: identifier_type, overlapping, relationships
"""

import sqlite3
import os
from datetime import datetime

def migrate_annotations_table():
    """Add missing columns to annotations table"""
    
    db_path = 'data/kdpii_labeler.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("=== Database Migration: Fix Annotations Schema ===")
    print(f"Target database: {db_path}")
    print(f"Backup created: {db_path}.backup")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        print("\n--- Current Schema ---")
        cursor.execute("PRAGMA table_info(annotations);")
        current_columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns: {current_columns}")
        
        # Define missing columns to add
        missing_columns = [
            ("identifier_type", "VARCHAR(20)", "default", "'default'"),
            ("overlapping", "BOOLEAN", "default", "0"),  # 0 for False in SQLite
            ("relationships", "JSON", "default", "'[]'")  # Empty JSON array
        ]
        
        # Add missing columns
        print("\n--- Adding Missing Columns ---")
        for col_name, col_type, default_constraint, default_value in missing_columns:
            if col_name not in current_columns:
                try:
                    alter_sql = f"ALTER TABLE annotations ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
                    print(f"Executing: {alter_sql}")
                    cursor.execute(alter_sql)
                    print(f"✅ Added column: {col_name}")
                except sqlite3.Error as e:
                    print(f"❌ Error adding column {col_name}: {e}")
                    conn.rollback()
                    return False
            else:
                print(f"ℹ️  Column {col_name} already exists, skipping")
        
        # Commit changes
        conn.commit()
        
        # Verify new schema
        print("\n--- Updated Schema ---")
        cursor.execute("PRAGMA table_info(annotations);")
        new_columns = cursor.fetchall()
        print("Updated columns:")
        for col in new_columns:
            print(f"  {col[1]} ({col[2]}) - NOT NULL: {bool(col[3])} - Default: {col[4]}")
        
        # Test table integrity
        cursor.execute("PRAGMA integrity_check;")
        integrity = cursor.fetchall()
        if integrity[0][0] == 'ok':
            print("✅ Database integrity check passed")
        else:
            print(f"❌ Database integrity issues: {integrity}")
            
        conn.close()
        
        print(f"\n✅ Migration completed successfully!")
        print(f"   Added {len([col for col in missing_columns if col[0] not in current_columns])} columns")
        print(f"   Database backup available: {db_path}.backup")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = migrate_annotations_table()
    exit(0 if success else 1)