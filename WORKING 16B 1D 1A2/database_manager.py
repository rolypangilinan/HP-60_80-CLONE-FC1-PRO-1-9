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
            temp_conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database_name}")
            temp_cursor.close()
            temp_conn.close()
            
            # Now connect WITH the database specified
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database_name
            )
            
            cursor = self.connection.cursor()
            
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
                standard_time DECIMAL(5,2) DEFAULT 1.50,
                title VARCHAR(255) DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_standard_times_table)
            
            # Alter column type if it was previously INT
            try:
                cursor.execute("ALTER TABLE standard_times MODIFY COLUMN standard_time DECIMAL(5,2) DEFAULT 1.50")
            except:
                pass
            
            # Add title column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE standard_times ADD COLUMN title VARCHAR(255) DEFAULT ''")
            except:
                pass
            
            # Default ST values per process (in minutes)
            default_st = {
                1: 1.56, 2: 1.73, 3: 1.53, 4: 1.49, 5: 1.46,
                6: 1.50, 7: 0.70, 8: 1.18, 9: 1.44
            }
            
            # Default titles per process
            default_titles = {
                1: 'EM Fastening', 2: 'DF & Rod Casing Fastening', 3: 'Partition Board',
                4: 'Lower Housing Prep', 5: 'Lower Housing Fastening',
                6: 'Combination Leadwire Arrange', 7: 'Soldering',
                8: 'Upper Housing', 9: 'Packing'
            }
            
            # Insert default standard times for processes 1-9 if they don't exist
            for i in range(1, 10):
                cursor.execute("INSERT IGNORE INTO standard_times (process_no, standard_time, title) VALUES (%s, %s, %s)", (i, default_st[i], default_titles[i]))
            
            # Update titles for existing rows that have empty titles
            for i in range(1, 10):
                cursor.execute("UPDATE standard_times SET title = %s WHERE process_no = %s AND (title IS NULL OR title = '')", (default_titles[i], i))
            
            # Create manpower table if it doesn't exist
            create_manpower_table = """
            CREATE TABLE IF NOT EXISTS manpower (
                process_no INT PRIMARY KEY,
                operator_manual VARCHAR(255) DEFAULT '',
                operator_scan VARCHAR(255) DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_manpower_table)
            
            # Insert default manpower rows for processes 1-9 if they don't exist
            for i in range(1, 10):
                cursor.execute("INSERT IGNORE INTO manpower (process_no) VALUES (%s)", (i,))
            
            self.connection.commit()
            print("Database and table initialized successfully")
            
        except Error as e:
            print(f"Error connecting to database: {e}")
            raise e
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def get_connection(self):
        """Create a fresh database connection for each operation"""
        return mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database_name
        )
    
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
            if connection:
                connection.close()
    
    def get_records_by_process(self, process_no, limit=100):
        """Get records for a specific process"""
        connection = None
        cursor = None
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_latest_record(self, process_no):
        """Get the latest record for a specific process"""
        connection = None
        cursor = None
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")
    
    def get_all_standard_times(self):
        """Get all standard times"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = "SELECT process_no, standard_time, title FROM standard_times ORDER BY process_no"
            cursor.execute(query)
            standard_times = cursor.fetchall()
            
            return standard_times
            
        except Error as e:
            print(f"Error fetching standard times: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def update_standard_time(self, process_no, standard_time, title=None):
        """Update standard time for a process"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if title is not None:
                query = "UPDATE standard_times SET standard_time = %s, title = %s WHERE process_no = %s"
                cursor.execute(query, (standard_time, title, process_no))
            else:
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def add_new_process(self, standard_time='50'):
        """Add a new process with standard time"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Get the next process number
            cursor.execute("SELECT MAX(process_no) FROM standard_times")
            result = cursor.fetchone()
            next_process_no = (result[0] or 0) + 1
            
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def delete_process(self, process_no):
        """Delete a process (only processes > 9)"""
        connection = None
        cursor = None
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_all_manpower(self):
        """Get all manpower records"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = "SELECT process_no, operator_manual, operator_scan FROM manpower ORDER BY process_no"
            cursor.execute(query)
            manpower = cursor.fetchall()
            
            return manpower
            
        except Error as e:
            print(f"Error fetching manpower: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def update_manpower(self, process_no, operator_manual=None, operator_scan=None):
        """Update manpower for a process"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            query = "UPDATE manpower SET operator_manual = %s, operator_scan = %s WHERE process_no = %s"
            cursor.execute(query, (operator_manual or '', operator_scan or '', process_no))
            connection.commit()
            
            return cursor.rowcount > 0
            
        except Error as e:
            print(f"Error updating manpower: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_cycle_graph_data(self):
        """Get average elapsed time per process for cycle graph monitoring"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Get average elapsed_time per process (only records with valid elapsed_time)
            query = """
            SELECT process_no, 
                   AVG(TIME_TO_SEC(elapsed_time)) as avg_seconds,
                   COUNT(*) as record_count
            FROM process_records 
            WHERE elapsed_time IS NOT NULL 
              AND elapsed_time != '00:00:00'
            GROUP BY process_no 
            ORDER BY process_no
            """
            cursor.execute(query)
            records = cursor.fetchall()
            
            # Convert avg_seconds to M.SS format
            result = []
            for row in records:
                avg_sec = float(row['avg_seconds']) if row['avg_seconds'] else 0
                minutes = int(avg_sec // 60)
                secs = int(avg_sec % 60)
                m_ss_value = minutes + (secs / 100.0)  # M.SS format
                result.append({
                    'process_no': row['process_no'],
                    'avg_seconds': avg_sec,
                    'avg_mss': round(m_ss_value, 2),
                    'record_count': row['record_count']
                })
            
            return result
            
        except Error as e:
            print(f"Error fetching cycle graph data: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_line_trend_data(self, process_no, limit=10):
        """Get individual elapsed time records for a process (for line trend graph)"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT id, elapsed_time, TIME_TO_SEC(elapsed_time) as elapsed_seconds, timestamp
            FROM process_records 
            WHERE process_no = %s 
              AND elapsed_time IS NOT NULL 
              AND elapsed_time != '00:00:00'
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            cursor.execute(query, (process_no, limit))
            records = cursor.fetchall()
            
            # Reverse so oldest is first (left-to-right on chart)
            records.reverse()
            
            # Convert to M.SS format
            result = []
            for row in records:
                elapsed_sec = float(row['elapsed_seconds']) if row['elapsed_seconds'] else 0
                minutes = int(elapsed_sec // 60)
                secs = int(elapsed_sec % 60)
                m_ss_value = minutes + (secs / 100.0)
                result.append({
                    'id': row['id'],
                    'elapsed_mss': round(m_ss_value, 2),
                    'elapsed_seconds': elapsed_sec,
                    'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if row['timestamp'] else ''
                })
            
            return result
            
        except Error as e:
            print(f"Error fetching line trend data: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_manpower_by_process(self, process_no):
        """Get manpower for a specific process"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = "SELECT process_no, operator_manual, operator_scan FROM manpower WHERE process_no = %s"
            cursor.execute(query, (process_no,))
            result = cursor.fetchone()
            
            return result
            
        except Error as e:
            print(f"Error fetching manpower: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
