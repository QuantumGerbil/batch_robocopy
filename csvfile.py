# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 10:03:39 2024
"""
import pandas as pd
import os

class CSVFile:
    def __init__(self, path, name):
        self.full_path = os.path.join(path, name)
        
    def write_to_csv(self, classification, location, content, UUID, time):
        data = {
                    'Classification': classification,
                    'Physical Location': location,
                    'Content': content,
                    'UUID': UUID,
                    'Timestamp': time
                }
        try:
            df = pd.read_csv(self.full_path)
            sequence_id = df['SequenceID'].iloc[-1] + 1
        except FileNotFoundError:
            sequence_id = 1
        """
        Writes data to a CSV file.
        """
        if self.full_path is None or self.full_path == "":
            raise ValueError("Invalid filename.")
        df = pd.DataFrame(data, index=[sequence_id])
        df.index.name = 'SequenceID'
        try:
            if os.path.exists(self.full_path):
                df.to_csv(self.full_path, mode='a', header=False)
            else:
                df.to_csv(self.full_path, mode='w')
        except Exception as e:
            print(f"Error writing to file: {e}")
