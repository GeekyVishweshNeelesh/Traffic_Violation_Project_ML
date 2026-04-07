"""
============================================================================
TRAFFIC VIOLATIONS INSIGHT SYSTEM
File 03 — MariaDB Database Setup (FINAL WORKING VERSION)
============================================================================
"""

import pymysql
import pandas as pd
import numpy as np
import time

print("="*80)
print("TRAFFIC VIOLATIONS - MARIADB DATABASE SETUP")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_HOST = 'localhost'
DB_USER = 'vishwesh'
DB_PASSWORD = 'Vish1408'  # ← CHANGE THIS!
DB_NAME = 'traffic_violations'
DB_PORT = 3306

CSV_FILE = '/home/vishwesh/Documents/GUVI_Course_Projects/Traffic_Violations_Project/traffic_violations_cleaned.csv'  # ← CHANGE THIS!

BATCH_SIZE = 1000
PROGRESS_INTERVAL = 50000

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================

print(f"\n{'='*80}")
print("STEP 1: LOADING DATA")
print(f"{'='*80}")

start_time = time.time()

try:
    print(f"📂 Loading: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE, low_memory=False)

    print(f"✅ Loaded successfully!")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)

print(f"\n📋 Original Columns:")
for i, col in enumerate(df.columns[:10], 1):
    print(f"   {i:2d}. {col}")
if len(df.columns) > 10:
    print(f"   ... and {len(df.columns) - 10} more")

# ============================================================================
# STEP 2: FIX DUPLICATES - COMPLETE REWRITE
# ============================================================================

print(f"\n{'='*80}")
print("STEP 2: CREATING UNIQUE PRIMARY KEY")
print(f"{'='*80}")

# Find original SeqID column
seq_col = None
for col in df.columns:
    if 'seq' in col.lower():
        seq_col = col
        break

if seq_col:
    print(f"📋 Found original ID column: {seq_col}")
    print(f"   Unique IDs: {df[seq_col].nunique():,} / {len(df):,}")

    # Check for duplicates
    duplicates = len(df) - df[seq_col].nunique()
    if duplicates > 0:
        print(f"   ⚠️  {duplicates:,} duplicate IDs detected")
else:
    print(f"⚠️  No SeqID column found")

# CRITICAL FIX: Drop the old SeqID column entirely, create fresh
print(f"\n🔨 Creating new primary key...")

# Reset index completely
df = df.reset_index(drop=True)

# Save original SeqID if exists
if seq_col:
    # Rename old SeqID to avoid conflicts
    df = df.rename(columns={seq_col: 'original_seq_id'})
    print(f"   ✅ Original IDs saved as: original_seq_id")

# Create brand new unique row_id column
df['row_id'] = range(len(df))

# Move row_id to first position
cols = ['row_id'] + [col for col in df.columns if col != 'row_id']
df = df[cols]

print(f"   ✅ Created row_id: 0 to {len(df)-1:,}")

# Verify uniqueness
if df['row_id'].nunique() == len(df):
    print(f"   ✅ All {len(df):,} row_ids are UNIQUE!")
else:
    print(f"   ❌ ERROR: row_id has duplicates!")
    exit(1)

# ============================================================================
# STEP 3: DATA PREPARATION
# ============================================================================

print(f"\n{'='*80}")
print("STEP 3: PREPARING DATA")
print(f"{'='*80}")

# Convert dates
date_count = 0
for col in df.columns:
    if 'date' in col.lower() and col != 'row_id':
        try:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            date_count += 1
        except:
            pass

print(f"📅 Converted {date_count} date columns")

# Handle NaN
print("🔄 Converting NaN to NULL...")
df = df.replace([np.nan, np.inf, -np.inf], None)
df = df.replace({pd.NaT: None})

for col in df.columns:
    if df[col].isna().any():
        df[col] = df[col].where(pd.notna(df[col]), None)

print("✅ Data ready!")
print(f"   Final columns: {len(df.columns)}")

# ============================================================================
# STEP 4: CREATE DATABASE
# ============================================================================

print(f"\n{'='*80}")
print("STEP 4: CREATING DATABASE")
print(f"{'='*80}")

