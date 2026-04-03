import mysql.connector
from mysql.connector import Error
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.host = "localhost"
        self.port = 3306
        self.user = "root"
        self.password = ""  # Default XAMPP password is empty
        self.database_name = "cycle_time_monitoring"
        self.connection = None
        
    def connect(self):
        """Create database connection"""
        try:
            # First connect without specifying database to create it if needed
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            
            cursor = self.connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database_name}")
            cursor.execute(f"USE {self.database_name}")
            
            # Create table if it doesn't exist
            create_table_query = """
            CREATE TABLE IF NOT EXISTS process_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kitting_no VARCHAR(255),
                lineout_reason VARCHAR(255),
                elapsed_time TIME,
                pass_ng INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                process_no INTEGER,
                INDEX idx_process_no (process_no),
                INDEX idx_timestamp (timestamp)
            )
            """
            cursor.execute(create_table_query)
            
            # Create standard_times table if it doesn't exist
            create_standard_times_table = """
            CREATE TABLE IF NOT EXISTS standard_times (
                process_no INT PRIMARY KEY,
                standard_time INT DEFAULT 50,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_standard_times_table)
            
            # Insert default standard times for processes 1-9 if they don't exist
            for i in range(1, 10):
                cursor.execute("INSERT IGNORE INTO standard_times (process_no, standard_time) VALUES (%s, %s)", (i, 50))
            
            self.connection.commit()
            print("Database and table initialized successfully")
            
        except Error as e:
            print(f"Error connecting to database: {e}")
            raise e
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def get_connection(self):
        """Get database connection"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection
    
    def insert_record(self, kitting_no, lineout_reason, elapsed_time, pass_ng, process_no):
        """Insert a new record into process_records table"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Convert elapsed_time from MM:SS to TIME format
            if elapsed_time and ':' in elapsed_time:
                # If format is MM:SS, convert to HH:MM:SS
                parts = elapsed_time.split(':')
                if len(parts) == 2:
                    elapsed_time = f"00:{parts[0]}:{parts[1]}"
            
            # Set lineout_reason to '-' if it's None or empty
            if lineout_reason is None or lineout_reason == '':
                lineout_reason = '-'
            
            # kitting_no is now sent directly as the correct value from the frontend
            # No adjustment needed since counter increments on START
            
            insert_query = """
            INSERT INTO process_records 
            (kitting_no, lineout_reason, elapsed_time, pass_ng, process_no)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            record = (kitting_no, lineout_reason, elapsed_time, pass_ng, process_no)
            print(f"Inserting record: kitting_no={kitting_no}, lineout_reason={lineout_reason}, elapsed_time={elapsed_time}, pass_ng={pass_ng}, process_no={process_no}")
            cursor.execute(insert_query, record)
            connection.commit()
            
            record_id = cursor.lastrowid
            print(f"Record inserted successfully with ID: {record_id}")
            return record_id
            
        except Error as e:
            print(f"Error inserting record: {e}")
            if connection:
                connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            # Don't close connection here, let the connection pool handle it
    
    def get_records_by_process(self, process_no, limit=100):
        """Get records for a specific process"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT * FROM process_records 
            WHERE process_no = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            
            cursor.execute(query, (process_no, limit))
            records = cursor.fetchall()
            
            return records
            
        except Error as e:
            print(f"Error fetching records: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def get_latest_record(self, process_no):
        """Get the latest record for a specific process"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT * FROM process_records 
            WHERE process_no = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            
            cursor.execute(query, (process_no,))
            record = cursor.fetchone()
            
            return record
            
        except Error as e:
            print(f"Error fetching latest record: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")
    
    def get_all_standard_times(self):
        """Get all standard times"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = "SELECT process_no, standard_time FROM standard_times ORDER BY process_no"
            cursor.execute(query)
            standard_times = cursor.fetchall()
            
            return standard_times
            
        except Error as e:
            print(f"Error fetching standard times: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def update_standard_time(self, process_no, standard_time):
        """Update standard time for a process"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            query = "UPDATE standard_times SET standard_time = %s WHERE process_no = %s"
            cursor.execute(query, (standard_time, process_no))
            connection.commit()
            
            return cursor.rowcount > 0
            
        except Error as e:
            print(f"Error updating standard time: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def add_new_process(self, standard_time='50'):
        """Add a new process with standard time"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Get the next process number
            cursor.execute("SELECT MAX(process_no) as max_process FROM standard_times")
            result = cursor.fetchone()
            next_process_no = (result['max_process'] or 0) + 1
            
            # Insert new process
            query = "INSERT INTO standard_times (process_no, standard_time) VALUES (%s, %s)"
            cursor.execute(query, (next_process_no, standard_time))
            connection.commit()
            
            return next_process_no
            
        except Error as e:
            print(f"Error adding new process: {e}")
            if connection:
                connection.rollback()
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def delete_process(self, process_no):
        """Delete a process (only processes > 9)"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Delete from standard_times table
            query = "DELETE FROM standard_times WHERE process_no = %s"
            cursor.execute(query, (process_no,))
            
            # Also delete related records from process_records
            query_records = "DELETE FROM process_records WHERE process_no = %s"
            cursor.execute(query_records, (process_no,))
            
            connection.commit()
            
            return cursor.rowcount > 0
            
        except Error as e:
            print(f"Error deleting process: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
