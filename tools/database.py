import polars as pl
import re
from fnmatch import fnmatch
import csv
import os
import psycopg
from pathlib import Path
from argparse import ArgumentParser
from typing import Mapping
import logging

logger = logging.getLogger(__name__)

class PostgreSQLDB:
    """
    Basic script to handle basic use of postgresql db
    """
    @classmethod
    def create_table(cls, table_name: str, varlist: list[list[str]]):
        fields = ',\n'.join([' '.join(x) for x in varlist])
        cmd = f"CREATE TABLE IF NOT EXISTS {table_name} ({fields});"
        # print(cmd)
        return cls.conn.execute(cmd)

    @classmethod
    def create_table_from_df(cls, table_name: str, df: pl.DataFrame):
        print(table_name)
        print(df)
    
    @classmethod
    def _insert_cmd(cls, table_name: str, datamap: Mapping[str, any], conflict_keys: list[str]):
        data = list(datamap.items())
        keys = [x[0] for x in data]
        placeholders =', '.join(["%s"] * len(keys))
        keystr = ', '.join(keys)
        cmd = f"""INSERT INTO {table_name} ({keystr}) 
                VALUES ({placeholders})
                ON CONFLICT ({', '.join(conflict_keys)}) DO NOTHING
                RETURNING {keystr};"""
        return cmd

    @classmethod
    def insert_many(cls, table_name: str, datamaplist: list[Mapping[str, any]], conflict_keys: list[str]):
        if not datamaplist:
            return None
        cmd = cls._insert_cmd(table_name, datamaplist[0], conflict_keys)
        values = list(tuple(datamap.values()) for datamap in datamaplist)
        # print(cmd)
        # print(values[0])
        # print(values)
        with cls.conn.cursor() as cur:
            cur.executemany(cmd, values)

    @classmethod
    def insert(cls, table_name: str, datamap: Mapping[str, any], conflict_keys: list[str]):
        cmd = cls._insert_cmd(cls, table_name, datamap, conflict_keys)
        values = tuple(datamap.values())
        return cls.conn.execute(cmd, values)

    @classmethod
    def select(cls, table_name: str, keylist: list[str], additional: str):
        cmd = f"SELECT {', '.join(keylist)} FROM {table_name} {additional};"
        return cls.conn.execute(cmd)

    @classmethod
    def create_enum(cls, typename, enum_values):
        enum_str = "\', \'".join(enum_values)
        cmd = f"""
DO $$ BEGIN
    CREATE TYPE {typename} AS ('{enum_str}');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
        """
        return cls.conn.execute(cmd)
    
    @classmethod
    def execute(cls, cmd):
        return cls.conn.execute(cmd)
    
    @classmethod
    def commit(cls):
        cls.conn.commit()

    @classmethod
    def start(cls, host, port, dbname, user=None, password=None):
        # Service name is required for most backends
        cls.conn = psycopg.connect( 
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=dbname
        )
        cursor = cls.conn.cursor()
        logger.info("Connection successful.")

        # Example query
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        logger.info("Current Time:", result)

        
    @classmethod
    def end(cls):
        if cls.conn:
            cls.conn.close()
            logger.info('Connection closed.')

class LoadFromLocal:
    @classmethod
    def grab_all_files(cls, indir: str, pattern: str):
        filepaths = []
        for path, _, files in os.walk(indir):
            for name in files:
                if fnmatch(name, pattern):
                    filepaths.append(Path(path, name))
        return filepaths

    @classmethod
    def validate_headers(cls, files: list[str]):
        keys = set()
        for fp in files:
            with open(fp, 'r') as file:
                reader = csv.reader(file)
                for headers in reader:
                    if not keys:
                        keys = set(headers)
                    elif keys.difference(headers):
                        raise Exception(f"difference between headers found: {files[0]}, {fp}")
                    break
        return keys

    @classmethod
    def process_time_fields(cls, df: pl.DataFrame, regex: str = r".*[tT]ime"):
        df = df.lazy()
        fields = [f for f in df.collect_schema().names() if re.match(regex, f)]
        for field in fields:
            column = df.select([field]).with_columns(
                minute=pl.col(field).str.split(':').first().str.to_integer(),
                second=pl.col(field).str.split(':').last().str.to_integer()
            ).select(
                field=pl.time(hour=pl.lit(0), minute=pl.col('minute'), second=pl.col('second'))
            )
            df = df.with_columns(**{field: column})
        return df
            

def main():
    parser = ArgumentParser("upload csv")
    parser.add_argument('-t', '--time_fields', help="time fields (comma separated)")
    parser.add_argument('-p', '--pattern', help="filepattern")
    parser.add_argument('-d', '--dir', help="input directory")
    parser.add_argument('-H', '--host', help="postgres host", default='127.0.0.1')
    parser.add_argument('-P', '--port',  help="postgres port", default=5432)
    parser.add_argument('-D', '--db', help="database name", default="nhlxg")
    parser.add_argument('-U', '--user', help="login user", default='trxe')
    parser.add_argument('-L', '--login', help="login password")
    args = parser.parse_args()
    
    # files = grab_all_files(args.dir, args.pattern)
    # headers = validate_headers(files)
    # df_gen = pl.scan_csv(args.dir, args.pattern, infer_schema_length=None, try_parse_dates=True).lazy()
    
    # df_gen = pl.read_csv(files[0], infer_schema_length=None, try_parse_dates=True).lazy()
    # PostgreSQLDB.start(args.host, args.port, args.db, args.user, args.login)

if __name__ == "__main__":
    main()