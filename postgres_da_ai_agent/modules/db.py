import psycopg2
from psycopg2.sql import SQL, Identifier

class PostgresManager:
    def __init__(self):
        self.connection = None
        self.cur = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cur:
            self.cur.close()
        if self.connection:
            self.connection.close()

    def connect_with_url(self, url):
        
        self.connection = psycopg2.connect(url)
        try:
         self.cur = self.connection.cursor()
        except Exception as e:
         print(f"Error creating cursor: {e}")


    def upsert(self, table_name, _dict):
        with self.connection.cursor() as cursor:
            insert_sql = f"INSERT INTO {table_name} ({', '.join(_dict.keys())}) " \
                         "VALUES ({', '.join(['%s' for _ in _dict.values()])} " \
                         "ON CONFLICT (id) DO UPDATE SET " + \
                         ', '.join([f"{key} = excluded.{key}" for key in _dict.keys()])
            cursor.execute(insert_sql, list(_dict.values()))
            self.connection.commit()

    def delete(self, table_name, _id):
        with self.connection.cursor() as cursor:
            delete_sql = f"DELETE FROM {table_name} WHERE id = %s"
            cursor.execute(delete_sql, (_id,))
            self.connection.commit()

    def get(self, table_name, _id):
        with self.connection.cursor() as cursor:
            select_sql = f"SELECT * FROM {table_name} WHERE id = %s"
            cursor.execute(select_sql, (_id,))
            return cursor.fetchone()

    def get_all(self, table_name):
        with self.connection.cursor() as cursor:
            select_sql = f"SELECT * FROM {table_name}"
            cursor.execute(select_sql)
            return cursor.fetchall()

    # def run_sql(self, sql):
    #     with self.connection.cursor() as cursor:
    #         cursor.execute(sql)
    #         return cursor.fetchall()

    def run_sql(self, sql) ->str:
        self.cur.execute(sql)
        columns =[desc[0] for desc in self.cur.description]
        res = self.cur.fetchall()

        list_of_dicts = [dict(zip(columns, row)) for row in res]
        
        json_result = json.dumps(list_of_dicts, indent=4, default=self.datetime_handler)

        #dump these results to a file
        with open("results.json", "w") as f:
            f.write(json_result)

        return "Successfully deliveres results to json file"
    
    def datetime_handler(self, obj):
        """
        Handle datetime objects when serializing to JSON.
        """

        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)  
    # or just return the object unchanged, or another default value
        

    def get_table_definition(self, table_name):
        with self.connection.cursor() as cursor:
            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s",
                           (table_name,))
            columns = cursor.fetchall()
            definition = f"CREATE TABLE {table_name} (\n"
            for column in columns:
                definition += f"  {column[0]} {column[1]},\n"
            definition = definition[:-2] + "\n);"
            return definition

    def get_all_table_names(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            return [table[0] for table in cursor.fetchall()]

    def get_table_definitions_for_prompt(self):
        table_names = self.get_all_table_names()
        print("table names", table_names)
        definitions = []
        for table_name in table_names:
            table_definition = self.get_table_definition(table_name)
            print("table definition", table_definition)
            definitions.append(table_definition)
        return '\n'.join(definitions)
    
def get_table_definitions_for_prompt_MOCK(self):
        return  """CREATE TABLE users (
  id integer,
  created timestamp without time zone,
  updated timestamp without time zone,
  authed boolean,
  plan text,
  name text,
  email text
);


CREATE TABLE jobs (
  id integer,
  created timestamp without time zone,
  updated timestamp without time zone,
  parentuserid integer,
  totaldurationms integer,
  status text
);
"""

def get_table_definition_map_for_embeddings(self):
    table_names = self.get_all_table_names()
    definitions = {}
    for table_name in table_names:
        definitions[table_name] = self.get_table_definition(table_name)
    return definitions