try:
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    print(f"🗑️  Dropping old database...")
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")

    print(f"📦 Creating new database...")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE {DB_NAME}")

    print(f"✅ Database ready!")

except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)

# ============================================================================
# STEP 5: CREATE TABLE
# ============================================================================

print(f"\n{'='*80}")
print("STEP 5: CREATING TABLE")
print(f"{'='*80}")

def get_sql_type(dtype, col_name):
    """Convert pandas dtype to SQL type"""
    dtype_str = str(dtype)
    col_lower = col_name.lower()

    # Primary key - row_id
    if col_name == 'row_id':
        return 'BIGINT PRIMARY KEY'

    # Date/Time
    if 'datetime' in dtype_str:
        return 'DATETIME'
    elif 'date' in dtype_str:
        return 'DATE'
    elif 'time' in dtype_str and 'datetime' not in dtype_str:
        return 'TIME'

    # Numeric
    elif dtype_str in ['int64', 'int32']:
        return 'BIGINT'
    elif dtype_str in ['float64', 'float32']:
        return 'DECIMAL(15, 6)'
    elif dtype_str == 'bool':
        return 'TINYINT(1)'

    # Text
    else:
        text_keywords = ['description', 'location', 'geolocation', 'subagency']
        if any(kw in col_lower for kw in text_keywords):
            return 'TEXT'
        else:
            return 'VARCHAR(200)'

print(f"🔨 Building table schema for {len(df.columns)} columns...")

column_definitions = []
for col in df.columns:
    sql_type = get_sql_type(df[col].dtype, col)
    column_definitions.append(f"`{col}` {sql_type}")

