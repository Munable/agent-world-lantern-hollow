"""The optional observer probe must not leak SQLite handles."""
from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from tools.measure_observers import database

class ObserverMeasurementTests(unittest.TestCase):
    def test_sampling_closes_its_read_only_connection(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/'sample.sqlite3'
            with closing(sqlite3.connect(path)) as db:
                db.execute('CREATE TABLE sample(id INTEGER)');db.commit()
            original=sqlite3.connect;opened=[]
            def connect(*args,**kwargs):
                connection=original(*args,**kwargs);opened.append(connection)
                self.assertIn('mode=ro',args[0])
                return connection
            with patch('tools.measure_observers.sqlite3.connect',side_effect=connect):
                self.assertEqual(database(path)['rows'],{'sample':0})
            self.assertEqual(len(opened),1)
            with self.assertRaises(sqlite3.ProgrammingError):opened[0].execute('SELECT 1')
