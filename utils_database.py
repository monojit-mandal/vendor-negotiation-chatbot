import duckdb
import datetime as dt
from dataclasses import dataclass

DUCKDB_DB_NAME = 'chatbot.duckdb'

# Connect to DuckDB and create tables if they don’t exist
db_connection = duckdb.connect(DUCKDB_DB_NAME)  # This will create a local database file named "chatbot.db"

# Create sequences for auto-incrementing IDs
db_connection.execute("CREATE SEQUENCE IF NOT EXISTS user_id_seq START 1;")
db_connection.execute("CREATE SEQUENCE IF NOT EXISTS session_id_seq START 1;")
db_connection.execute("CREATE SEQUENCE IF NOT EXISTS message_id_seq START 1;")
db_connection.execute("CREATE SEQUENCE IF NOT EXISTS contract_id_seq START 1;")

# Define and create tables
db_connection.execute("""
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER DEFAULT nextval('user_id_seq') PRIMARY KEY,
    username VARCHAR,
    role VARCHAR DEFAULT 'supplier',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

db_connection.execute("""
CREATE TABLE IF NOT EXISTS Materials (
    material_id INTEGER PRIMARY KEY,
    description VARCHAR,
    quantity INTEGER,
    price_per_unit FLOAT,
    min_quantity INTEGER,
    max_quantity INTEGER,
    min_price_per_unit FLOAT,
    max_price_per_unit FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

db_connection.execute("""
CREATE TABLE IF NOT EXISTS Contracts (
    contract_id INTEGER DEFAULT nextval('contract_id_seq') PRIMARY KEY,
    user_id INTEGER,
    material_id INTEGER,
    contract_details VARCHAR,
    price_per_unit FLOAT,
    quantity FLOAT,
    bundling_unit FLOAT,
    bundling_amount FLOAT,
    bundling_discount FLOAT,
    payment_term VARCHAR CHECK (
        payment_term IN (
            'NET10','NET20','NET30','NET40',
            'NET50','NET60','NET70','NET80','NET90'
        )
    ),
    delivery_timeline FLOAT,
    contract_period FLOAT,
    contract_inflation FLOAT,
    rebates_threshold_unit FLOAT,
    rebates_discount FLOAT,
    warranty FLOAT,
    incoterms VARCHAR CHECK (
        incoterms IN (
            'EXW','FCA','FAS','FOB','CFR',
            'CIF','CPT','CIP','DAP','DPU','DDP'
        )
    ),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_tmstp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (material_id) REFERENCES Materials(material_id), 
);
""")


db_connection.execute("""
CREATE TABLE IF NOT EXISTS Sessions (
    session_id INTEGER DEFAULT nextval('session_id_seq') PRIMARY KEY,
    user_id INTEGER,
    material_id INTEGER,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (material_id) REFERENCES Materials(material_id)
);
""")

db_connection.execute("""
CREATE TABLE IF NOT EXISTS Messages (
    message_id INTEGER DEFAULT nextval('message_id_seq') PRIMARY KEY,
    session_id INTEGER,
    sender VARCHAR CHECK (sender IN ('user', 'bot')),
    content TEXT NOT NULL,
    step INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES Sessions(session_id)
);
""")

db_connection.close()

@dataclass
class Material():
    material_id:int = None
    description:str = None
    quantity:int = None
    price_per_unit:float = None
    min_quantity:int = None
    max_quantity:int = None
    min_price_per_unit:float = None
    max_price_per_unit:float = None
    
    def load_from_data(self,data):
        self.material_id = data['material_id']
        self.description = data['description']
        self.quantity = data['quantity']
        self.price_per_unit = data['price_per_unit']
        self.min_quantity = data['min_quantity']
        self.max_quantity = data['max_quantity']
        self.min_price_per_unit = data['min_price_per_unit']
        self.max_price_per_unit = data['max_price_per_unit']
        return self


@dataclass
class Contract():
    contract_id:int = None
    user_id:int = None
    material_id:int = None
    contract_details:str = None
    price_per_unit:float = None
    quantity:float = None
    bundling_unit:float = None
    bundling_amount:float = None
    bundling_discount:float = None
    payment_term:str = None
    delivery_timeline:float = None
    contract_period:float = None
    contract_inflation:float = None
    rebates_threshold_unit:float = None
    rebates_discount:float = None
    warranty:float = None
    incoterms:str = None

    def load_from_data(self,data):
        self.user_id = data['user_id']
        self.material_id = data['material_id']
        self.contract_details = data['contract_details']
        self.price_per_unit = data['price_per_unit']
        self.quantity = data['quantity']
        self.bundling_unit = data['bundling_unit']
        self.bundling_amount = data['bundling_amount']
        self.bundling_discount = data['bundling_discount']
        self.payment_term = data['payment_term']
        self.delivery_timeline = data['delivery_timeline']
        self.contract_period = data['contract_period']
        self.contract_inflation = data['contract_inflation']
        self.rebates_threshold_unit = data['rebates_threshold_unit']
        self.rebates_discount = data['rebates_discount']
        self.warranty = data['warranty']
        self.incoterms = data['incoterms']
        return self

@dataclass
class Session():
    session_id:int = None
    user_id: int = None
    material_id:int = None
    start_time:dt.datetime = None
    end_time:dt.datetime = None

    def load_from_data(self,data):
        self.user_id = data['user_id']
        self.material_id = data['material_id']
        self.start_time = data['start_time']
        self.end_time = data['end_time']
        return self



# Function to add a new user
def add_user(username,role):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    db_connection.execute("INSERT INTO Users (username,role) VALUES (?,?)", (username,role))
    user_id = db_connection.execute("SELECT user_id FROM Users WHERE username = ?", (username,)).fetchone()[0]
    db_connection.close()
    return user_id

def add_material(material:Material):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    db_connection.execute(
        """
        INSERT INTO Materials 
        (material_id,description,quantity,price_per_unit,
        min_quantity,max_quantity,min_price_per_unit,max_price_per_unit)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            material.material_id,material.description,material.quantity,
            material.price_per_unit,material.min_quantity,material.max_quantity,
            material.min_price_per_unit,material.max_price_per_unit
        )
    )
    db_connection.close()
    return True

def add_contract(contract:Contract):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    db_connection.execute(
        """
        INSERT INTO Contracts 
        (
        user_id,material_id,contract_details,price_per_unit,
        quantity,bundling_unit,bundling_amount,bundling_discount,payment_term,
        delivery_timeline,contract_period,contract_inflation,
        rebates_threshold_unit,rebates_discount,warranty,incoterms
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            contract.user_id,contract.material_id,
            contract.contract_details,contract.price_per_unit,contract.quantity,
            contract.bundling_unit,contract.bundling_amount,contract.bundling_discount,
            contract.payment_term,contract.delivery_timeline,contract.contract_period,
            contract.contract_inflation,contract.rebates_threshold_unit,
            contract.rebates_discount,contract.warranty,contract.incoterms
        )
    )
    db_connection.close()
    return True

def add_session(session:Session):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    db_connection.execute(
        """
        INSERT INTO Sessions 
        (user_id,material_id,start_time,end_time)
        VALUES(?,?,?,?)
        """,
        (
            session.user_id,session.material_id,
            session.start_time,session.end_time
        )
    )
    db_connection.close()
    return True

def get_material_info(material_id):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    df = db_connection.execute(
        """
        select * from Materials 
        where material_id = ?""",
        (material_id,)
    ).pl()
    db_connection.close()
    return df.rows(named = True)[0]

def get_last_contract(user_id,material_id):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    df = db_connection.execute(
        """
        select * from Contracts 
        where user_id = ? and material_id = ? 
        order by created_at desc
        """,
        (user_id,material_id)
    ).pl()
    if df.shape[0] == 0:
        df = db_connection.execute(
            """
            select * from Contracts 
            where material_id = ? 
            order by created_at desc
            """,
            (material_id,)
        ).pl()
    db_connection.close()
    return df.rows(named = True)[0]

# Function to start a new session for a user
def start_session(
    user_id:int,
    material_id:int
) -> int:
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    db_connection.execute(
        "INSERT INTO Sessions (user_id,material_id) VALUES (?,?)", 
        (user_id,material_id)
    )
    session_id = db_connection.execute(
        """SELECT session_id FROM Sessions 
        WHERE user_id = ? 
        ORDER BY start_time DESC LIMIT 1""", 
        (user_id,)
    ).fetchone()[0]
    print(session_id)
    db_connection.close()
    return session_id

def get_user_id(username):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    user_id = db_connection.execute(
        """SELECT user_id FROM Users WHERE username = ?""", 
        (username,)
    ).fetchone()
    db_connection.close()
    return user_id

# Function to add a message to a session
def add_message(session_id, sender, content,step):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    db_connection.execute(
        """
        INSERT INTO Messages (session_id, sender, content, step) 
        VALUES (?, ?, ?, ?)
        """, 
        (session_id, sender, content, step)
    )
    db_connection.close()
    return True

# Function to end a session
def end_session(session_id):
    end_time = dt.datetime.now()
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    db_connection.execute("UPDATE Sessions SET end_time = ? WHERE session_id = ?", (end_time, session_id))
    db_connection.close()
    return True

# Function to list user's previous sessions
def list_sessions(user_id):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    sessions = db_connection.execute(
        """
        SELECT session_id, start_time, end_time 
        FROM Sessions WHERE user_id = ?
        order by start_time desc
        """, 
        (user_id,)
    ).fetchall()
    db_connection.close()
    return sessions

def pull_all_sessions():
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    df = db_connection.execute(
        """
        SELECT ss.session_id, u.username,m.description, ss.start_time, ss.end_time 
        FROM Sessions ss
        LEFT JOIN Users u on ss.user_id = u.user_id
        LEFT JOIN Materials m on ss.material_id = m.material_id
        order by start_time desc
        """
    ).pl()
    db_connection.close()
    return df

def pull_sessions_by_user(username:str):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    df = db_connection.execute(
        """
        SELECT ss.session_id, u.username,m.description, ss.start_time, ss.end_time 
        FROM Sessions ss
        LEFT JOIN Users u on ss.user_id = u.user_id
        LEFT JOIN Materials m on ss.material_id = m.material_id
        WHERE u.username = ?
        order by start_time desc
        """, 
        (username,)
    ).pl()
    db_connection.close()
    return df

def list_materials(user_id:int):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    materials = db_connection.execute(
        """
        SELECT distinct material_id 
        FROM Contracts WHERE user_id = ?
        """, 
        (user_id,)
    ).fetchall()
    if len(materials) == 0:
        materials = db_connection.execute(
            """
            SELECT distinct material_id 
            FROM Contracts
            """
        ).fetchall()
    db_connection.close()
    return [mat[0] for mat in materials]

# Function to display messages in an existing session
def pull_message_history(session_id):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    
    df = db_connection.execute(
        """
        SELECT distinct sender, content, step
        FROM Messages WHERE session_id = ? 
        ORDER BY timestamp
        """, 
        (session_id,)
    ).pl()
    db_connection.close()
    return df.rows(named = True)

def pull_all_materials():
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    df = db_connection.execute(
        """SELECT * FROM Materials"""
    ).pl()
    db_connection.close()
    return df

def pull_material_by_id(material_id):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    df = db_connection.execute(
        """SELECT * FROM Materials where material_id = ?""",(material_id,)
    ).pl()
    db_connection.close()
    return df

def pull_all_suplliers():
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    df = db_connection.execute(
        """SELECT * FROM Users where role = 'supplier'"""
    ).pl()
    db_connection.close()
    return df

def pull_all_contracts():
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    df = db_connection.execute(
        """SELECT * FROM Contracts"""
    ).pl()
    db_connection.close()
    return df

def get_session_by_id(session_id:int):
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    df = db_connection.execute(
        """SELECT * FROM Sessions where session_id = ?""",
        (session_id,)
    ).pl()
    db_connection.close()
    return df

# def pull_latest_contract(user_id,material_id):
#     db_connection = duckdb.connect(DUCKDB_DB_NAME)
#     df = db_connection.execute(
#         """select * from Contracts where user_id = ? and material_id = ?"""
#         ,(user_id,material_id)
#     ).pl()
#     if df.shape[0] == 0:
#         df = db_connection.execute(
#             """select * from Contracts where material_id = ?"""
#             ,(material_id,)
#         ).pl()
#     return df.rows(named = True)

def clear_messages():
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    db_connection.execute(
        """
        DELETE FROM Messages
        """,
    )
    return True

def clear_sessions():
    db_connection = duckdb.connect(DUCKDB_DB_NAME)
    db_connection.execute(
        """
        DELETE FROM Sessions
        """,
    )
    return True

def clear_database(db_connection):
    return None

# clear_sessions()