create_table_sql = f"""
CREATE TABLE violations (
    {',\n    '.join(column_definitions)}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

try:
    cursor.execute(create_table_sql)
    print(f"✅ Table created!")

except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"\nFirst 5 column definitions:")
    for col_def in column_definitions[:5]:
        print(f"   {col_def}")
    cursor.close()
    conn.close()
    exit(1)

# ============================================================================
# STEP 6: CREATE INDEXES
# ============================================================================

print(f"\n{'='*80}")
print("STEP 6: CREATING INDEXES")
print(f"{'='*80}")

index_mappings = {
    'date': ['date_of_stop', 'dateofstop'],
    'agency': ['agency'],
    'category': ['violation_category', 'violationcategory'],
    'vehicle_type': ['vehicle_type', 'vehicletype'],
    'accident': ['accident'],
    'hour': ['hour'],
    'race': ['race'],
    'gender': ['gender'],
    'original_id': ['original_seq_id']
}

created_indexes = 0
for idx_name, possible_cols in index_mappings.items():
    for possible_col in possible_cols:
        matching_col = next((c for c in df.columns if c.lower() == possible_col.lower()), None)

        if matching_col:
            try:
                cursor.execute(f"CREATE INDEX idx_{idx_name} ON violations (`{matching_col}`)")
                print(f"   ✅ {matching_col}")
                created_indexes += 1
                break
            except:
                pass

print(f"✅ Created {created_indexes} indexes")

# ============================================================================
# STEP 7: INSERT DATA - WITH PROGRESS TRACKING
# ============================================================================

print(f"\n{'='*80}")
print("STEP 7: INSERTING DATA")
print(f"{'='*80}")

columns = df.columns.tolist()
placeholders = ', '.join(['%s'] * len(columns))
column_names = ', '.join([f"`{col}`" for col in columns])

insert_query = f"INSERT INTO violations ({column_names}) VALUES ({placeholders})"

print(f"📝 Insert Configuration:")
print(f"   Total Rows: {len(df):,}")
print(f"   Columns: {len(columns)}")
print(f"   Batch Size: {BATCH_SIZE:,}")
print(f"   Progress Updates: Every {PROGRESS_INTERVAL:,} rows")
print(f"\n⏳ Starting insertion... (estimated 20-30 minutes)\n")

start_insert = time.time()
inserted_count = 0
error_count = 0
last_progress_time = start_insert

try:
    for i in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[i:i+BATCH_SIZE]

        for index, row in batch.iterrows():
            try:
                values = []
                for val in row.values:
                    if pd.isna(val):
                        values.append(None)
                    elif isinstance(val, pd.Timestamp):
                        values.append(val.to_pydatetime())
                    elif isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                        values.append(None)
                    else:
                        values.append(val)

                cursor.execute(insert_query, tuple(values))
                inserted_count += 1

            except Exception as row_error:
                error_count += 1
                if error_count <= 5:
                    print(f"⚠️  Row {index} error: {row_error}")
                if error_count > 100:
                    raise Exception(f"Too many errors: {error_count}")

        conn.commit()

        # Progress updates
        if inserted_count % PROGRESS_INTERVAL == 0 or inserted_count == len(df):
            current_time = time.time()
            elapsed = current_time - start_insert
            speed = inserted_count / elapsed if elapsed > 0 else 0
            remaining_rows = len(df) - inserted_count
            eta = (remaining_rows / speed) if speed > 0 else 0
            percent = (inserted_count / len(df) * 100)

            print(f"   📊 Progress: {inserted_count:,} / {len(df):,} rows ({percent:.1f}%)")
            print(f"      Speed: {speed:.0f} rows/sec")
            print(f"      Elapsed: {elapsed/60:.1f} min")
            print(f"      ETA: {eta/60:.1f} min")
            print()

    conn.commit()

    insert_time = time.time() - start_insert

    print(f"{'='*80}")
    print(f"✅ INSERT COMPLETE!")
    print(f"{'='*80}")
    print(f"   ✅ Inserted: {inserted_count:,} rows")
    print(f"   ⚠️  Errors: {error_count} rows")
    print(f"   ✅ Success Rate: {(inserted_count/(inserted_count+error_count)*100):.2f}%")
    print(f"   ⏱️  Time: {insert_time/60:.1f} minutes")
    print(f"   ⚡ Average Speed: {inserted_count/insert_time:.0f} rows/sec")

except Exception as e:
    print(f"\n❌ INSERTION ERROR: {e}")
    print(f"   Rows inserted: {inserted_count:,}")
    print(f"   Errors: {error_count}")
    conn.rollback()
    cursor.close()
    conn.close()
    exit(1)

# ============================================================================
# STEP 8: VERIFY
# ============================================================================

print(f"\n{'='*80}")
print("STEP 8: VERIFICATION")
print(f"{'='*80}")

try:
    cursor.execute("SELECT COUNT(*) FROM violations")
    row_count = cursor.fetchone()[0]

    print(f"📊 Database row count: {row_count:,}")
    print(f"📊 Expected: {len(df):,}")

    if row_count >= len(df) * 0.99:
        print(f"✅ VERIFICATION PASSED!")
    else:
        print(f"⚠️  Row count mismatch")

    # Sample data
    cursor.execute("SELECT row_id, original_seq_id FROM violations LIMIT 5")
    samples = cursor.fetchall()

    print(f"\n📋 Sample rows:")
    for sample in samples:
        print(f"   row_id={sample[0]}, original_seq_id={sample[1]}")

    # Check indexes
    cursor.execute("SHOW INDEX FROM violations")
    indexes = cursor.fetchall()
    unique_indexes = len(set([idx[2] for idx in indexes]))

    print(f"\n📊 Indexes: {unique_indexes}")

except Exception as e:
    print(f"⚠️  Verification error: {e}")

# ============================================================================
# CLEANUP
# ============================================================================

cursor.close()
conn.close()

total_time = time.time() - start_time

print(f"\n{'='*80}")
print("✅ DATABASE SETUP COMPLETE!")
print(f"{'='*80}")
print(f"\n📊 Final Summary:")
print(f"   Database: {DB_NAME}")
print(f"   Table: violations")
print(f"   Rows: {inserted_count:,}")
print(f"   Columns: {len(columns)}")
print(f"   Indexes: {created_indexes}")
print(f"   Primary Key: row_id (sequential 0 to {len(df)-1:,})")
print(f"   Original IDs: original_seq_id column")
print(f"   Total Time: {total_time/60:.1f} minutes")
print(f"\n🎯 Next Step:")
print(f"   streamlit run 04_streamlit_dashboard.py")
print(f"\n{'='*80}")
